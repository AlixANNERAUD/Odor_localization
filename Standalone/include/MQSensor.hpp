#pragma once

#include <Arduino.h>

class CalibrationCurveClass
{
public:
    CalibrationCurveClass(float x, float y, float slope);

    float getPercentage(float rs_ro_ratio) const;

private:
    float x, y, slope;
};

class MQSensorClass
{
public:
    MQSensorClass(int pin, float R_L = 5.0, float R0_clean_air_factor = 9.83);

    void initialize();

    float getGasPercentage(const CalibrationCurveClass &calibration_curve);
    unsigned int rawValue();

private:
    int pin;
    float R_L, Ro;
    bool initialized = false;

    float resistanceCalculation(unsigned int raw_value);
    float getCalibrationValue(float R0_clean_air_factor);
    float read(unsigned int num_samples, unsigned int sample_interval);
};