#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include "MQSensor.hpp"
#include <ArduinoJson.h>

bool setup_wifi(const char *wifi_ssid, const char *wifi_password)
{
  WiFi.mode(WIFI_STA);
  WiFi.disconnect();

  delay(1000);

  ESP_LOGI("WiFi", "Connecting to %s ...", wifi_ssid);

  WiFi.begin(wifi_ssid, wifi_password);

  while (WiFi.status() != WL_CONNECTED)
  {
    if (WiFi.status() == WL_CONNECT_FAILED)
      return false;

    delay(1000);
  }
  ESP_LOGI("WiFi", "WiFi connected with IP: %s\n", WiFi.localIP().toString().c_str());
  return true;
}

void reconnect_mqtt_client(PubSubClient &client, const char *mqtt_broker, const char *client_name, uint16_t mqtt_port)
{
  client.setServer(mqtt_broker, mqtt_port);

  ESP_LOGI("MQTT", "Attempting connection to %s:%d", mqtt_broker, mqtt_port);

  while (!client.connected())
  {
    if (client.connect(client_name))
    {
      ESP_LOGI("MQTT", "connected !");
    }
    else
    {
      ESP_LOGE("MQTT", "Connection failed, rc=%d, try again in 5 seconds\n", client.state());
      delay(5000);
    }
  }
}

bool get_unix_timestamp(unsigned long &timestamp)
{
  time_t now;
  struct tm timeinfo;
  if (!getLocalTime(&timeinfo))
  {
    return false;
  }
  time(&now);
  timestamp = now;
  return true;
}

CalibrationCurveClass LPG(2.3, 0.21, -0.47);
CalibrationCurveClass CO(2.3, 0.72, -0.34);
CalibrationCurveClass Smoke(2.3, 0.53, -0.44);

bool publish_sensor_data(PubSubClient &client, MQSensorClass &sensor, JsonDocument &document, String &buffer, char *topic, const char *client_name)
{
  float sensorValue = sensor.getGasPercentage(LPG);

  document["data"] = sensorValue;

  // - Timestamp

  unsigned long timestamp;

  if (!get_unix_timestamp(timestamp))
  {
    ESP_LOGE("MQTT", "Failed to get timestamp");
    return false;
  }

  document["timestamp"] = timestamp;

  // - Serialize JSON
  document.shrinkToFit();

  serializeJson(document, buffer);

  ESP_LOGI("MQTT", "Publishing sensor data: %s\n", buffer.c_str());
  return client.publish(topic, buffer.c_str());
}

void setup()
{
  // - WiFi
  while (!setup_wifi(DEFAULT_WIFI_SSID, DEFAULT_WIFI_PASSWORD))
  {
    ESP_LOGI("WiFi", "Failed to connect to WiFi, retrying in 5 seconds");
    delay(5000);
  }

  // - Time (NTP)
  configTime(0, 0, "pool.ntp.org");

  // - Sensor
  sensor.initialize();
}

MQSensorClass sensor(DEFAULT_SENSOR_PIN, 5.0, 9.83);
WiFiClient wifi_client;
PubSubClient client(wifi_client);
JsonDocument document;
String buffer;

void loop()
{
  document["sensor"] = DEFAULT_CLIENT_NAME;

  if (!client.connected())
  {
    reconnect_mqtt_client(client, DEFAULT_MQTT_BROKER, DEFAULT_CLIENT_NAME, DEFAULT_MQTT_PORT);
  }

  int sensorValue = analogRead(DEFAULT_SENSOR_PIN);

  if (publish_sensor_data(client, sensor, document, buffer, DEFAULT_MQTT_TOPIC, DEFAULT_CLIENT_NAME))
  {
    ESP_LOGI("MQTT",
             "Published sensor data: %d\n",
             sensorValue);
  }
  else
  {
    ESP_LOGI("MQTT", "Failed to publish sensor data");
  }

  delay(100);
}