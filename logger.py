#!/usr/bin/env python3

import can, json, os, csv, time, math, logging, sys
from datetime import datetime
from pathlib import Path

# Try GPIO, fall back to keyboard
try:
    import RPi.GPIO as GPIO
    HAS_GPIO = True
except Exception:
    HAS_GPIO = False


HERE = Path(__file__).resolve().parent
CONFIG_PATH = HERE / "config.json"
LOG_DIR = HERE / "logs"
LOG_DIR.mkdir(exist_ok=True)
timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

# Logging and CAN setup
logging.basicConfig(
    filename=str(LOG_DIR / f"pedal_monitor_{timestamp}.log"),
    level=logging.INFO,
    format="%(asctime)s %(levelname)s: %(message)s"
)
console = logging.StreamHandler()
console.setLevel(logging.INFO)
logging.getLogger("").addHandler(console)

CAN_CHANNEL = "can0"
INTERFACE = "socketcan"
CONFIRM_PIN = 17
DEBOUNCE_MS = 200


def parse_bytes_little_endian(data: bytes, offset: int, length: int) -> int:
    # Grab a few bytes and turn them into an integer (little-endian order)
    if offset + length > len(data):
        return 0
    return int.from_bytes(data[offset:offset + length], "little", signed=False)


def extract_bits_little_endian(data: bytes, start_bit: int, bit_length: int) -> int:
    # Pull out a specific group of bits from a byte array
    data_int = int.from_bytes(data, "little")
    return (data_int >> start_bit) & ((1 << bit_length) - 1)


def evaluate_safe_expression(expression: str, value: float):
    # Run a simple math expression that uses 'x' — safely
    if not expression:
        return None
    allowed = {"math": math, "min": min, "max": max, "abs": abs, "pow": pow, "__builtins__": {}}
    try:
        return eval(expression, allowed, {"x": value})
    except Exception:
        return None


def load_can_config(config_path: Path) -> dict:
    # Load up the CAN config JSON and turn the IDs into ints
    with open(config_path, "r") as f:
        raw_cfg = json.load(f)
    can_map = {
        int(k, 16) if isinstance(k, str) and k.lower().startswith("0x") else int(k): v
        for k, v in raw_cfg.items()
    }
    return can_map


def decode_can_frame(frame, config: dict) -> dict | None:
    # Decode one CAN frame based on what's in the config file
    can_id = frame.arbitration_id
    if can_id not in config:
        return None

    frame_cfg = config[can_id]
    data = frame.data
    decoded = {}

    for signal_name, signal_spec in frame_cfg.get("signals", {}).items():
        # handle byte-based signals
        if "start" in signal_spec and "length" in signal_spec:
            offset = int(signal_spec["start"])
            length = int(signal_spec["length"])
            raw_val = parse_bytes_little_endian(data, offset, length)
        # handle bit-based signals
        elif "bits" in signal_spec:
            start_bit, bit_len = signal_spec["bits"]
            raw_val = extract_bits_little_endian(data, start_bit, bit_len)
        else:
            continue

        # basic scaling and offset
        value = raw_val * float(signal_spec.get("scale", 1.0)) + float(signal_spec.get("offset", 0.0))

        # apply any math formulas from the config (if provided)
        if "formula" in signal_spec:
            computed = evaluate_safe_expression(signal_spec["formula"], raw_val)
            if computed is not None:
                value = computed

        decoded[signal_name] = value

    return decoded



def main():
    cfg = load_can_config(CONFIG_PATH)

    # Track current signal states 
    state = {}
    for entry in cfg.values():
        for sig_name in entry.get("signals", {}):
            state[sig_name] = None

    # Open CAN interface
    try:
        bus = can.interface.Bus(channel=CAN_CHANNEL, interface=INTERFACE)
    except Exception as e:
        logging.error(f"Failed to open CAN: {e}")
        sys.exit(1)

    # Set up CSV logging
    csv_path = LOG_DIR / f"decoded_{timestamp}.csv"
    csv_f = open(csv_path, "w", newline="")
    csv_writer = csv.DictWriter(csv_f, fieldnames=["t", "can_id"] + sorted(state.keys()))
    csv_writer.writeheader()

    last_print = 0
    print_rate = 0.2  # seconds between live dashboard updates

    print("Listening on CAN0... (Ctrl+C to quit)\n")

    try:
        for frame in bus:
            decoded = decode_can_frame(frame, cfg)
            if decoded:
                state.update(decoded)

            # Write every frame to CSV
            csv_writer.writerow({
                "t": time.time(),
                "can_id": hex(frame.arbitration_id),
                **state
            })
            csv_f.flush()

            # Console dashboard (refresh every 0.2s)
            now = time.time()
            if now - last_print >= print_rate:
                last_print = now
                speed = state.get("speed_kph")
                steer = state.get("steering_angle_deg")
                brake = state.get("brake_position_pct")
                throttle = state.get("accelerator_pct") or state.get("throttle_valve_pct")
                gear = state.get("gear")
                yaw = state.get("yaw_rate_deg_s")
                latg = state.get("lat_accel_g")
                longg = state.get("long_accel_g")

                line = (
                    f"Speed: {speed or 0:.1f} km/h | "
                    f"Steer: {steer or 0:.1f}° | "
                    f"Brake: {brake or 0:.0f}% | "
                    f"Throttle: {throttle or 0:.0f}% | "
                    f"Gear: {int(gear) if gear is not None else '-'} | "
                    f"Yaw: {yaw or 0:.2f}°/s | "
                    f"LatG: {latg or 0:.2f} | "
                    f"LongG: {longg or 0:.2f}"
                )
                print("\r" + line, end="", flush=True)

    except KeyboardInterrupt:
        print("\nInterrupted — shutting down...")
    finally:
        csv_f.close()
        if HAS_GPIO:
            GPIO.cleanup()
        try:
            bus.shutdown()
        except Exception:
            pass
        logging.info("Exiting.")


if __name__ == "__main__":
    main()