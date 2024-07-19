#include "MQSensor.hpp"

#ifndef CALIBRATION_SAMPLE_COUNT
#define CALIBRATION_SAMPLE_COUNT 50
#endif

#ifndef CALIBRATION_SAMPLE_INTERVAL
#define CALIBRATION_SAMPLE_INTERVAL 100
#endif

#ifndef READ_SAMPLE_INTERVAL
#define READ_SAMPLE_INTERVAL 20
#endif

#ifndef READ_SAMPLE_TIMES
#define READ_SAMPLE_TIMES 5
#endif

#ifndef ADC_STEPS
#define ADC_STEPS 4096.0
#endif

MQSensorClass::MQSensorClass(int pin) : pin(pin)
{
}

void MQSensorClass::initialize()
{
    this->calibration_value = this->getCalibrationValue();
}

float MQSensorClass::getCalibrationValue()
{
    return this->read(CALIBRATION_SAMPLE_COUNT, CALIBRATION_SAMPLE_INTERVAL);
}

float MQSensorClass::read(unsigned int samples_count, unsigned int sample_interval)
{
    float samples = 0;
    for (int i = 0; i < samples_count; i++)
    {
        samples += this->getNormalizedValue();
        delay(sample_interval);
    }
    return samples / samples_count;
}

float MQSensorClass::getNormalizedValue()
{
    return this->read(READ_SAMPLE_INTERVAL, READ_SAMPLE_INTERVAL);
}

unsigned int MQSensorClass::getRawValue()
{
    return analogRead(pin);
}
