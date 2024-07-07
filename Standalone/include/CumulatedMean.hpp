#include <cmath>

class CumulatedMeanStdClass
{
private:
    float currentAverage = 0.0;
    float sumSquareDifferences = 0.0;
    int count = 0;

public:
    inline void addValue(float value)
    {
        count++;
        float previousAverage = currentAverage;
        this->currentAverage += (value - currentAverage) / count;
        this->sumSquareDifferences += (value - previousAverage) * (value - currentAverage);
    }

    inline float getAverage() const
    {
        return currentAverage;
    }

    inline float getStd() const
    {
        return std::sqrt(sumSquareDifferences / count);
    }

    inline int getCount() const
    {
        return count;
    }

    inline float centerValue(float value) const
    {
        return value - currentAverage;
    }

    inline float normalizeValue(float value) const
    {
        return centerValue(value) /
               getStd();
    }
};
