#pragma once

#include <Arduino.h>
#include <functional>

// - Types

/// @brief Sensors array type
/// @tparam N Number of sensors
template <size_t N>
using SensorsType = std::array<std::tuple<const char *, MQSensorClass, float>, N>; // - Name, Sensor, Position

/// @brief Sensors data type
/// @tparam N Number of sensors
template <size_t N>
using SensorsDataType = std::array<std::tuple<const char *, float, uint64_t>, N>; // - Name, Value, Timestamp

// - Functions


/// @brief Initialize sensors
/// @tparam N Number of sensors
/// @param sensors Sensor data
template <size_t N>
inline void initialize_sensors(SensorsType<N> &sensors)
{
    for (auto &[name, sensor, position] : sensors)
        sensor.initialize();
}

/// @brief Loop sensors
/// @tparam N Number of sensors
/// @param sensors Sensor data
template <size_t N>
inline void loop_sensors(SensorsType<N> &sensors)
{
    for (auto &[name, sensor, position] : sensors)
        sensor.loop();
}

/// @brief Read sensors data
/// @tparam N Number of sensors
/// @param sensors Sensor data
/// @param data Data
/// @param get_unix_timestamp Function to get the current timestamp in milliseconds
/// @return True if the operation was successful, false otherwise
template <size_t N>
inline bool read_sensors(SensorsType<N> &sensors, SensorsDataType<N> &data, std::function<bool(uint64_t &)> get_unix_timestamp)
{
    // - Iterate over sensors
    for (size_t i = 0; i < N; i++)
    {
        // - Sensor acquisition
        auto &[name, sensor, position] = sensors[i];
        auto scaler = sensor.getScaler();
        auto average = scaler.getAverage();

        // - Timestamp
        uint64_t timestamp;
        if (!get_unix_timestamp(timestamp))
        {
            ESP_LOGE("Time", "Failed to get timestamp");
            return false;
        }

        data[i] = {name, average, timestamp};
    }

    return true;
}

/// @brief Get the values from the sensor data
/// @tparam N Number of sensors
/// @param data Sensor data
/// @return Values
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