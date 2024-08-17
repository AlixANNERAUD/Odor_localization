import numpy
import logging
import pandas

class MinimumMaximumScaler:
    def __init__(self, minimum, maximum):
        self.minimum = minimum
        self.maximum = maximum

    def scale(self, x):
        """
        Scale x from [minimum, maximum] to [0, 1]

        # Arguments

        - x (float or numpy.ndarray): value to scale

        # Returns

        - float or numpy.ndarray: scaled value
        """

        # Check if x is a numpy array and if it is in the range [minimum, maximum]
        if isinstance(x, numpy.ndarray):
            if max(x) > self.maximum:
                raise ValueError(f"Maximum value {max(x)} out of range for sensor")
                
            if min(x) < self.minimum:
                raise ValueError(f"Minimum value {min(x)} out of range for sensor")

        return (x - self.minimum) / (self.maximum - self.minimum)


class SensorClass:
    
    def __init__(self, x, y, maximum_values=10000):
        """
        Create a new sensor

        # Arguments
        - x (int): x position of the sensor
        - y (int): y position of the sensor
        - scaler (MinimumMaximumScaler): scaler
        - maximum_values (int): maximum number of values to store

        # Returns
        - SensorClass: new sensor    
        """

        self.x = x
        self.y = y

        self.a = {}
        self.index = {}
        self.scalers = {}

        self.maximum_values = maximum_values

    def add_gaz_sensors_type(self, name, minimum, maximum):
        """
        Add a new gaz sensor type

        # Arguments

        - name (str): name of the sensor
        - minimum (float): minimum value
        - maximum (float): maximum value
        """

        # Check if the sensor already has the name
        if name in self.a:
            raise ValueError(f"Sensor already has {name}")

        # Create a new dataframe for the sensor
        self.a[name] = pandas.DataFrame(numpy.zeros((self.maximum_values, 2)), columns=["time", "value"])
        # Set the index to 0
        self.index[name] = 0
        # Create a new scaler for the sensor
        self.scalers[name] = MinimumMaximumScaler(minimum, maximum)

        return self

    def update(self, gaz_sensors_type, value, timestamp):
        if gaz_sensors_type not in self.a:
            raise ValueError(f"Sensor does not have {gaz_sensors_type}")

        i = self.index[gaz_sensors_type]

        if i >= self.maximum_values:
            raise ValueError("Too many values for sensor")

        self.a[gaz_sensors_type].iloc[i] = [timestamp, value]

        self.index[gaz_sensors_type] += 1
        
    def get_position(self):
        return self.x, self.y

    def get_gaz_sensors_types(self):
        return list(self.a.keys())

    def scale(self, data, gaz_sensors_type=None):
        # If data is a dictionary, scale all values recursively
        if gaz_sensors_type is None:
            if not(isinstance(data, dict)):
                raise ValueError("Data must be a dictionary when gaz_sensors_type is None")

            return {name: self.scale(data[name], name) for name in data}

        return self.scalers[gaz_sensors_type].scale(data)

    def get_latest_values(self, gaz_sensors_type, scale=False):
        if gaz_sensors_type not in self.a:
            raise ValueError(f"Sensor does not have {gaz_sensors_type}")

        i = self.index[gaz_sensors_type]
        
        if i == 0:
            raise ValueError(f"No values for {gaz_sensors_type}")
        
        data = self.a[gaz_sensors_type].iloc[i - 1].copy()

        if scale:
            data = self.scale(data)

        return data

    def get_all_values(self, gaz_sensors_type=None, scale=False):
        """
        Get all values for a sensor

        # Arguments

        - gaz_sensors_type (str): gaz sensor type, None for all
        - scale (bool): scale values

        # Returns

        - pandas.DataFrame or dict: values
        """

        # If gaz_sensors_type is None, return all values (recursively to resize the data)
        if gaz_sensors_type is None:
            data = {name: self.get_all_values(name, scale) for name in self.a}
            return data

        if gaz_sensors_type not in self.a:
            raise ValueError(f"Sensor does not have {gaz_sensors_type}")

        # Get the index of the sensor
        i = self.index[gaz_sensors_type]

        # Create a sliced copy of the data (only the values before the index)
        data = self.a[gaz_sensors_type].iloc[:i].copy()

        # Scale the data if needed
        if scale:
            data = self.scale(data, gaz_sensors_type)

        return data
        
    def get_gradient(self, gaz_sensors_type):
        i = self.index[gaz_sensors_type]

        data = self.a[gaz_sensors_type].iloc[:i].copy()

        gradient_data = pandas.DataFrame({
            "time": data["time"],
            "value": numpy.gradient(data["value"], data["time"])
        })
        
        return gradient_data

    def __str__(self):
        return f"Sensor ({self.x}, {self.y}) :\n - Value {self.get_latest_values()}"