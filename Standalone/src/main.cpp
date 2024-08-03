#include <Arduino.h>
#include "MQSensor.hpp"
#include "StandardScaler.hpp"
#include "Sensors.hpp"

#if defined(DEFAULT_LCD_ADDRESS) || defined(DEFAULT_LCD_SDA_PIN) || defined(DEFAULT_LCD_SCL_PIN)
#if !(defined(DEFAULT_LCD_ADDRESS) && defined(DEFAULT_LCD_SDA_PIN) && defined(DEFAULT_LCD_SCL_PIN))
#error "You must define all or none of the following: DEFAULT_LCD_ADDRESS, DEFAULT_LCD_SDA_PIN, DEFAULT_LCD_SCL_PIN"
#else
#define LCD_ENABLED
#endif
#endif

#ifdef LCD_ENABLED
#include <Wire.h>
#include <Adafruit_GFX.h>
#include <Adafruit_SSD1306.h>
#endif

#ifdef LCD_ENABLED

bool setup_lcd(Adafruit_SSD1306 &display, unsigned int sda_pin, unsigned int scl_pin)
{
  if (!Wire.begin(sda_pin, scl_pin))
    return false;

  if (!display.begin(SSD1306_SWITCHCAPVCC, DEFAULT_LCD_ADDRESS))
    return false;

  return true;
}
#endif

template <size_t N>
float get_gaz_direction(const SensorsDataType<N> &data)
{
  float gradient_position_sum = 0;
  float gradient_sum = 0;

  for (const auto &[name, position, value] : data)
  {
    gradient_position_sum += position * value;
    gradient_sum += value;
  }

  return gradient_position_sum / gradient_sum;
}

SensorsType<2> sensors = {{{"MQ3 L", MQSensorClass(DEFAULT_MQ3_1_PIN), 1},
                           {
                               "MQ3 R",
                               MQSensorClass(DEFAULT_MQ3_2_PIN),
                               -1,
                           }}};

std::array<StandardScalerClass<float>, 2> scalers;

StandardScalerClass<float> global_scaler;

#ifdef LCD_ENABLED
Adafruit_SSD1306 display(DISPLAY_WIDTH, DISPLAY_HEIGHT, &Wire, -1);
#endif

void setup()
{
  ESP_LOGI("LCD", "Starting !setup");

#ifdef LCD_ENABLED
  // - Liquid crystal display
  if (setup_lcd(display, DEFAULT_LCD_SDA_PIN, DEFAULT_LCD_SCL_PIN))
    ESP_LOGE("LCD", "LCD initialized");
#endif

  ESP_LOGI("MQ3", "Starting setup");
  // - Sensor
  initialize_sensors(sensors);
}

void loop()
{
  SensorsDataType<2> sensors_data;

  auto time_lambda = [](uint64_t &timestamp) -> bool
  {
    timestamp = 0; // Just don't care about the timestamp
    return true;
  };

  if (!read_sensors(sensors, sensors_data, time_lambda))
  {
    ESP_LOGE("MQ3", "Failed to read sensors");
    return;
  }

  auto raw_values = get_values(sensors_data);

  auto normalized_values = fit_transform(scalers, raw_values);
  auto centered_values = fit_transform(scalers, raw_values, true);

  for (auto value : raw_values)
    global_scaler.fit(value);

  auto direction = get_gaz_direction(sensors_data);

  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(WHITE);
  display.setCursor(0, 0);

  display.println("Sniffer project");

  for (size_t i = 0; i < 2; i++)
  {

    display.print(std::get<0>(sensors[i]));
    display.print(" : ");
    display.println(raw_values[i]);
  }

  display.print("Direction : ");
  display.println(direction);

  display.display();
}