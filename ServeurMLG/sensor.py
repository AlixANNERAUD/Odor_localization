import numpy

class SensorClass:
    
    def __init__(self,  maximum_values=1001):
        self.sensor = { }
        self.index = { }
        self.maximum_values = maximum_values
        for i in range(1, 1001):
            self.update("MQ3", 0.0001, 0)
            self.update("MQ136", 0.0001, 0)

    def update(self, gaz_sensors_type, value, timestamp):
        if gaz_sensors_type not in self.sensor:
            self.index[gaz_sensors_type] = 0
            self.sensor[gaz_sensors_type] = {}
            self.sensor[gaz_sensors_type]["timestamp"] = numpy.zeros(self.maximum_values, dtype=numpy.uint64)
            self.sensor[gaz_sensors_type]["value"] = numpy.zeros(self.maximum_values, dtype=float)
        self.sensor[gaz_sensors_type]["value"][self.index[gaz_sensors_type]] = value
        self.sensor[gaz_sensors_type]["timestamp"][self.index[gaz_sensors_type]] = timestamp
        self.index[gaz_sensors_type] += 1
        if self.index[gaz_sensors_type] >= self.maximum_values:
            self.index[gaz_sensors_type] -= 1
            self.sensor[gaz_sensors_type]["value"] = numpy.roll(self.sensor[gaz_sensors_type]["value"], -1)
            self.sensor[gaz_sensors_type]["timestamp"] = numpy.roll(self.sensor[gaz_sensors_type]["timestamp"], -1)
        return True
        

    def get_latest_values(self, gaz_sensors_type, center=True):
        if gaz_sensors_type not in self.sensor:
            return None

        i = self.index[gaz_sensors_type]
        
        if i == 0:
            return None

        value = self.sensor[gaz_sensors_type]["value"][i - 1].copy()
        timestamp = self.sensor[gaz_sensors_type]["timestamp"][i - 1].copy()

        return (timestamp, value)


    def get_all_values(self, gaz_sensors_type, center=True):
        if gaz_sensors_type not in self.sensor:
            return None

        i = self.index[gaz_sensors_type]
        if i == 0:
            return None
        
        return (self.sensor[gaz_sensors_type]["timestamp"][:i].copy(), self.sensor[gaz_sensors_type]["value"][:i].copy())
        

    def __str__(self):
        return f"Sensor: Value {self.get_latest_values()}"