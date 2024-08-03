#pragma once

#include <cmath>
#include <array>

template <typename T>
class StandardScalerClass
{
private:
    T currentAverage = 0.0;
    T sumSquareDifferences = 0.0;
    size_t count = 0;

public:
    inline void fit(T value)
    {
        count++;
        auto previousAverage = currentAverage;
        this->currentAverage += (value - currentAverage) / count;
        this->sumSquareDifferences += (value - previousAverage) * (value - currentAverage);
    }

    inline T getAverage() const
    {
        return currentAverage;
    }

    inline T getStd() const
    {
        return std::sqrt(sumSquareDifferences / count);
    }

    inline size_t getCount() const
    {
        return count;
    }

    inline T transform(T value, bool reduce = false) const
    {
        if (reduce)
            return (value - currentAverage) / getStd();
        return value - currentAverage;
    }

    inline T fit_transform(T value, bool reduce = false)
    {
        fit(value);
        return transform(value, reduce);
    }
};

template <size_t N, typename T>
inline std::array<T, N> fit_transform(std::array<StandardScalerClass<T>, N> &scaler, std::array<T, N> values, bool reduce = false)
{
    for (size_t i = 0; i < N; i++)
        values[i] = scaler[i].fit_transform(values[i], reduce);

    return values;
}