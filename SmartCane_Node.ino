// SmartCane_Node.ino
// MPU6050 (raw accel + gyro) + FSR grip sensor -> JSON lines over USB serial, 100 Hz.
// Output matches src/live/serial_logger.py exactly (acc in m/s^2, gyro in deg/s, grip = raw ADC 0..4095).
// No libraries needed beyond the ESP32 board package (uses Wire only).
//
// Arduino IDE: Board "ESP32 Dev Module" (or your C3 board), Serial Monitor/logger baud = 460800.

#include <Wire.h>

#if defined(CONFIG_IDF_TARGET_ESP32C3)
  #define SDA_PIN 8
  #define SCL_PIN 9
  #define FSR_PIN 2        // ADC1 pin on the C3
#else                       // classic ESP32 DevKit
  #define SDA_PIN 21
  #define SCL_PIN 22
  #define FSR_PIN 34       // ADC1 pin, input only
#endif

#define MPU_ADDR   0x68    // AD0 low/unconnected
#define BAUD       460800
#define RATE_HZ    100

static const float G_MS2   = 9.80665f;
static const float ACC_LSB = 4096.0f;   // +-8 g
static const float GYR_LSB = 32.8f;     // +-1000 deg/s

static void mpuWrite(uint8_t reg, uint8_t val) {
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(reg);
  Wire.write(val);
  Wire.endTransmission();
}

static bool mpuRead(int16_t *d) {       // d[0..2]=acc, d[3]=temp, d[4..6]=gyro
  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x3B);
  if (Wire.endTransmission(false) != 0) return false;
  if (Wire.requestFrom((uint8_t)MPU_ADDR, (uint8_t)14) != 14) return false;
  for (int i = 0; i < 7; i++) {
    int16_t hi = Wire.read();
    int16_t lo = Wire.read();
    d[i] = (hi << 8) | lo;
  }
  return true;
}

static uint32_t t0, nextTick;

void setup() {
  Serial.begin(BAUD);
  delay(500);
  Wire.begin(SDA_PIN, SCL_PIN);
  Wire.setClock(400000);

  Wire.beginTransmission(MPU_ADDR);
  Wire.write(0x75);                       // WHO_AM_I
  Wire.endTransmission(false);
  Wire.requestFrom((uint8_t)MPU_ADDR, (uint8_t)1);
  uint8_t who = Wire.available() ? Wire.read() : 0;
  Serial.print("# WHO_AM_I=0x"); Serial.println(who, HEX);   // 0x68 is normal; lines starting with # are ignored by the logger
  if (who == 0) Serial.println("# ERROR: MPU6050 not found. Check SDA/SCL/VCC/GND wires.");

  mpuWrite(0x6B, 0x00);                   // wake up
  delay(100);
  mpuWrite(0x1A, 0x03);                   // low-pass ~44 Hz
  mpuWrite(0x1B, 0x10);                   // gyro +-1000 deg/s
  mpuWrite(0x1C, 0x10);                   // accel +-8 g

  analogReadResolution(12);
  t0 = micros();
  nextTick = t0;
}

void loop() {
  nextTick += 1000000UL / RATE_HZ;
  while ((int32_t)(micros() - nextTick) < 0) { }       // wait for next 10 ms tick

  int16_t d[7];
  if (!mpuRead(d)) return;                             // skip bad read, logger tolerates gaps

  int grip = 0;
  for (int i = 0; i < 4; i++) grip += analogRead(FSR_PIN);
  grip /= 4;

  float t = (micros() - t0) / 1e6f;
  char buf[160];
  snprintf(buf, sizeof(buf),
    "{\"timestamp\":%.3f,\"acc_x\":%.3f,\"acc_y\":%.3f,\"acc_z\":%.3f,"
    "\"gyro_x\":%.2f,\"gyro_y\":%.2f,\"gyro_z\":%.2f,\"grip\":%d}",
    t,
    d[0] / ACC_LSB * G_MS2, d[1] / ACC_LSB * G_MS2, d[2] / ACC_LSB * G_MS2,
    d[4] / GYR_LSB, d[5] / GYR_LSB, d[6] / GYR_LSB,
    grip);
  Serial.println(buf);
}
