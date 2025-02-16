#include <HardwareSerial.h>
#include <TinyGPS++.h>

// Define the UART pins for GPS
#define GPS_RX 16  // ESP32 RX pin connected to GT-U7 TX
#define GPS_TX 17  // ESP32 TX pin connected to GT-U7 RX

// Create a TinyGPS++ object
TinyGPSPlus gps;

// Create a HardwareSerial object for GPS communication
HardwareSerial gpsSerial(1);

void setup() {
  // Start the Serial Monitor
  Serial.begin(115200);

  // Start the GPS serial connection
  gpsSerial.begin(9600, SERIAL_8N1, GPS_RX, GPS_TX);

  Serial.println("GT-U7 GPS Module Test");
}

void loop() {
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