#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <LiquidCrystal_I2C.h>
#include <Wire.h>
#include "MQSensor.hpp"

bool setup_wifi(const char *wifi_ssid, const char *wifi_password)
{
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

bool get_unix_timestamp(uint64_t &timestamp)
{
  struct tm timeinfo;
  if (!getLocalTime(&timeinfo))
    return false;

  struct timeval now;
  gettimeofday(&now, NULL);
  timestamp = (now.tv_sec * 1000) + now.tv_usec / 1000;
  return true;
}

const CalibrationCurveClass LPG(2.3, 0.21, -0.47);
const CalibrationCurveClass CO(2.3, 0.72, -0.34);
const CalibrationCurveClass Smoke(2.3, 0.53, -0.44);

bool publish_sensor_data(PubSubClient &client, MQSensorClass &mq3, MQSensorClass &mq136, JsonDocument &document, String &buffer, const char *topic, const char *client_name)
{
  // - Sensor acquisition
  document["data"]["MQ136"] = mq136.getGasPercentage(LPG);
  document["data"]["MQ3"] = mq3.getGasPercentage(LPG);

  // - Timestamp

  uint64_t timestamp;

  if (!get_unix_timestamp(timestamp))
  {
    ESP_LOGE("MQTT", "Failed to get timestamp");
    return false;
  }

  document["timestamp"] = timestamp;

  // - Serialize JSON
  document.shrinkToFit();

  serializeJson(document, buffer);

  // - Publish
  return client.publish(topic, buffer.c_str());
}

bool setup_lcd(LiquidCrystal_I2C &lcd, unsigned int sda_pin, unsigned int scl_pin)
{
  if (!Wire.begin(sda_pin, scl_pin))
    return false;

  lcd.init();
  lcd.backlight();

  return true;
}

MQSensorClass mq136(DEFAULT_MQ135_PIN, 5.0, 9.83);
MQSensorClass mq3(DEFAULT_MQ3_PIN, 5.0, 9.83);
LiquidCrystal_I2C lcd(DEFAULT_LCD_ADDRESS, 20, 4);

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

  // - Liquid crystal display
  setup_lcd(lcd, DEFAULT_LCD_SDA_PIN, DEFAULT_LCD_SCL_PIN);

  // - Sensor
  mq3.initialize();
  mq136.initialize();
}

WiFiClient wifi_client;
PubSubClient client(wifi_client);
JsonDocument document;
String buffer;


void loop()
{
  document["sensor"] = DEFAULT_CLIENT_NAME;

  if (!client.connected())
    reconnect_mqtt_client(client, DEFAULT_MQTT_BROKER, DEFAULT_CLIENT_NAME, DEFAULT_MQTT_PORT);

  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Sniffer project");

  lcd.setCursor(0,2);
  lcd.print("MQ136 ");
  lcd.print(mq136.getGasPercentage(LPG));

  lcd.setCursor(0,3);
  lcd.print("MQ3 ");
  lcd.print(mq3.getGasPercentage(LPG));
  

  if (publish_sensor_data(client, mq3, mq136, document, buffer, DEFAULT_MQTT_TOPIC, DEFAULT_CLIENT_NAME))
    ESP_LOGV("MQTT",
             "Published sensor data: %d\n",
             sensorValue);
  else
    ESP_LOGI("MQTT", "Failed to publish sensor data");

  delay(100);
}