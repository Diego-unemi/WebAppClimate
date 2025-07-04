#include <WiFi.h>
#include <WebServer.h>
#include <ArduinoJson.h>
#include "DHT.h"
#include "MQ135.h"

// Configuración WiFi
char ssid[] = "HEY_GARCIA";
char pass[] = "Garcia2912";

// Definiciones para sensores
#define DHTPIN 16
#define DHTTYPE DHT11
#define MQ135_PIN 39
#define rzero 47.66
#define rload 0.98

// Inicialización de sensores
DHT dht(DHTPIN, DHTTYPE);
MQ135 gasSensor = MQ135(MQ135_PIN);

// Servidor web en puerto 80
WebServer server(80);

// Variables globales para almacenar lecturas
float humidity = 0;
float temperature = 0;
float co2_ppm = 0;
unsigned long lastReading = 0;
const unsigned long readingInterval = 2000; // 2 segundos

void setup() {
  Serial.begin(115200);
  delay(100);
  Serial.println("Inicializando sensores...");
  
  // Inicializar sensor DHT
  dht.begin();
  
  // Conectar a WiFi
  WiFi.begin(ssid, pass);
  Serial.print("Conectando a WiFi");
  
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
  }
  
  Serial.println();
  Serial.println("WiFi conectado!");
  Serial.print("Dirección IP: ");
  Serial.println(WiFi.localIP());
  
  // Configurar rutas del servidor
  server.on("/", handleRoot);
  server.on("/data", handleData);
  server.enableCORS(true); // Habilitar CORS para peticiones desde Flask
  
  // Iniciar servidor
  server.begin();
  Serial.println("Servidor HTTP iniciado");
}

void loop() {
  server.handleClient();
  
  // Leer sensores cada 2 segundos
  if (millis() - lastReading >= readingInterval) {
    readSensors();
    lastReading = millis();
  }
}

void readSensors() {
  humidity = dht.readHumidity();
  temperature = dht.readTemperature();
  
  if (!isnan(humidity) && !isnan(temperature)) {
    co2_ppm = gasSensor.getCorrectedPPM(temperature, humidity);
    
    Serial.print("Humidity: ");
    Serial.print(humidity);
    Serial.print("% Temperature: ");
    Serial.print(temperature);
    Serial.print("°C CO2: ");
    Serial.print(co2_ppm);
    Serial.println(" ppm");
  } else {
    Serial.println("Error leyendo sensor DHT");
  }
}

void handleRoot() {
  String html = "<!DOCTYPE html><html><head><title>ESP32 Sensor Status</title></head>";
  html += "<body><h1>ESP32 Sensor Data</h1>";
  html += "<p>Temperature: " + String(temperature) + "°C</p>";
  html += "<p>Humidity: " + String(humidity) + "%</p>";
  html += "<p>CO2: " + String(co2_ppm) + " ppm</p>";
  html += "<p><a href='/data'>Get JSON Data</a></p></body></html>";
  
  server.send(200, "text/html", html);
}

void handleData() {
  // Crear objeto JSON con los datos de los sensores
  StaticJsonDocument<200> doc;
  doc["temperature"] = temperature;
  doc["humidity"] = humidity;
  doc["co2_ppm"] = co2_ppm;
  doc["timestamp"] = millis();
  doc["status"] = "ok";
  
  String response;
  serializeJson(doc, response);
  
  server.send(200, "application/json", response);
}