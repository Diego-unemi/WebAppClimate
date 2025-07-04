#include <WiFi.h>

// Reemplaza con tus propias credenciales de Wi-Fi
const char* ssid = "HEY_GARCIA";
const char* password = "Garcia2912";

void setup() {
  Serial.begin(115200);
  delay(100);

  WiFi.mode(WIFI_STA);
  WiFi.disconnect(); // Desconecta cualquier conexión anterior
  delay(100);

  Serial.println("Iniciando conexión a la red Wi-Fi...");
  Serial.print("SSID: ");
  Serial.println(ssid);

  WiFi.begin(ssid, password);

  int intentos = 0;
  while (WiFi.status() != WL_CONNECTED) {
    delay(500);
    Serial.print(".");
    intentos++;
    if (intentos > 20) { // Intenta conectar durante 10 segundos
      Serial.println("\nNo se pudo conectar a la red Wi-Fi.");
      // Imprime el código de estado para saber por qué falló
      printWifiStatus();
      return; // Detiene el intento de conexión
    }
  }

  Serial.println("\n¡Conexión Wi-Fi establecida!");
  Serial.print("Dirección IP asignada: ");
  Serial.println(WiFi.localIP());
}

void loop() {
  // Nada aquí por ahora
}

// Función para imprimir el estado de la conexión
void printWifiStatus() {
  Serial.print("Estado de la conexión: ");
  Serial.print(WiFi.status());
  Serial.print(" - ");
  switch (WiFi.status()) {
    case WL_NO_SSID_AVAIL:
      Serial.println("No se encontró el SSID.");
      break;
    case WL_CONNECT_FAILED:
      Serial.println("Fallo en la conexión.");
      break;
    case WL_CONNECTION_LOST:
      Serial.println("Conexión perdida.");
      break;
    case WL_DISCONNECTED:
      Serial.println("Desconectado.");
      break;
    case WL_IDLE_STATUS:
      Serial.println("Estado inactivo.");
      break;
    case WL_SCAN_COMPLETED:
      Serial.println("Escaneo completado.");
      break;
    default:
      Serial.println("Estado desconocido.");
      break;
  }
}