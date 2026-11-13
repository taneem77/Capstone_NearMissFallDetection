# Smart Cane Hardware Wiring & Mounting Specification

This document details the exact hardware wiring, pin mapping, circuit schematic, and physical cane mounting instructions for the Smart Cane node.

---

## 1. Pin Mapping & Interconnect Table

| Component | Pin Label | Connected to ESP32 Pin | Function / Description |
| :--- | :--- | :--- | :--- |
| **MPU-6050 IMU** | VCC | **3V3** | 3.3V Power Rail |
| | GND | **GND** | Common Ground |
| | SDA | **GPIO 21** | I2C Data Line (Internal Pullup) |
| | SCL | **GPIO 22** | I2C Clock Line (Internal Pullup) |
| | AD0 | **GND** | Sets I2C Address to `0x68` |
| | INT | *Not Connected* | Interrupt not required in polling mode |
| **FSR 402 Grip Sensor** | Pin 1 | **3V3** | 3.3V Power Rail |
| | Pin 2 | **GPIO 34** & **10 kΩ Resistor** | Voltage divider tap to ADC input |
| **Fixed Resistor** | 10 kΩ Pin 1 | **GPIO 34** & **FSR Pin 2** | Divider center point |
| | 10 kΩ Pin 2 | **GND** | Pull-down ground reference |
| **Status Indicator** | Anode | **GPIO 2** | Onboard Blue LED (Lights on Near-Fall) |

---

## 2. Circuit Schematic (ASCII Diagram)

```
                    +------------------------------------+
                    |         ESP32 DevKit V1            |
                    |                                    |
     [3.3V Rail] <--| 3V3                                |
     [GND Rail]  <--| GND                                |
                    |                                    |
                    | GPIO21 (SDA) ---------\            |
                    | GPIO22 (SCL) -----\   |            |
                    |                   |   |            |
                    | GPIO34 (ADC) -+   |   |            |
                    |               |   |   |            |
                    | GPIO2 (LED)   |   |   |            |
                    +---------------+---|---|------------+
                                    |   |   |
                                    |   |   |
              +---------------------+   |   |
              |                         |   |
              |     +-------------------+   |
              |     |   +-------------------+
              |     |   |
              v     v   v
       +--------------------+
       |     MPU-6050       |
       | VCC  GND  SCL  SDA |
       +--|----|------------+
          |    |
          |    +--- [GND Rail]
          +-------- [3.3V Rail]


        Grip Force Voltage Divider Circuit:
        -----------------------------------
        [3.3V Rail]
             |
             |
          [ FSR ] (Handle Grip Sensor)
             |
             +--------------------> GPIO 34 (ESP32 ADC Input)
             |
          [10 kΩ] (Fixed Pull-Down Resistor)
             |
             |
         [GND Rail]
```

---

## 3. Physical Cane Mounting Guidelines (From Lab Verification)

```
         ===================[ FSR Grip Sensor ]===================  <-- Handle (Under Palm)
         |                                                       |
         +--------------------------+----------------------------+
                                    |
                                    |  <-- Cane Shaft (Upper)
                              [ MPU-6050 ] (Mounted flat on shaft)
                                    |
                           [ Mini-Breadboard ]
                           [ ESP32 DevKit V1 ] (Velcro / Zip-tie)
                           [ 10 kΩ Resistor  ]
                                    |
                                    |  <-- USB Cable taped down
                                    |      along shaft every 10 cm
                                    |
                                    |
                                  =====  Rubber Tip
```

### Critical Assembly Tips:
1. **Single Breadboard Layout**:
   - One mini solderless breadboard (170 tie points) holds the ESP32, 10 kΩ resistor, and jumper wires.
   - If mounting the MPU6050 separately on the shaft is fiddly, place the MPU6050 directly onto the breadboard next to the ESP32. The rigid shaft transmits identical kinematic accelerations.
2. **Handle Grip Sensor Placement**:
   - The FSR is the **only component mounted on the handle**.
   - Tape the FSR by its outer perimeter edges **only**. Never tape across the circular sensing spot; tape pressure acts as permanent mechanical preload and weakens dynamic sensitivity.
3. **Mechanical Rigidity (Zero Bounce)**:
   - Loose breadboards or dangling jumper wires create spurious vibrational spikes that trigger false alarms.
   - Fasten the breadboard flat against the cane shaft using dual Velcro straps or electrical tape.
   - Secure the USB cable down the shaft at 10 cm intervals, leaving 3 cm of slack near the handle to prevent strain.
4. **Consistency**:
   - Keep the MPU6050 axis orientation identical across collection sessions (Z-axis pointing downward along the shaft).
   - Ensure the volunteer grips the handle with their palm centered over the FSR circle.
