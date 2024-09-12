#pragma once

#include <Arduino.h>
#include "StandardScaler.hpp"

class MQSensorClass
{
public:
    MQSensorClass(int pin, unsigned int read_sample_interval);

    void initialize();

    float getNormalizedValue();
    unsigned int getRawValue();

    float read(unsigned int num_samples, unsigned int sample_interval);

    void loop();

    StandardScalerClass<float> getScaler();

private:

    int pin;
    bool initialized = false;

    StandardScalerClass<float> scaler;

    const unsigned int read_sample_interval;
    unsigned int next_read = 0;
};
