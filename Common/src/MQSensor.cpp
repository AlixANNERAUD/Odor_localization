#include "MQSensor.hpp"

#ifndef ADC_STEPS
#define ADC_STEPS 4096.0
#endif

MQSensorClass::MQSensorClass(int pin, unsigned int read_sample_interval)
    : read_sample_interval(read_sample_interval), pin(pin)
{}

void MQSensorClass::initialize()
{
    pinMode(pin, INPUT);
}

float MQSensorClass::read(unsigned int samples_count, unsigned int sample_interval)
{
    float samples = 0;
    for (int i = 0; i < samples_count; i++)
    {
        samples += this->getRawValue();
        delay(sample_interval);
    }
    return samples / samples_count;
}

float MQSensorClass::getNormalizedValue()
{
    return this->read(READ_SAMPLE_INTERVAL, READ_SAMPLE_INTERVAL) / ADC_STEPS;
}

unsigned int MQSensorClass::getRawValue()
{
    return analogRead(pin);
}

StandardScalerClass<float> MQSensorClass::getScaler()
{
    auto previous_scaler = this->scaler;

    this->scaler = StandardScalerClass<float>(); // Reset the scaler

    return previous_scaler;
}

void MQSensorClass::loop()
{
    // If the next read is due
    if (next_read < millis())
    {
        scaler.fit(this->getRawValue() / ADC_STEPS);

        next_read = millis() + this->read_sample_interval;
    }
}