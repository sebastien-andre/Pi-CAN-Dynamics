# Pi-CAN Dynamics

> A Raspberry Pi CAN-bus data logger and AI learning project for understanding vehicle dynamics and improving driver performance.



## Overview

**Pi-CAN Dynamics** is a personal research and learning project that connects a **Raspberry Pi** to the **CAN bus** of a **2014 Scion FR-S**.  
The system captures real-time sensor data (steering angle, wheel speed, throttle, brake pressure, yaw rate, etc.) directly from the car’s CAN network for analysis and visualization.

Long term, Pi-CAN Dynamics will train an **AI predictive model** capable of analyzing laps, learning from driver inputs, and giving **contextual real-time feedback** to improve lap and autocross times.

This project also served as a way for me to explore **embedded systems**, **vehicle telemetry**, and **machine learning** integration in a real-world automotive environment.

![CAN Logger Output](images/logger.jpg)

## Hardware

### Current

- **Raspberry Pi Zero 2 W** *(current logger)*  
- **RS485 / CAN HAT** with MCP2515 + TJA1050 transceiver  
- **OBD-II connector harness** (pins: 6 = CAN-H, 14 = CAN-L, 4/5 = GND)

### Planned Improvements
- **Upgrade to Raspberry Pi 5 (8 GB)** for real-time predictive modeling  
- **Integrate via head-unit harness** for a hidden CAN connection  
- **Add dual IMUs** (front & rear) to capture chassis motion, slip, and balance  
- **Add GPS module** for track mapping and lap segmentation  
- **Replicate the “pedal dance” sequence** electronically — disabling traction and stability systems without temperature or manual input requirements  
- **Include switch input** inside the cabin to toggle data logging mode
- **Mount Pi + HAT in a custom glovebox enclosure** for easy maintenance and upgrades  
- **Implement removable data storage** for simple PC data transfer
- **Develop predictive AI model** that learns from driver behavior and lap data  
- **Provide real-time driving suggestions** via a compact display:
  - “Brake later next corner entry”  
  - “Get on throttle earlier”  
  - “Reduce steering input at corner exit”  
- **Correlate telemetry with GPS coordinates** for segment-specific analysis  



