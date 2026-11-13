/*
 * ============================================================================
 * Smart Cane Telemetry & On-Device Near-Fall Detector Node
 * Hardware: ESP32 DevKit V1 + MPU6050 (I2C) + FSR 402 Force Sensor (ADC)
 * PES University | Capstone Project Phase-1 (PW_27_MHR_01)
 * ============================================================================
 * Pin Connections:
 *   ESP32 3V3  --> MPU6050 VCC & FSR Terminal 1
 *   ESP32 GND  --> MPU6050 GND & 10k Resistor Terminal 2
 *   ESP32 GPIO21 (SDA) --> MPU6050 SDA
 *   ESP32 GPIO22 (SCL) --> MPU6050 SCL
 *   ESP32 GPIO34 (ADC6) --> Junction of FSR Terminal 2 & 10k Resistor
 *   ESP32 GPIO2  --> Onboard Indicator LED
 * ============================================================================
 */

#include <Wire.h>

#define MPU_ADDR 0x68
#define PIN_FSR 34
#define PIN_LED 2
#define SAMPLE_INTERVAL_MS 10 // 100 Hz sampling (10 ms per tick)

// Detection Thresholds (On-Device Dual Threshold Rule)
const float JERK_THRESHOLD = 55.0; // m/s^3
const int GRIP_RISE_THRESHOLD = 800; // ADC count rise
const int COINCIDENCE_WINDOW_MS = 350;

// Variables for Kinematic & Kinetic Tracking
int16_t raw_ax, raw_ay, raw_az;
int16_t raw_gx, raw_gy, raw_gz;

float ax, ay, az; // in m/s^2
float gx, gy, gz; // in deg/s
float prev_ax = 0, prev_ay = 0, prev_az = 9.81;

int raw_grip = 0;
int baseline_grip = 500;
unsigned long last_jerk_trigger_ms = 0;
unsigned long last_sample_time = 0;

void setup() {
  Serial.begin(115200);
  pinMode(PIN_LED, OUTPUT);
  digitalWrite(PIN_LED, LOW);
  
  // Initialize I2C for MPU6050
  Wire.begin(21, 22);
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x6B); // PWR_MGMT_1 register
  Wire.write(0);    // Wake up MPU-6050
  Wire.endTransmission(true);

  // Configure Accelerometer (+/- 4g) & Gyro (+/- 500 deg/s)
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x1C); // ACCEL_CONFIG
  Wire.write(0x08); // +/- 4g
  Wire.endTransmission(true);

  // Flash LED twice to confirm boot
  digitalWrite(PIN_LED, HIGH); delay(150);
  digitalWrite(PIN_LED, LOW);  delay(150);
  digitalWrite(PIN_LED, HIGH); delay(150);
  digitalWrite(PIN_LED, LOW);
}

void loop() {
  unsigned long current_time = millis();
  if (current_time - last_sample_time < SAMPLE_INTERVAL_MS) {
    return;
  }
  
  float dt = (current_time - last_sample_time) / 1000.0;
  if (dt <= 0.0) dt = 0.01;
  last_sample_time = current_time;

  // 1. Read MPU6050 Registers
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x3B); // Starting register for Accel readings
  Wire.endTransmission(false);
  Wire.requestFrom(MPU_ADDR, 14, true);

  if (Wire.available() >= 14) {
    raw_ax = (Wire.read() << 8) | Wire.read();
    raw_ay = (Wire.read() << 8) | Wire.read();
    raw_az = (Wire.read() << 8) | Wire.read();
    Wire.read(); Wire.read(); // Skip temperature
    raw_gx = (Wire.read() << 8) | Wire.read();
    raw_gy = (Wire.read() << 8) | Wire.read();
    raw_gz = (Wire.read() << 8) | Wire.read();

    // Convert raw to engineering units (+/- 4g range -> 8192 LSB/g)
    ax = (raw_ax / 8192.0) * 9.80665;
    ay = (raw_ay / 8192.0) * 9.80665;
    az = (raw_az / 8192.0) * 9.80665;
    gx = raw_gx / 65.5;
    gy = raw_gy / 65.5;
    gz = raw_gz / 65.5;
  }

  // 2. Read Grip Sensor (ADC on GPIO34)
  raw_grip = analogRead(PIN_FSR);

  // 3. Compute Jerk Vector Derivative (m/s^3)
  float jx = (ax - prev_ax) / dt;
  float jy = (ay - prev_ay) / dt;
  float jz = (az - prev_az) / dt;
  float jerk_mag = sqrt(jx*jx + jy*jy + jz*jz);

  prev_ax = ax;
  prev_ay = ay;
  prev_az = az;

  // Track slow baseline grip (exponential filter)
  baseline_grip = (int)(0.99 * baseline_grip + 0.01 * raw_grip);
  int grip_rise = raw_grip - baseline_grip;

  // 4. On-Device Dual-Domain Coincidence Logic
  bool event_flag = false;
  if (jerk_mag >= JERK_THRESHOLD) {
    last_jerk_trigger_ms = current_time;
  }

  // If reflex grip rise occurs within 350 ms of jerk onset
  if ((current_time - last_jerk_trigger_ms <= COINCIDENCE_WINDOW_MS) && (grip_rise >= GRIP_RISE_THRESHOLD)) {
    event_flag = true;
    digitalWrite(PIN_LED, HIGH);
  } else {
    digitalWrite(PIN_LED, LOW);
  }

  // 5. Stream Formatted JSON Line to Host
  Serial.print("{\"t\":"); Serial.print(current_time);
  Serial.print(",\"ax\":"); Serial.print(ax, 2);
  Serial.print(",\"ay\":"); Serial.print(ay, 2);
  Serial.print(",\"az\":"); Serial.print(az, 2);
  Serial.print(",\"gx\":"); Serial.print(gx, 1);
  Serial.print(",\"gy\":"); Serial.print(gy, 1);
  Serial.print(",\"gz\":"); Serial.print(gz, 1);
  Serial.print(",\"grip\":"); Serial.print(raw_grip);
  Serial.print(",\"jerk\":"); Serial.print(jerk_mag, 1);
  Serial.print(",\"alert\":"); Serial.print(event_flag ? 1 : 0);
  Serial.println("}");
}
