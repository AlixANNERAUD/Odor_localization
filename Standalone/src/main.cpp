#include <Arduino.h>
#include <Wire.h>
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
#include <LiquidCrystal_I2C.h>
#endif

const CalibrationCurveClass LPG(2.3, 0.21, -0.47);
const CalibrationCurveClass CO(2.3, 0.72, -0.34);
const CalibrationCurveClass Smoke(2.3, 0.53, -0.44);

#ifdef LCD_ENABLED
bool setup_lcd(LiquidCrystal_I2C &lcd, unsigned int sda_pin, unsigned int scl_pin)
{
  if (!Wire.begin(sda_pin, scl_pin))
    return false;

  lcd.init();
  lcd.backlight();

  return true;
}
#endif

float get_gaz_direction(float sensor_1, float sensor_2, float sensor_distance)
{
  float difference = sensor_1 - sensor_2;

  if (difference == 0)
    return 90;

  return atan(abs(difference) / sensor_distance);
}

float radians_to_degrees(float radians)
{
  return radians * 180 / PI;
}

MQSensorClass mq3_2(DEFAULT_MQ3_2_PIN, 5.0, 9.83);
MQSensorClass mq3_1(DEFAULT_MQ3_1_PIN, 5.0, 9.83);
CumulatedMeanStdClass cumulated_mean_mq3_1;
CumulatedMeanStdClass cumulated_mean_mq3_2;

#ifdef LCD_ENABLED
LiquidCrystal_I2C lcd(DEFAULT_LCD_ADDRESS, 20, 4);
#endif

void setup()
{
  ESP_LOGI("LCD", "Starting setup");

#ifdef LCD_ENABLED
  // - Liquid crystal display
  setup_lcd(lcd, DEFAULT_LCD_SDA_PIN, DEFAULT_LCD_SCL_PIN);
#endif

  ESP_LOGI("MQ3", "Starting setup");
  // - Sensor
  mq3_1.initialize();
  mq3_2.initialize();
}

void loop()
{
#ifdef LCD_ENABLED
  auto mq3_1_value = mq3_1.getGasPercentage(LPG);
  auto mq3_2_value = mq3_2.getGasPercentage(LPG);

  cumulated_mean_mq3_1.addValue(mq3_1.getGasPercentage(LPG));
  cumulated_mean_mq3_2.addValue(mq3_2.getGasPercentage(LPG));

  auto centered_mq3_1 = cumulated_mean_mq3_1.centerValue(mq3_1_value);
  auto centered_mq3_2 = cumulated_mean_mq3_2.centerValue(mq3_2_value);

  auto normalized_mq3_1 = cumulated_mean_mq3_1.normalizeValue(mq3_1_value);
  auto normalized_mq3_2 = cumulated_mean_mq3_2.normalizeValue(mq3_2_value);

  auto direction_raw = get_gaz_direction(centered_mq3_1, centered_mq3_2, 1.0);
  auto direction_centered = get_gaz_direction(mq3_1_value, mq3_2_value, 1.0);

  auto direction = direction_raw;

  lcd.clear();
  lcd.setCursor(0, 0);
  lcd.print("Sniffer project");

  lcd.setCursor(0, 1);
  lcd.print("MQ3 1 : ");
  lcd.print(mq3_1.getGasPercentage(LPG));

  lcd.setCursor(0, 2);
  lcd.print("MQ3 2 : ");
  lcd.print(mq3_2.getGasPercentage(LPG));

  lcd.setCursor(0, 3);
  lcd.print("Direction : ");
  lcd.print(radians_to_degrees(direction));

#endif
  ESP_LOGI("Direction", "%f", radians_to_degrees(direction));
}