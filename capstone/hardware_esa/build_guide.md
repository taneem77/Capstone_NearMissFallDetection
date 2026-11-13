# Smart Cane Hardware Build Guide & Integration Specification

This step-by-step guide details the bill of materials, circuit schematic, physical cane mounting, bench verification checks, FSR calibration, and troubleshooting.

---

## 1. Bill of Materials (BOM) & Costs in INR

| Item # | Component | Technical Specification | Quantity | Unit Price (INR) | Total Cost (INR) | Indian Vendor |
| :---: | :--- | :--- | :---: | :---: | :---: | :--- |
| 1 | **Microcontroller Board** | ESP32 DevKit V1 (30-pin, Dual Core 240 MHz) | 1 | ₹450 | ₹450 | Robu.in / ElectronicsComp |
| 2 | **6-DOF IMU Sensor** | MPU-6050 (3-axis Accel ±4g, 3-axis Gyro ±500°/s) | 1 | ₹180 | ₹180 | Robu.in / Robocraze |
| 3 | **Grip Force Sensor** | Interlink FSR 402 (0.5" circular active zone) | 1 | ₹650 | ₹650 | Robu.in / Sunrom |
| 4 | **Fixed Pull-Down Resistor** | 10 kΩ Metal Film 1/4W (0.1% tolerance) | 2 | ₹2 | ₹4 | Local Electronics / Robu |
| 5 | **Mini Solderless Breadboard**| 170 Tie-point Mini Breadboard | 1 | ₹55 | ₹55 | Robu.in |
| 6 | **Jumper Wires** | Male-to-Female & Male-to-Male (20 cm) | 10 pcs | ₹40 | ₹40 | Robu.in |
| 7 | **Mechanical Fasteners** | Velcro Cable Straps, 3M Double-Sided Foam Tape | 1 set | ₹75 | ₹75 | Local Hardware Store |
| 8 | **Shielded USB Cable** | Micro-USB to USB-A (1.5 m) | 1 | ₹80 | ₹80 | Amazon India |
| **TOTAL** | **Hardware Prototype Cost** | | | | **₹1,534** | *(~ USD $18.40)* |

---

## 2. Pin Interconnect Table & Circuit Schematic

### Pin Mapping Table

| Component | Pin Label | Connected to ESP32 Pin | Function / Notes |
| :--- | :--- | :--- | :--- |
| **MPU-6050 IMU** | VCC | **3V3** | 3.3V Power Rail |
| | GND | **GND** | Ground Rail |
| | SDA | **GPIO 21** | I2C Data Line (Internal Pullup) |
| | SCL | **GPIO 22** | I2C Clock Line (Internal Pullup) |
| | AD0 | **GND** | Sets I2C Address to `0x68` |
| | INT | *Not Connected* | Polled at 100 Hz timer loop |
| **FSR 402 Handle Sensor** | Terminal 1 | **3V3** | 3.3V Power Rail |
| | Terminal 2 | **GPIO 34** & **10 kΩ Resistor** | Voltage divider tap into ADC |
| **Fixed Resistor** | 10 kΩ Leg 1 | **GPIO 34** & **FSR Terminal 2** | Divider center point |
| | 10 kΩ Leg 2 | **GND** | Pull-down ground reference |
| **Indicator LED** | Anode | **GPIO 2** | Onboard Blue LED (Lights on near-fall) |

### ASCII Circuit Schematic

```
                      +---------------------------------------+
                      |            ESP32 DevKit V1            |
                      |                                       |
       [3.3V Rail] <--| 3V3                                   |
       [GND Rail]  <--| GND                                   |
                      |                                       |
                      | GPIO21 (SDA) -----------\             |
                      | GPIO22 (SCL) -------\   |             |
                      |                     |   |             |
                      | GPIO34 (ADC) ---+   |   |             |
                      |                 |   |   |             |
                      | GPIO2 (LED)     |   |   |             |
                      +-----------------|---|---|-------------+
                                        |   |   |
                                        |   |   |
                +-----------------------+   |   |
                |                           |   |
                |       +-------------------+   |
                |       |   +-------------------+
                |       |   |
                v       v   v
         +----------------------+
         |       MPU-6050       |
         | VCC  GND   SCL   SDA |
         +---|---|--------------+
             |   |
             |   +--- [GND Rail]
             +------- [3.3V Rail]


          Grip Force Voltage Divider Circuit:
          -----------------------------------
          [3.3V Rail]
               |
               |
            [ FSR ] (Handle Palm Sensor)
               |
               +---------------------> GPIO 34 (ESP32 ADC Input)
               |
            [10 kΩ] (Fixed Pull-Down Resistor)
               |
               |
           [GND Rail]
```

---

## 3. Physical Cane Mounting Guidelines

```
           ====================[ FSR Grip Sensor ]====================  <-- Handle (Under Palm)
           |                                                         |
           +----------------------------+----------------------------+
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
                                      =====  Rubber Ferrule Tip
```

### Critical Mounting Instructions:
1. **FSR Handle Mounting**:
   - The FSR is the **only component mounted on the cane handle**.
   - Tape the FSR by its outer perimeter edges **only**. Never tape across the circular sensing area; adhesive tension applies static preload and ruins dynamic sensitivity.
2. **Breadboard & IMU Fastening**:
   - The mini-breadboard houses the ESP32, 10 kΩ resistor, and jumper wires.
   - If mounting the MPU-6050 separately on the shaft is cumbersome, mount it directly onto the mini-breadboard. Because the cane is a rigid strut, vibrations transmit identically.
   - Fasten the breadboard flat against the cane shaft using dual Velcro straps.
3. **Vibration Damping & Zero Bounce**:
   - Dangling wires or loose boards create fake impact jolts that trigger false alarms.
   - Tape the USB cable flush against the cane shaft every 10 cm, leaving 3 cm of slack near the handle to prevent strain.

---

## 4. Bench Verification Checks (Pass/Fail Criteria)

Before performing any walking tests, execute this 4-step bench test:
1. **Power & I2C Handshake Check**:
   - *Action*: Power ESP32 over USB. Open Serial Monitor at 115200 baud.
   - *Pass Criteria*: Serial prints formatted CSV lines at ~100 Hz. If `MPU6050 initialization failed` appears, check SDA/SCL lines.
2. **Gravity Alignment Check**:
   - *Action*: Hold cane vertically upright at rest.
   - *Pass Criteria*: $a_z \approx 9.8\text{ m/s}^2$ ($\pm 0.5\text{ m/s}^2$), while $a_x \approx 0$ and $a_y \approx 0$.
3. **Handle Grip Response Check**:
   - *Action*: Rest hand gently on handle (no grip); `grip_adc` reads between 200 and 600 counts. Squeeze handle firmly; `grip_adc` spikes beyond 2200 counts.
   - *Pass Criteria*: Dynamic rise $\Delta ADC > 1500$ counts upon squeeze.
4. **Cane Tap Rejection Check**:
   - *Action*: Firmly tap cane rubber tip onto hard floor without squeezing the handle.
   - *Pass Criteria*: Acceleration and jerk spike, but onboard LED on GPIO 2 **remains OFF** (verifying false alarm rejection).

---

## 5. Troubleshooting Matrix

| Symptom | Probable Cause | Corrective Action |
| :--- | :--- | :--- |
| **ESP32 boots in brownout loop** | Insufficient USB port current (<500 mA). | Use a powered USB hub or direct motherboard USB-3 port. |
| **MPU-6050 I2C read error** | Loose SDA/SCL jumper wires or wrong pins. | Ensure SDA connects to GPIO 21 and SCL connects to GPIO 22. Verify AD0 is tied to GND. |
| **Grip ADC reads 4095 constantly** | FSR shorted to 3.3V or missing 10 kΩ pull-down. | Check voltage divider wiring. Confirm 10 kΩ resistor is connected between GPIO 34 and GND. |
| **Spurious jerk spikes during steady walk** | Loose breadboard bouncing against cane shaft. | Secure mini-breadboard tightly with dual Velcro straps. Tape down jumper wires flush. |
