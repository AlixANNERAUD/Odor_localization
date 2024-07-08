#include "MQSensor.hpp"

#ifndef CALIBRATION_SAMPLE_TIMES
#define CALIBRATION_SAMPLE_TIMES 50
#endif

#ifndef CALIBRATION_SAMPLE_INTERVAL
#define CALIBRATION_SAMPLE_INTERVAL 20
#endif

#ifndef READ_SAMPLE_INTERVAL
#define READ_SAMPLE_INTERVAL 20
#endif

#ifndef READ_SAMPLE_TIMES
#define READ_SAMPLE_TIMES 5
#endif

CalibrationCurveClass::CalibrationCurveClass(float x, float y, float slope) : x(x), y(y), slope(slope)
{
}

float CalibrationCurveClass::getPercentage(float rs_ro_ratio) const
{
    return (pow(10, ((log(rs_ro_ratio) - this->y) / this->slope) + this->x));
    //return ((log(rs_ro_ratio) - this->y) / this->slope) + this->x;
}

MQSensorClass::MQSensorClass(int pin, float R_L, float R0_clean_air_factor) : pin(pin), R_L(R_L), Ro(R0_clean_air_factor)
{
}

void MQSensorClass::initialize()
{
    if (this->initialized)
        return;

    pinMode(pin, INPUT);

    this->Ro = this->getCalibrationValue(this->Ro);

    this->initialized = true;
}

float MQSensorClass::resistanceCalculation(unsigned int raw_value)
{
    return (this->R_L * (4095 - raw_value) / raw_value);
}

float MQSensorClass::getCalibrationValue(float R0_clean_air_factor)
{
    return this->read(CALIBRATION_SAMPLE_TIMES, CALIBRATION_SAMPLE_INTERVAL) / R0_clean_air_factor;
}

float MQSensorClass::read(unsigned int samples_count, unsigned int sample_interval)
{
    float samples = 0;
    for (int i = 0; i < samples_count; i++)
    {
        samples += this->resistanceCalculation(analogRead(pin));
        delay(sample_interval);
    }
    return samples / samples_count;
}

unsigned int MQSensorClass::rawValue()
{
    return analogRead(pin);
}

float MQSensorClass::getGasPercentage(const CalibrationCurveClass &calibration_curve)
{
    float rs_ro_ratio = read(READ_SAMPLE_TIMES, READ_SAMPLE_INTERVAL) / this->Ro;
    return calibration_curve.getPercentage(rs_ro_ratio);
}