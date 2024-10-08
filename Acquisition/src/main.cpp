#include <Arduino.h>
#include <WiFi.h>
#include <PubSubClient.h>
#include <ArduinoJson.h>
#include <Wire.h>
#include "MQSensor.hpp"
#include <array>
#include <tuple>
#include "Sensors.hpp"

#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>

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

  if (!display.begin(SSD1306_SWITCHCAPVCC, LCD_ADDRESS))
    return false;

  return true;
}

SensorsType<2> sensors = {{{"MQ3", MQSensorClass(MQ3_PIN, READ_SAMPLE_INTERVAL),
                            0},
                           {"MQ136", MQSensorClass(MQ135_PIN, READ_SAMPLE_INTERVAL),
                            0}}};

Adafruit_SSD1306 display(DISPLAY_WIDTH, DISPLAY_HEIGHT, &Wire, -1);

void setup()
{
  ESP_LOGI("Display", "Initialize...");

  // - Liquid crystal display
  if (!setup_display(display, LCD_SDA_PIN, LCD_SCL_PIN))
    ESP_LOGE("Display", "Initialisation failed.");

  // - Sensor
  ESP_LOGI("MQ", "Initialize ...");
  initialize_sensors(sensors);
  printf_on_display(display, "Initialize sensors");
}

WiFiClient wifi_client;
PubSubClient client(wifi_client);
JsonDocument document;
String buffer;
unsigned int next_publish = 0;

void loop()
{
  document["sensor"] = CLIENT_NAME;

  if (next_publish < millis())
  {
    ESP_LOGD("MQTT", "Publishing sensor data with a lag of %d ms", millis() - next_publish);

    if (next_publish == 0)
    {
      next_publish = millis() + PUBLISH_INTERVAL;
      return;
    }

    // - Check if the wifi is connected
    while (WiFi.status() != WL_CONNECTED)
    {
      printf_on_display(display, "Connecting to WiFi ...");
      if (!setup_wifi(display, WIFI_SSID, WIFI_PASSWORD))
      {
        printf_on_display(display, "Failed to connect to WiFi, retrying in 5 seconds");
        ESP_LOGE("WiFi", "Failed to connect to WiFi, retrying in 5 seconds");
        delay(5000);
      }
      else
        // - Set the time via NTP
        configTime(0, 0, "pool.ntp.org");
    }

    ESP_LOGD("MQTT", "Publishing sensor data with a lag of %d ms", millis() - next_publish);


    // - Check if the client is connected
    while (!client.connected())
      reconnect_mqtt_client(client, MQTT_BROKER, CLIENT_NAME, MQTT_PORT);

    ESP_LOGD("MQTT", "Co sensor data with a lag of %d ms", millis() - next_publish);


    // - Collect sensor data
    SensorsDataType<2> data;

    // - Read sensor data
    if (!read_sensors(sensors, data, get_unix_timestamp))
    {
      ESP_LOGE("MQ", "Failed to read sensor data");
      return;
    }

     ESP_LOGD("MQTT", "Reading sensor data with a lag of %d ms", millis() - next_publish);


    // - Print sensor data
    printf_on_display(display, "MQ3: %.6f\nMQ136: %.6f", std::get<1>(data[0]), std::get<1>(data[1]));

    // - Publish sensor data
    if (publish_sensor_data(client, data, document, buffer, MQTT_TOPIC, CLIENT_NAME))
    {
      for (const auto &[name, value, timestamp] : data)
        ESP_LOGV("MQTT", "Sensor: %s, Value: %.2f, Timestamp: %llu", name, value, timestamp);
    }
    else
      ESP_LOGE("MQTT", "Failed to publish sensor data");

    next_publish = millis() + PUBLISH_INTERVAL;
  }

  // - Loop sensors (collect data)
  loop_sensors(sensors);

  delay(5); // Let the CPU breathe alcohol
}