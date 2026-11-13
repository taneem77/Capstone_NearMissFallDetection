# Bill of Materials (BOM) & Cost Breakdown

The Smart Cane prototype is engineered using cost-effective, readily available commercial-off-the-shelf (COTS) components to guarantee economic accessibility for elderly individuals and public health centers.

---

## 1. Primary Component List & Cost in INR

| Item # | Component Name | Model / Specification | Quantity | Unit Price (INR) | Total (INR) | Primary Indian Vendor |
| :---: | :--- | :--- | :---: | :---: | :---: | :--- |
| 1 | **Microcontroller Board** | ESP32 DevKit V1 (30-pin, Dual Core, Wi-Fi/BLE) | 1 | ₹450 | ₹450 | Robu.in / ElectronicsComp |
| 2 | **Inertial Measurement Unit** | MPU-6050 (3-axis Accel + 3-axis Gyro, I2C) | 1 | ₹180 | ₹180 | Robu.in / Robocraze |
| 3 | **Grip Force Sensor** | Interlink FSR 402 (0.5" circular, 0.2N - 20N) | 1 | ₹650 | ₹650 | Robu.in / Sunrom |
| 4 | **Fixed Resistor** | 10 kΩ Metal Film 1/4W (0.1% tolerance) | 2 | ₹2 | ₹4 | Local Electronics / Robu |
| 5 | **Mini Breadboard** | 170 Tie-point Mini Solderless Breadboard | 1 | ₹55 | ₹55 | Robu.in |
| 6 | **Jumper Wires** | Male-to-Female & Male-to-Male (20 cm) | 10 pcs | ₹40 | ₹40 | Robu.in |
| 7 | **Mounting Hardware** | Velcro Straps, Zip-ties, 3M Double-Sided Foam Tape | 1 set | ₹75 | ₹75 | Local Hardware Store |
| 8 | **USB Interface Cable** | Micro-USB to USB-A (1.5 m Shielded) | 1 | ₹80 | ₹80 | Amazon India |
| **TOTAL** | **Hardware Prototype Cost** | | | | **₹1,534** | *(~ USD $18.40)* |

---

## 2. Low-Cost Alternatives & Future Custom PCB Roadmap

| Current Prototype Part | Low-Cost / Scaled Alternative | Trade-off / Technical Assessment |
| :--- | :--- | :--- |
| **ESP32 DevKit V1 (₹450)** | **ESP32-C3 SuperMini (₹220)** | Smaller footprint ($22 \times 18\text{ mm}$), single-core RISC-V, cuts power by 40%, fits inside cane handle cavity. |
| **MPU-6050 (₹180)** | **STMicroelectronics LSM6DSO (₹240)** | Built-in finite state machine, ultra-low noise, reduced drift, native 1.8V support. |
| **Interlink FSR 402 (₹650)** | **Conductive Velostat Film Strip (₹90)** | Piezoresistive custom strip covering entire handle circumference; lower cost but requires calibration. |
| **Mini Breadboard (₹55)** | **Custom 2-Layer Rigid-Flex PCB (₹150 in bulk)** | Eliminates loose wiring, fits inside the cane shaft, enhances durability and moisture protection. |
