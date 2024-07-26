#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include "MQSensor.hpp"
#include <array>
#include <tuple>

#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

template <size_t N>
using SensorsType = std::array<std::tuple<const char *, MQSensorClass>, N>;

template <size_t N>
using SensorsDataType = std::array<std::tuple<const char *, float, uint64_t>, N>;

void printf_on_display(Adafruit_SSD1306 &display, const char *format, ...)
{
  char buffer[512];
  va_list args;
  va_start(args, format);
  vsnprintf(buffer, sizeof(buffer), format, args);
  va_end(args);

  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(WHITE);
  display.setCursor(0, 0);

  display.println("Sniffer project");

  display.print(buffer);

  display.display();
}

bool setup_wifi(Adafruit_SSD1306 &display, const char *wifi_ssid, const char *wifi_password)
{
  printf_on_display(display, "Connecting to %s ...", wifi_ssid);

  ESP_LOGI("WiFi", "Connecting to %s ...", wifi_ssid);

  WiFi.begin(wifi_ssid, wifi_password);
  WiFi.setTxPower(WIFI_POWER_8_5dBm);

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

template <size_t N>
bool publish_sensor_data(PubSubClient &client, const SensorsDataType<N> &data, JsonDocument &document, String &buffer, const char *topic, const char *client_name)
{
  // - Sensor acquisition
  for (const auto &[name, value, timestamp] : data)
  {
    document["data"][name]["value"] = value;
    document["data"][name]["timestamp"] = timestamp;
  }

  // - Serialize JSON
  document.shrinkToFit();

  serializeJson(document, buffer);

  // - Publish
  return client.publish(topic, buffer.c_str());
}

bool setup_display(Adafruit_SSD1306 &display, unsigned int sda_pin, unsigned int scl_pin)
{
  if (!Wire.begin(sda_pin, scl_pin))
    return false;

  if (!display.begin(SSD1306_SWITCHCAPVCC, DEFAULT_LCD_ADDRESS))
    return false;

  return true;
}

SensorsType<2> sensors = {{{"MQ3", MQSensorClass(DEFAULT_MQ135_PIN)},
                           {"MQ136", MQSensorClass(DEFAULT_MQ3_PIN)}}};

template <size_t N>
void initialize_sensors(SensorsType<N> &sensors)
{
  for (auto &[name, sensor] : sensors)
  {
    sensor.initialize();
  }
}

template <size_t N>
bool read_sensors(SensorsType<N> &sensors, SensorsDataType<N> &data)
{

  for (size_t i = 0; i < N; i++)
  {
    // - Sensor acquisition
    auto &[name, sensor] = sensors[i];
    float percentage = sensor.getNormalizedValue();

    // - Timestamp
    uint64_t timestamp;
    if (!get_unix_timestamp(timestamp))
    {
      ESP_LOGE("Time", "Failed to get timestamp");
      return false;
    }

    data[i] = {name, percentage, timestamp};
  }

  return true;
}

Adafruit_SSD1306 display(DISPLAY_WIDTH, DISPLAY_HEIGHT, &Wire, -1);

void setup()
{
  ESP_LOGI("Display", "Initialize...");

  // - Liquid crystal display
  if (!setup_display(display, DEFAULT_LCD_SDA_PIN, DEFAULT_LCD_SCL_PIN))
    ESP_LOGE("Display", "Initialisation failed.");

  // - Sensor
  ESP_LOGI("MQ", "Initialize ...");
  printf_on_display(display, "Initialize sensors");

  initialize_sensors(sensors);
}

WiFiClient wifi_client;
PubSubClient client(wifi_client);
JsonDocument document;
String buffer;

void loop()
{
  document["sensor"] = DEFAULT_CLIENT_NAME;

  while (WiFi.status() != WL_CONNECTED)
  {
    printf_on_display(display, "Connecting to WiFi ...");
    if (!setup_wifi(display, DEFAULT_WIFI_SSID, DEFAULT_WIFI_PASSWORD))
    {
      printf_on_display(display, "Failed to connect to WiFi, retrying in 5 seconds");
      ESP_LOGE("WiFi", "Failed to connect to WiFi, retrying in 5 seconds");
      delay(5000);
    }
    else
      configTime(0, 0, "pool.ntp.org");
  }

  while (!client.connected())
    reconnect_mqtt_client(client, DEFAULT_MQTT_BROKER, DEFAULT_CLIENT_NAME, DEFAULT_MQTT_PORT);

  SensorsDataType<2> data;

  if (!read_sensors(sensors, data))
  {
    ESP_LOGE("MQ", "Failed to read sensor data");
    return;
  }

  printf_on_display(display, "MQ3: %.2f\nMQ136: %.2f", std::get<1>(data[0]), std::get<1>(data[1]));

  if (publish_sensor_data(client, data, document, buffer, DEFAULT_MQTT_TOPIC, DEFAULT_CLIENT_NAME))
  {
    for (const auto &[name, value, timestamp] : data)
      ESP_LOGV("MQTT", "Sensor: %s, Value: %.2f, Timestamp: %llu", name, value, timestamp);
  }

  else
    ESP_LOGE("MQTT", "Failed to publish sensor data");

  delay(DEFAULT_SEND_INTERVAL);
}