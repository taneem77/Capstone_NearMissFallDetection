/*
 * ============================================================================
 * Smart Cane Telemetry & Pre-Impact Stumble Detection Node (ESA Production)
 * Hardware: ESP32 DevKit V1 + MPU6050 (I2C) + Interlink FSR 402 (ADC)
 * Output Format: CSV Stream (time_ms, ax, ay, az, gx, gy, gz, grip_adc)
 * PES University | Capstone Project Phase-1 (PW_27_MHR_01)
 * ============================================================================
 */

#include <Wire.h>

#define MPU_ADDR 0x68
#define PIN_FSR 34
#define PIN_LED 2
#define SAMPLE_INTERVAL_MS 10 // 100 Hz sampling loop (10 ms tick)

// Dual-Threshold Rule Parameters
const float JERK_THRESHOLD = 55.0;     // m/s^3
const int GRIP_RISE_THRESHOLD = 800;   // ADC count rise
const int COINCIDENCE_WINDOW_MS = 350; // 350 ms physiological window

// Raw and converted variables
int16_t raw_ax, raw_ay, raw_az;
int16_t raw_gx, raw_gy, raw_gz;

float ax, ay, az; // in m/s^2
float gx, gy, gz; // in deg/s
float prev_ax = 0, prev_ay = 0, prev_az = 9.80665;

int raw_grip = 0;
int baseline_grip = 500;
unsigned long last_jerk_trigger_ms = 0;
unsigned long last_sample_time = 0;

void setup() {
  Serial.begin(115200);
  pinMode(PIN_LED, OUTPUT);
  digitalWrite(PIN_LED, LOW);

  // Initialize I2C on standard ESP32 pins: SDA=21, SCL=22
  Wire.begin(21, 22, 400000); // 400 kHz fast I2C mode
  
  // Wake up MPU-6050
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x6B); // PWR_MGMT_1
  Wire.write(0x00); // Clear sleep bit
  Wire.endTransmission(true);

  // Set Accelerometer full-scale range to +/- 4g (8192 LSB/g)
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x1C); // ACCEL_CONFIG
  Wire.write(0x08); // +/- 4g
  Wire.endTransmission(true);

  // Set Gyroscope full-scale range to +/- 500 deg/s (65.5 LSB/(deg/s))
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x1B); // GYRO_CONFIG
  Wire.write(0x08); // +/- 500 deg/s
  Wire.endTransmission(true);

  // Print standard CSV header
  Serial.println("time_ms,ax,ay,az,gx,gy,gz,grip_adc");

  // Confirmation flash on LED
  digitalWrite(PIN_LED, HIGH); delay(100);
  digitalWrite(PIN_LED, LOW);  delay(100);
  digitalWrite(PIN_LED, HIGH); delay(100);
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

  // 1. Read MPU-6050 Registers (14 consecutive bytes)
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x3B);
  Wire.endTransmission(false);
  Wire.requestFrom(MPU_ADDR, 14, true);

  if (Wire.available() >= 14) {
    raw_ax = (Wire.read() << 8) | Wire.read();
    raw_ay = (Wire.read() << 8) | Wire.read();
    raw_az = (Wire.read() << 8) | Wire.read();
    Wire.read(); Wire.read(); // Skip internal temperature sensor
    raw_gx = (Wire.read() << 8) | Wire.read();
    raw_gy = (Wire.read() << 8) | Wire.read();
    raw_gz = (Wire.read() << 8) | Wire.read();

    // Convert raw to engineering units (+/- 4g -> 8192 LSB/g)
    ax = (raw_ax / 8192.0) * 9.80665;
    ay = (raw_ay / 8192.0) * 9.80665;
    az = (raw_az / 8192.0) * 9.80665;
    gx = raw_gx / 65.5;
    gy = raw_gy / 65.5;
    gz = raw_gz / 65.5;
  }

  // 2. Read Handle Grip ADC (GPIO 34)
  raw_grip = analogRead(PIN_FSR);

  // 3. Compute Instantaneous Jerk Vector (m/s^3)
  float jx = (ax - prev_ax) / dt;
  float jy = (ay - prev_ay) / dt;
  float jz = (az - prev_az) / dt;
  float jerk_mag = sqrt(jx * jx + jy * jy + jz * jz);

  prev_ax = ax;
  prev_ay = ay;
  prev_az = az;

  // Slow exponential moving average for resting grip baseline
  baseline_grip = (int)(0.99 * baseline_grip + 0.01 * raw_grip);
  int grip_rise = raw_grip - baseline_grip;

  // 4. Dual-Domain Temporal Coincidence Logic
  if (jerk_mag >= JERK_THRESHOLD) {
    last_jerk_trigger_ms = current_time;
  }

  // If reflex grip rise occurs within 350 ms following jerk spike
  if ((current_time - last_jerk_trigger_ms <= COINCIDENCE_WINDOW_MS) && (grip_rise >= GRIP_RISE_THRESHOLD)) {
    digitalWrite(PIN_LED, HIGH); // Confirm near-fall stumble
  } else {
    digitalWrite(PIN_LED, LOW);
  }

  // 5. Stream Formatted Standard CSV Line
  Serial.print(current_time); Serial.print(",");
  Serial.print(ax, 3); Serial.print(",");
  Serial.print(ay, 3); Serial.print(",");
  Serial.print(az, 3); Serial.print(",");
  Serial.print(gx, 2); Serial.print(",");
  Serial.print(gy, 2); Serial.print(",");
  Serial.print(gz, 2); Serial.print(",");
  Serial.println(raw_grip);
}
