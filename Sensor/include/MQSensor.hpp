#pragma once

#include <Arduino.h>

class MQSensorClass
{
public:
    MQSensorClass(int pin);

    void initialize();

    float getNormalizedValue();
    unsigned int getRawValue();
    float getCalibrationValue();
    float read(unsigned int num_samples, unsigned int sample_interval);

private:
    int pin;
    float calibration_value;
    bool initialized = false;
};