#pragma once

#include <Arduino.h>
#include <functional>

// - Types

template <size_t N>
using SensorsType = std::array<std::tuple<const char *, MQSensorClass, float>, N>; // - Name, Sensor, Position

template <size_t N>
using SensorsDataType = std::array<std::tuple<const char *, float, uint64_t>, N>; // - Name, Value, Timestamp

// - Functions

template <size_t N>
inline void initialize_sensors(SensorsType<N> &sensors)
{
    for (auto &[name, sensor, position] : sensors)
    {
        sensor.initialize();
    }
}

template <size_t N>
inline bool read_sensors(SensorsType<N> &sensors, SensorsDataType<N> &data, std::function<bool(uint64_t &)> get_unix_timestamp)
{
    for (size_t i = 0; i < N; i++)
    {
        // - Sensor acquisition
        auto &[name, sensor, position] = sensors[i];
        float percentage = sensor.getNormalizedValue();

        // - Timestamp
        uint64_t timestamp;
        if (!get_unix_timestamp(timestamp))
        {
            ESP_LOGE("Time", "Failed to get timestamp");
            return false;
        }

        data[i] = {name, percentage, timestamp};
    }

    return true;
}

template <size_t N>
inline std::array<float, N> get_values(SensorsDataType<N> &data)
{
    std::array<float, N> values;
    for (size_t i = 0; i < N; i++)
    {
        values[i] = std::get<1>(data[i]);
    }
    return values;
}