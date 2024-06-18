#include <Arduino.h>
#include "WiFi.h"
#include "PubSubClient.h"

void setup_wifi(const char *wifi_ssid, const char *wifi_password)
{
  WiFi.mode(WIFI_STA);
  WiFi.disconnect();

  delay(1000);

  Serial.printf("Connecting to %s ", wifi_ssid);
  Serial.flush();

  WiFi.begin(wifi_ssid, wifi_password);

  while (WiFi.status() != WL_CONNECTED)
  {
    delay(500);
    Serial.print(".");
    Serial.flush();
  }
  Serial.printf("WiFi connected with IP: %s\n", WiFi.localIP().toString().c_str());
}

void setup_mqtt_client(PubSubClient &client, const char *mqtt_broker, uint16_t mqtt_port)
{
  client.setServer(mqtt_broker, mqtt_port);
  
  String clientId = "ESP32Client-";

  while (!client.connected())
  {
    Serial.print("Attempting MQTT connection...");

    clientId += String(random(0xffff), HEX);
    
    if (client.connect(clientId.c_str()))
    {
      Serial.println("connected");
    }
    else
    {
      Serial.printf("failed, rc=%d, try again in 5 seconds\n", client.state());
      delay(5000);
    }
  }
}

bool publish_sensor_data(PubSubClient &client, unsigned int value)
{
  char payload[10];
  sprintf(payload, "%d", value);
  return client.publish(DEFAULT_MQTT_TOPIC, payload);
}

PubSubClient client;

void setup()
{
  // - Serial
  Serial.begin(115200);

  // - WiFi
  setup_wifi(DEFAULT_WIFI_SSID, DEFAULT_WIFI_PASSWORD);

  // - MQTT
  setup_mqtt_client(client, DEFAULT_MQTT_BROKER, DEFAULT_MQTT_PORT);

  // - Analog
  pinMode(DEFAULT_SENSOR_PIN, INPUT);
}

void loop()
{
  int sensorValue = analogRead(DEFAULT_SENSOR_PIN);

  if (publish_sensor_data(client, sensorValue))
  {
    Serial.printf("Published sensor data: %d\n", sensorValue);
  }
  else
  {
    Serial.println("Failed to publish sensor data");
  }
  

  delay(100);
}