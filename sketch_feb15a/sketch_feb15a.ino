#include <WiFi.h>
#include <PubSubClient.h>
#include <TinyGPS++.h>

//This is the gps stuff 
#define GPS_RX 16  // ESP32 RX pin connected to GT-U7 TX
#define GPS_TX 17  // ESP32 TX pin connected to GT-U7 RX
// Create a TinyGPS++ object
TinyGPSPlus gps;
// Create a HardwareSerial object for GPS communication
HardwareSerial gpsSerial(1);

// Wi-Fi Credentials
//#define WIFI_SSID "Treehacks-2025"
//#define WIFI_PASSWORD "treehacks2025!"
#define WIFI_SSID "Jones"
#define WIFI_PASSWORD "Pokemon@1234"

// MQTT Broker Details
#define MQTT_BROKER "broker.hivemq.com"  // Free MQTT Broker
#define MQTT_PORT 1883
#define MQTT_TOPIC "wander/commands"

// Wi-Fi & MQTT Clients
WiFiClient espClient;
PubSubClient client(espClient);

//This deifines the pins 
#define LIGHT 32
#define MOTOR 33

//Vars for the light blinking
bool alertActive = false;
unsigned long previousMillis = 0;
const long blinkInterval = 1000;
bool lightState = LOW;

// Function to connect to Wi-Fi
void connectWiFi() {

    Serial.print("Connecting to WiFi...");
    WiFi.begin(WIFI_SSID, WIFI_PASSWORD);
    
    while (WiFi.status() != WL_CONNECTED) {
        delay(1000);
        Serial.print(".");
    }
    
    Serial.println("\n✅ WiFi connected!");
}

// Function to connect to MQTT broker
void connectMQTT() {
    client.setServer(MQTT_BROKER, MQTT_PORT);
    client.setCallback(receiveCommand);

    Serial.print("Connecting to MQTT...");
    while (!client.connected()) {
        if (client.connect("ESP32_Wander_Client")) {
            Serial.println("\n✅ Connected to MQTT Broker!");
            client.subscribe(MQTT_TOPIC);
            analogWrite(LIGHT, 128);  // Subscribe to command topic
        } else {
            Serial.print(".");
            digitalWrite(LIGHT, LOW);
            delay(1000);
        }
    }
}

// Function to receive MQTT messages
void receiveCommand(char* topic, byte* payload, unsigned int length) {
    String command = "";
    for (int i = 0; i < length; i++) {
        command += (char)payload[i];
    }
    
    Serial.println("📥 Received command: " + command);
    
    if (command == "startup") {
        digitalWrite(LIGHT, HIGH);
        Serial.println("🚀 Starting setup...");
    } else if (command == "alert") {
        digitalWrite(MOTOR, HIGH);
        alertActive = true;
        Serial.println("⚠️ ALERT: Patient has left the geofence!");
    } else if (command == "safe") {
        alertActive = false;
        digitalWrite(MOTOR, LOW);
        digitalWrite(LIGHT, 128);
        Serial.println("✅ Patient has returned inside the geofence.");
    } else {
        Serial.println("❓ Unknown command: " + command);
    }
}

void setup() {
  
    Serial.begin(115200);
    connectWiFi();
    connectMQTT();

    pinMode(LIGHT, OUTPUT);
    pinMode(MOTOR, OUTPUT);

     // Start the GPS serial connection
    gpsSerial.begin(9600, SERIAL_8N1, GPS_RX, GPS_TX);
    Serial.println("GT-U7 GPS Module Test");
}

void loop() {
  
    client.loop();  // Keep MQTT connection alive

    // This makes the lights flash every 5 seconds
    if (alertActive) {
        unsigned long currentMillis = millis();
        if (currentMillis - previousMillis >= blinkInterval) {
            previousMillis = currentMillis;
            lightState = !lightState;
            digitalWrite(LIGHT, lightState);
        }
    }

     // Read data from the GPS module
    while (gpsSerial.available() > 0) {
      char c = gpsSerial.read();
      Serial.write(c); // Print raw GPS data to the Serial Monitor
      gps.encode(c);
    }
    // Print parsed GPS data if valid
    if (gps.location.isValid()) {
      Serial.print("Latitude: ");
      Serial.println(gps.location.lat(), 6);
      Serial.print("Longitude: ");
      Serial.println(gps.location.lng(), 6);
      Serial.print("Altitude: ");
      Serial.println(gps.altitude.meters());
    } else {
      Serial.println("Waiting for valid GPS data...");
    }
    Serial.print("Latitude: ");
    Serial.println(gps.location.lat(), 6);
    Serial.print("Longitude: ");
    Serial.println(gps.location.lng(), 6);
    Serial.print("Altitude: ");
    Serial.println(gps.altitude.meters());
    // Print the time and date
    if (gps.date.isValid() && gps.time.isValid()) {
      Serial.print("Date: ");
      Serial.print(gps.date.month());
      Serial.print("/");
      Serial.print(gps.date.day());
      Serial.print("/");
      Serial.println(gps.date.year());
      Serial.print("Time: ");
      Serial.print(gps.time.hour());
      Serial.print(":");
      Serial.print(gps.time.minute());
      Serial.print(":");
      Serial.println(gps.time.second());
    } else {
      Serial.println("Date and time not valid.");
    }
    // Print satellite information
    Serial.print("Satellites in view: ");
    Serial.println(gps.satellites.value());
    
    // Delay to avoid flooding the Serial Monitor
    delay(1000);
}
