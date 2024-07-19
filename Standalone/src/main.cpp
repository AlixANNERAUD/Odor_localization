#include <Arduino.h>
#include "MQSensor.hpp"
#include "CumulatedMean.hpp"

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

const CalibrationCurveClass LPG(2.3, 0.21, -0.47);
const CalibrationCurveClass CO(2.3, 0.72, -0.34);
const CalibrationCurveClass Smoke(2.3, 0.53, -0.44);

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

float get_gaz_direction(float sensor_1, float sensor_2, float sensor_distance)
{
  float difference = sensor_1 - sensor_2;

  if (difference == 0)
    return 90;

  return atan(difference / sensor_distance);
}

float radians_to_degrees(float radians)
{
  return radians * 180 / PI;
}

MQSensorClass mq3_1(DEFAULT_MQ3_1_PIN, 5.0, 9.83);
MQSensorClass mq3_2(DEFAULT_MQ3_2_PIN, 5.0, 9.83);
CumulatedMeanStdClass cumulated_mean_mq3_1;
CumulatedMeanStdClass cumulated_mean_mq3_2;
CumulatedMeanStdClass cumulated_mean_common;

#ifdef LCD_ENABLED
Adafruit_SSD1306 display(DISPLAY_WIDTH, DISPLAY_HEIGHT, &Wire, -1);
#endif

void setup()
{
  ESP_LOGI("LCD", "Starting setup");

#ifdef LCD_ENABLED
  // - Liquid crystal display
  if (setup_lcd(display, DEFAULT_LCD_SDA_PIN, DEFAULT_LCD_SCL_PIN))
    ESP_LOGE("LCD", "LCD initialized");
#endif

  ESP_LOGI("MQ3", "Starting setup");
  // - Sensor
  mq3_1.initialize();
  mq3_2.initialize();
}

float mq3_1_values[] = {0.0, 0.0};
float mq3_2_values[] = {0.0, 0.0};
float direction_values[] = {0.0, 0.0};

void loop()
{
#ifdef LCD_ENABLED

  mq3_1_values[0] = mq3_1_values[1];
  mq3_2_values[0] = mq3_2_values[1];

  mq3_1_values[1] = mq3_1.getGasPercentage(LPG);
  mq3_2_values[1] = mq3_2.getGasPercentage(LPG);

  cumulated_mean_mq3_1.addValue(mq3_1_values[1]);
  cumulated_mean_mq3_2.addValue(mq3_2_values[1]);
  cumulated_mean_common.addValue((mq3_1_values[1] + mq3_2_values[1]) / 2);

  auto centered_mq3_1 = cumulated_mean_common.centerValue(mq3_1_values[1]);
  auto centered_mq3_2 = cumulated_mean_common.centerValue(mq3_2_values[1]);

  auto normalized_mq3_1 = cumulated_mean_common.normalizeValue(mq3_1_values[1]);
  auto normalized_mq3_2 = cumulated_mean_common.normalizeValue(mq3_2_values[1]);

  auto direction_raw = get_gaz_direction(mq3_1_values[1], mq3_2_values[1], SENSOR_DISTANCE);
  auto direction_centered = get_gaz_direction(centered_mq3_1, centered_mq3_2, SENSOR_DISTANCE);
  auto direction_normalized = get_gaz_direction(normalized_mq3_1, normalized_mq3_2, SENSOR_DISTANCE);

  float growth_rates[] = {mq3_1_values[1] - mq3_1_values[0], mq3_2_values[1] - mq3_2_values[0]};

  direction_values[0] = direction_values[1];

  direction_values[1] = direction_centered;

  ESP_LOGI("MQ3", "MQ3 1: %f, MQ3 2: %f, Direction: %f", mq3_1_values[1], mq3_2_values[1], radians_to_degrees(direction_raw));

  ESP_LOGI("MQ3", "C MQ3 1: %f, C MQ3 2: %f,C  Direction: %f", centered_mq3_1, centered_mq3_2, radians_to_degrees(direction_centered));

  ESP_LOGI("MQ3", "N MQ3 1: %f, N MQ3 2: %f,N  Direction: %f", normalized_mq3_1, normalized_mq3_2, radians_to_degrees(direction_normalized));

  ESP_LOGI("MQ3", "G MQ3 1: %f, G MQ3 2: %f, Diff : %f", growth_rates[0], growth_rates[1], growth_rates[0] - growth_rates[1]);

  ESP_LOGI("MQ3", "Direction growth : %f", radians_to_degrees(direction_centered - direction_values[0]));

  ESP_LOGI("MQ3", "-------------------");

  display.clearDisplay();
  display.setTextSize(1);
  display.setTextColor(WHITE);
  display.setCursor(0, 0);

  display.println("Sniffer project");

  display.print("MQ3 : ");
  display.print(mq3_1_values[1]);
  display.print(" - ");
  display.println(mq3_2_values[1]);

  display.print("Direction : ");
  display.println(radians_to_degrees(direction_values[1]));

  display.print("Growth rate : ");
  display.println(radians_to_degrees(direction_values[1]) - radians_to_degrees(direction_values[0]));

  display.display();
#endif
}