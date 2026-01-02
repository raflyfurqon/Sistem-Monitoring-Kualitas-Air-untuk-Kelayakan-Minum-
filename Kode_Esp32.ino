#include <Arduino.h>
#include <WiFi.h>
#include <Firebase_ESP_Client.h>
#include <Wire.h>
#include <math.h>
#include <time.h>

// ================= WIFI =================
#define WIFI_SSID "idoy"
#define WIFI_PASSWORD "112345678"

// ================= FIREBASE =================
#define API_KEY "AIzaSyCy0aOLAdKWrYxc4_qPkp1WL0GsNfGGlhI"
#define DATABASE_URL "water-quality-3f1b1-default-rtdb.asia-southeast1.firebasedatabase.app"

// ================= FIREBASE OBJECT =================
FirebaseData fbdo;
FirebaseAuth auth;
FirebaseConfig config;

// ================= PIN INPUT =================
constexpr int PIN_TURB = 34;
constexpr int PIN_PH   = 32;
constexpr int PIN_TDS  = 35;

// ================= PIN OUTPUT =================
constexpr int PIN_LED_HIJAU = 25;
constexpr int PIN_LED_BIRU  = 26;
constexpr int PIN_LED_MERAH = 27;
constexpr int PIN_BUZZER    = 14;

// ================= ADC =================
constexpr float VREF = 3.3f;
constexpr float ADC_MAX = 4095.0f;

// ================= TURBIDITY CAL =================
constexpr int TURB_SAMPLES = 30;
constexpr int TURB_SAMPLE_DELAY_MS = 2;

constexpr int N_CAL = 5;
int adcCal[N_CAL] = {1800, 1600, 1300, 1050, 900};
float ntuCal[N_CAL] = {0.1, 1.0, 5.0, 25.0, 100.0};

// ================= pH =================
float calibration_value = 23.31;
unsigned long avgval;
int buffer_arr[10], temp;
float ph_act;

// ================= TIME SYNC =================
// Timezone offset untuk WIB (UTC+7)
const long gmtOffset_sec = 7 * 3600;
const int daylightOffset_sec = 0;

void syncTime() {
  configTime(gmtOffset_sec, daylightOffset_sec, "pool.ntp.org", "time.nist.gov");
  Serial.print("Syncing time");
  time_t now = time(nullptr);
  int attempts = 0;
  while (now < 1700000000 && attempts < 20) {
    delay(500);
    Serial.print(".");
    now = time(nullptr);
    attempts++;
  }
  if (now >= 1700000000) {
    Serial.println("\nTime synced successfully!");
    struct tm timeinfo;
    getLocalTime(&timeinfo);
    Serial.print("Current time: ");
    Serial.println(&timeinfo, "%H:%M:%S");
  } else {
    Serial.println("\nTime sync failed!");
  }
}

// ================= GET TIMESTAMP (HANYA WAKTU) =================
String getTimestamp() {
  time_t now;
  struct tm timeinfo;
  time(&now);
  localtime_r(&now, &timeinfo);
  
  char buffer[10];
  strftime(buffer, sizeof(buffer), "%H:%M:%S", &timeinfo);
  return String(buffer);
}

// ================= ADC AVG =================
int readAdcAvg(int pin, int samples, int dlyMs) {
  uint32_t sum = 0;
  for (int i = 0; i < samples; i++) {
    sum += analogRead(pin);
    delay(dlyMs);
  }
  return sum / samples;
}

// ================= TURBIDITY =================
float adcToNtu(int adc) {
  if (adc >= adcCal[0]) return ntuCal[0];
  if (adc <= adcCal[N_CAL - 1]) return 150.0f;

  for (int i = 0; i < N_CAL - 1; i++) {
    if (adc <= adcCal[i] && adc >= adcCal[i + 1]) {
      float t = (float)(adcCal[i] - adc) /
                (float)(adcCal[i] - adcCal[i + 1]);
      return ntuCal[i] + t * (ntuCal[i + 1] - ntuCal[i]);
    }
  }
  return ntuCal[N_CAL - 1];
}

