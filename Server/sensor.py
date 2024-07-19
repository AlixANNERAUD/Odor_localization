import numpy

class SensorClass:
    
    def __init__(self, x, y, maximum_values=10000):
        self.x = x
        self.y = y

        self.a = { }
        self.index = { }

        self.maximum_values = maximum_values

    def update(self, gaz_sensors_type, value, timestamp):
        if gaz_sensors_type not in self.a:
            self.index[gaz_sensors_type] = 0
            self.a[gaz_sensors_type] = {}
            self.a[gaz_sensors_type]["timestamp"] = numpy.zeros(self.maximum_values, dtype=numpy.uint64)
            self.a[gaz_sensors_type]["value"] = numpy.zeros(self.maximum_values, dtype=float)
            self.a[gaz_sensors_type]["range"] = numpy.zeros(2, dtype=float)
            self.a[gaz_sensors_type]["range"][0] = value
            self.a[gaz_sensors_type]["range"][1] = value

        if self.index[gaz_sensors_type] >= self.maximum_values:
            return False

        self.a[gaz_sensors_type]["timestamp"][self.index[gaz_sensors_type]] = timestamp
        self.a[gaz_sensors_type]["value"][self.index[gaz_sensors_type]] = value

        self.a[gaz_sensors_type]["range"][0] = min(self.a[gaz_sensors_type]["range"][0], value)
        self.a[gaz_sensors_type]["range"][1] = max(self.a[gaz_sensors_type]["range"][1], value)

        self.index[gaz_sensors_type] += 1

        return True
        
    def get_position(self):
        return self.x, self.y

    def get_gaz_sensors_types(self):
        return list(self.a.keys())

    def get_latest_values(self, gaz_sensors_type, center=True):
        if gaz_sensors_type not in self.a:
            return None

        i = self.index[gaz_sensors_type]
        
        if i == 0:
            return None

        value = self.a[gaz_sensors_type]["value"][i - 1].copy()
        timestamp = self.a[gaz_sensors_type]["timestamp"][i - 1].copy()

        if center:
            value -= self.a[gaz_sensors_type]["value"][:i].mean()

        value -= self.a[gaz_sensors_type]["range"][0]
        value /= self.a[gaz_sensors_type]["range"][1] - self.a[gaz_sensors_type]["range"][0]

        return (timestamp, value)

    def get_all_values(self, gaz_sensors_type, center=True):
        if gaz_sensors_type not in self.a:
            return None

        i = self.index[gaz_sensors_type]
        values_copy = self.a[gaz_sensors_type]["value"][:i].copy()

        #if center and i > 0:
        #    values_copy[:i] -= values_copy[:i].mean()
        
        if center:
            values_copy -= self.a[gaz_sensors_type]["range"][0]
            values_copy = values_copy / (self.a[gaz_sensors_type]["range"][1] - self.a[gaz_sensors_type]["range"][0])
            
        print(f"min : {self.a[gaz_sensors_type]['range'][0]} max : {self.a[gaz_sensors_type]['range'][1]}")
            

        return (self.a[gaz_sensors_type]["timestamp"][:i], values_copy)
        
    def get_growth_rate(self, gaz_sensors_type):
        if gaz_sensors_type not in self.a:
            return None

        i = self.index[gaz_sensors_type]
        
        if i < 2:
            return None

        growth_rates = numpy.zeros(i - 1, dtype=float)

        for j in range(1, i):
            growth_rates[j - 1] = (self.a[gaz_sensors_type]["value"][j] - self.a[gaz_sensors_type]["value"][j - 1]) / (self.a[gaz_sensors_type]["timestamp"][j] - self.a[gaz_sensors_type]["timestamp"][j - 1])

        return (self.a[gaz_sensors_type]["timestamp"][1:i], growth_rates)

    def __str__(self):
        return f"Sensor ({self.x}, {self.y}) :\n - Value {self.get_latest_values()}"