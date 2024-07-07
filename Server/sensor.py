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
            self.a[gaz_sensors_type] = numpy.zeros((2, self.maximum_values))



        if self.index[gaz_sensors_type] >= self.a[gaz_sensors_type].shape[1]:
            return False

        self.a[gaz_sensors_type][:, self.index[gaz_sensors_type]] = numpy.array([timestamp, value])

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

        value = self.a[gaz_sensors_type][:, i - 1].copy()

        if center:
            value[1] -= self.a[gaz_sensors_type][1, :i].mean()

        return value

    def get_all_values(self, gaz_sensors_type, center=True):
        if gaz_sensors_type not in self.a:
            return None

        i = self.index[gaz_sensors_type]
        values_copy = self.a[gaz_sensors_type].copy()

        if center and i > 0:
            values_copy[1, :i] -= values_copy[1, :i].mean()
        

        return values_copy[:, :i]
        

    def __str__(self):
        return f"Sensor ({self.x}, {self.y}) :\n - Value {self.get_latest_values()}"