// ================= pH =================
float readPH() {
  for (int i = 0; i < 10; i++) {
    buffer_arr[i] = analogRead(PIN_PH);
    delay(30);
  }

  for (int i = 0; i < 9; i++) {
    for (int j = i + 1; j < 10; j++) {
      if (buffer_arr[i] > buffer_arr[j]) {
        temp = buffer_arr[i];
        buffer_arr[i] = buffer_arr[j];
        buffer_arr[j] = temp;
      }
    }
  }

  avgval = 0;
  for (int i = 2; i < 8; i++) avgval += buffer_arr[i];

  float volt = (float)avgval * VREF / ADC_MAX / 6.0f;
  ph_act = -5.70f * volt + calibration_value;
  return ph_act;
}

// ================= TDS =================
float readTDS() {
  int adc = analogRead(PIN_TDS);
  float voltage = adc * (VREF / ADC_MAX);
  float tds = (133.42 * pow(voltage, 3)
              -255.86 * pow(voltage, 2)
              +857.39 * voltage) * 0.5;
  return max(tds, 0.0f);
}

// ================= LED & BUZZER =================
void handleStatus(const String& status) {
  digitalWrite(PIN_LED_HIJAU, LOW);
  digitalWrite(PIN_LED_BIRU, LOW);
  digitalWrite(PIN_LED_MERAH, LOW);
  digitalWrite(PIN_BUZZER, LOW);

  if (status == "Layak Minum") {
    digitalWrite(PIN_LED_HIJAU, HIGH);
  }
  else if (status == "Cukup Layak Minum") {
    digitalWrite(PIN_LED_BIRU, HIGH);
  }
  else if (status == "Tidak Layak Minum") {
    digitalWrite(PIN_LED_MERAH, HIGH);

    digitalWrite(PIN_BUZZER, HIGH);
    delay(200);
    digitalWrite(PIN_BUZZER, LOW);
    delay(800);
  }
}

// ================= FIREBASE SEND =================
void firebaseSetFloat(const String& path, float value) {
  if (!Firebase.RTDB.setFloat(&fbdo, path, value)) {
    Serial.println(fbdo.errorReason());
  }
}

void firebaseSetString(const String& path, const String& value) {
  if (!Firebase.RTDB.setString(&fbdo, path, value)) {
    Serial.println(fbdo.errorReason());
  }
}

// ================= SETUP =================
void setup() {
  Serial.begin(115200);
  Wire.begin();

  analogReadResolution(12);
  analogSetPinAttenuation(PIN_TURB, ADC_11db);
  analogSetPinAttenuation(PIN_PH, ADC_11db);
  analogSetPinAttenuation(PIN_TDS, ADC_11db);

  pinMode(PIN_LED_HIJAU, OUTPUT);
  pinMode(PIN_LED_BIRU, OUTPUT);
  pinMode(PIN_LED_MERAH, OUTPUT);
  pinMode(PIN_BUZZER, OUTPUT);

  Serial.println("Connecting to WiFi...");
  WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  Serial.println("\nWiFi Connected");

  // Sync waktu dari NTP server
  syncTime();

  config.api_key = API_KEY;
  config.database_url = DATABASE_URL;
  config.signer.test_mode = true;
  Firebase.begin(&config, &auth);
  Firebase.reconnectWiFi(true);

  Serial.println("Firebase Ready");
}

// ================= LOOP =================
void loop() {
  // Baca sensor
  float ntu = adcToNtu(readAdcAvg(PIN_TURB, TURB_SAMPLES, TURB_SAMPLE_DELAY_MS));
  float ph  = readPH();
  float tds = readTDS();

  // Dapatkan timestamp (hanya waktu)
  String timestamp = getTimestamp();

  // Kirim data ke Firebase
  firebaseSetFloat("/sensor/ntu", ntu);
  firebaseSetFloat("/sensor/ph", ph);
  firebaseSetFloat("/sensor/tds", tds);
  firebaseSetString("/sensor/timestamp", timestamp);

  // Print ke Serial Monitor
  Serial.println("====================");
  Serial.print("Time: ");
  Serial.println(timestamp);
  Serial.print("NTU: ");
  Serial.println(ntu);
  Serial.print("pH: ");
  Serial.println(ph);
  Serial.print("TDS: ");
  Serial.println(tds);

  // Baca status dari Firebase
  if (Firebase.RTDB.getString(&fbdo, "/sensor/status")) {
    String status = fbdo.stringData();
    Serial.print("Status: ");
    Serial.println(status);
    handleStatus(status);
  }

  delay(3000);
}