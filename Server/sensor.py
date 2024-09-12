import numpy
import logging
import pandas
from scipy.interpolate import interp1d
from scipy.fft import fft, ifft
from sklearn.preprocessing import StandardScaler
from sklearn.linear_model import LinearRegression

from scipy.signal import butter, sosfiltfilt

import configuration

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

def get_shift(signal1, timestamps1, signal2, timestamps2):
    """
    Calculate the relative shift between two signals using their timestamps and Fourier Transform.

    Parameters:
    signal1 (numpy array): The first signal.
    timestamps1 (numpy array): The timestamps for the first signal.
    signal2 (numpy array): The second signal.
    timestamps2 (numpy array): The timestamps for the second signal.

    Returns:
    float: The relative shift between the two signals in the same units as the timestamps.
    """

    if len(signal1) != len(timestamps1) or len(signal2) != len(timestamps2):
        raise ValueError(f"The lengths of the signals and timestamps must match, with {len(signal1)} signals and {len(timestamps1)} timestamps for the first signal and {len(signal2)} signals and {len(timestamps2)} timestamps for the second signal.")

    # Ensure the signals and timestamps are numpy arrays
    signal1 = numpy.array(signal1)
    timestamps1 = numpy.array(timestamps1)
    signal2 = numpy.array(signal2)
    timestamps2 = numpy.array(timestamps2)

    # Create a common time grid for interpolation
    common_time = numpy.linspace(max(timestamps1[0], timestamps2[0]), min(timestamps1[-1], timestamps2[-1]), num=1000)

    # Interpolate the signals on the common time grid
    interp_signal1 = interp1d(timestamps1, signal1, kind='linear', fill_value="extrapolate")(common_time)
    interp_signal2 = interp1d(timestamps2, signal2, kind='linear', fill_value="extrapolate")(common_time)

    # Compute the Fourier Transform of both signals
    fft_signal1 = fft(interp_signal1)
    fft_signal2 = fft(interp_signal2)

    # Compute the cross-correlation in the frequency domain
    cross_correlation = ifft(fft_signal1 * numpy.conj(fft_signal2))

    # Find the index of the maximum correlation
    maximum_correlation_index = numpy.argmax(numpy.abs(cross_correlation))

    # Calculate the relative shift in terms of the common time grid
    if maximum_correlation_index < len(common_time) // 2:
        relative_shift = maximum_correlation_index
    else:
        relative_shift = maximum_correlation_index - len(common_time)

    # Convert the relative shift to the original time units
    time_step = common_time[1] - common_time[0]
    relative_shift_time = relative_shift * time_step

    return -relative_shift_time 

def get_shifts(data):
    """
    Calculate the relative shifts between the first signal and all other signals using their timestamps.

    # Parameters:
    - data (dict of dataframes of shape (n, 2)): The signals and timestamps for each sensor.
    
    # Returns:
    - dict : The relative shifts between the first signal and all other signals.
    """

    reference_signal = next(iter(data))
    reference_value = data[reference_signal]["value"].values
    reference_time = data[reference_signal]["time"].values


    shifts = {}
    shifts[reference_signal] = 0

    for name, signal in data.items():
        if name == reference_signal:
            continue

        current_value = signal["value"].values
        current_time = signal["time"].values

        shifts[name] = get_shift(reference_value, reference_time, current_value, current_time)

    return shifts


def get_sliding_shift(signal1, timestamps1, signal2, timestamps2, window_size=10):
    """
    Calculate the sliding shift between two signals using a specified window size.

    Parameters:
    signal1 (numpy array): The first signal.
    timestamps1 (numpy array): The timestamps for the first signal.
    signal2 (numpy array): The second signal.
    timestamps2 (numpy array): The timestamps for the second signal.
    window_size (int): The size of the window to slide over the signals.

    Returns:
    list: A list of calculated shifts for each window position.
    """

    if len(signal1) < window_size or len(signal2) < window_size:
        raise ValueError("The signals must be at least as long as the window size.")

    num_windows = len(signal1) - window_size + 1

    shifts = numpy.zeros(num_windows)
    shifts_timestamps = numpy.zeros(num_windows)

    for i in range(num_windows):
        window_signal1 = signal1[i:i + window_size]
        window_timestamps1 = timestamps1[i:i + window_size]
        window_signal2 = signal2[i:i + window_size]
        window_timestamps2 = timestamps2[i:i + window_size]

        shifts[i] = get_shift(window_signal1, window_timestamps1, window_signal2, window_timestamps2)

        shifts_timestamps[i] = window_timestamps1[0]
        
    return (shifts, shifts_timestamps)

class VoltageDividerClass:
    def __init__(self, R_2, V_in):
        """
        Create a new voltage divider circuit.

        # Parameters:
        - R_2 (float): The resistance of the second resistor in the voltage divider circuit.
        - V_in (float): The input voltage of the voltage divider circuit.

        # Returns:
        - VoltageDividerClass: The new voltage divider circuit.
        """

        self.R_2 = R_2
        self.V_in = V_in

    def get_R1(self, V_out):
        """
        Get the resistance of the first resistor in the voltage divider circuit (R_1 between V_in and V_out).

        # Parameters:
        - V_out (float): The output voltage of the voltage divider circuit.
    
        # Returns:
        - float: The resistance of the second resistor.
        """

        return self.R_2 * (self.V_in - V_out) / V_out

class CalibrationCurveClass:
    def __init__(self, R_0, a, b):
        """
        Create a new calibration curve.
        
        # Parameters:
        - R_0 (float): The resistance of the gas sensor in clean air.
        - a (float): The slope of the calibration curve.
        - b (float): The intercept of the calibration curve.

        # Returns:
        - CalibrationCurveClass: The new calibration
        """
    
        self.R_0 = R_0
        self.a = a
        self.b = b

    def get_concentration(self, resistance):
        """
        Get the concentration of a gas based on its resistance.

        # Parameters:

        - resistance (float or numpy.ndarray): The resistance of the gas sensor.

        # Returns:

        - float: The concentration of the gas.
        """

        ratio = numpy.log10(resistance / self.R_0)  # log(R / R_0)
        division = (ratio - self.b) / self.a # (log(R / R_0) - b) / a
        return numpy.power(10, division) # 10^((log(R / R_0) - b) / a)

      
class GazSensorClass:
    def __init__(self, configuration, maximum_values=10000):
        """
        Create a new gas sensor

        # Arguments

        - configuration (dict): sensor configuration
        - maximum_values (int): maximum number of values

        # Returns
        - GazSensorClass: new gas sensor
        
        """

        self.voltage_divider = VoltageDividerClass(configuration["R_2"], configuration["V_in"])
        self.calibration_curve = CalibrationCurveClass(configuration["R_0"], configuration["a"], configuration["b"])

        self.data = pandas.DataFrame(numpy.zeros((maximum_values, 8)), 
            columns=["time",
            "raw_value",
            "raw_value_filtered",
            "raw_value_filtered_gradient",
            "resistance",
            "concentration",
            "concentration_filtered",
            "concentration_filtered_gradient"])

        self.butterworth = None
        self.filtering_chunk_size = 64

        self.index = 0

        self.excitement_index = None
        self.excitement_threshold = 1e-5

    def update(self, value : float, timestamp : float):
        i = self.index

        if i >= self.data.shape[0]:
            raise ValueError("Too many values for sensor")

        # Get the resistance of the sensor
        resistance = self.voltage_divider.get_R1(value)

        # Get the concentration of the gas
        concentration = self.calibration_curve.get_concentration(resistance)           

        previous_index = i - 1

        time_difference = (timestamp - self.data.iloc[previous_index]["time"]) / 1000
    
        if i > 0:

            if time_difference < 0:
                raise ValueError(f"Timestamps must be increasing : {timestamp} <= {self.data.iloc[previous_index]['time']} for index {i}")


            # Calculate the gradients
            concentration_gradient = (concentration - self.data.iloc[previous_index]["concentration"]) / time_difference
        
        else:
            raw_value_gradient = 0
            resistance_gradient = 0
            concentration_gradient = 0

        # Update the data
        self.data.iloc[i] = [timestamp, value, 0, 0, resistance, concentration, 0, 0]

        # Increment the index
        self.index += 1

        i = self.index

        # Apply filtering
        if i >= self.filtering_chunk_size:

            if self.butterworth is None:
                sample_frequency = self.get_sample_frequency()
                self.butterworth = butter(4, Wn=0.1, fs=sample_frequency, output="sos", btype="lowpass")
            
            previous_chunk_index = i - self.filtering_chunk_size

            self.data["raw_value_filtered"].values[:i] = sosfiltfilt(self.butterworth, self.data["raw_value"].values[:i])

            self.data["raw_value_filtered_gradient"].values[:i] = numpy.abs(numpy.gradient(self.data["raw_value_filtered"].values[:i], self.data["time"].values[:i]))

            self.data["concentration_filtered"].values[:i] = sosfiltfilt(self.butterworth, self.data["concentration"].values[:i])

            self.data["concentration_filtered_gradient"].values[:i] = numpy.abs(numpy.gradient(self.data["concentration_filtered"].values[:i], self.data["time"].values[:i]))

            # Find the excitement index
            if self.data["raw_value_filtered_gradient"].values[i - 1] > self.excitement_threshold:
                if self.excitement_index is None:
                    sample_frequency = self.get_sample_frequency()

                    print(f"i = {i}, sample_frequency = {sample_frequency}")

                    self.excitement_index = i - int(2 / (1/sample_frequency)) # 2 seconds before the excitement
            
    def get_current_index(self):
        return self.index

    def get_sample_frequency(self):
        i = self.index

        if i == 0:
            raise ValueError("No values for sensor")

        return 1 / (numpy.diff(self.data.iloc[:i]["time"]).mean() / 1000)

    def get_latest_values(self):
        i = self.index
        
        if i == 0:
            raise ValueError("No values for sensor")
        
        return self.data.iloc[i - 1]

    def get_excitement_index(self):
        return self.excitement_index

    def get_all_values(self):
        i = self.index

        return self.data.iloc[:i]

    def get_gradient(self):
        i = self.index

        if i == 0:
            raise ValueError("No values for sensor")

        data = self.data.iloc[:i].copy()

        concentration_gradient = numpy.gradient(data["concentration"], data["time"])

        resistance_gradient = numpy.gradient(data["resistance"], data["time"])

        raw_value_gradient = numpy.gradient(data["raw_value"], data["time"])

        return pandas.DataFrame({
            "time": data["time"],
            "raw_value": raw_value_gradient,
            "resistance": resistance_gradient,
            "concentration": concentration_gradient,
        })

    def get_response_time(self):
        """
        Get the response time of the sensor

        # Returns

        - float: response time (average time difference between values)
        """

        i = self.index

        if i == 0:
            raise ValueError("No values for sensor")

        data = self.data.iloc[:i].copy()

        time_differences = numpy.diff(data["time"])

        return numpy.mean(time_differences)

class SensorClass:
    
    def __init__(self, configuration):
        """
        Create a new sensor

        # Returns
        - SensorClass: new sensor    
        """

        self.configuration = configuration

        self.sensors = {}

        for name, sensor_configuration in self.configuration.sensors.items():
            self.sensors[name] = GazSensorClass(sensor_configuration, self.configuration.maximum_values)
          
    def update(self, gaz_sensors_type, value, timestamp):
        if gaz_sensors_type not in self.sensors:
            raise ValueError(f"Sensor does not have {gaz_sensors_type}")

        self.sensors[gaz_sensors_type].update(value, timestamp)
              
    def get_position(self):
        return self.configuration.x, self.configuration.y

    def get_gaz_sensors_types(self):
        return list(self.sensors.keys())


    def get_latest_values(self, gaz_sensors_type, scale=False):
        """
        Get the latest values for a sensor

        # Arguments

        - gaz_sensors_type (str): gaz sensor type
        - scale (bool): scale values

        # Returns

        - pandas.Series or dict: values
        """

        if gaz_sensors_type not in self.sensors:
            raise ValueError(f"Sensor does not have {gaz_sensors_type}")

        return self.sensors[gaz_sensors_type].get_latest_values()

    def get_all_values(self, gaz_sensors_type=None):
        """
        Get all values for a sensor

        # Arguments

        - gaz_sensors_type (str): gaz sensor type, None for all
        - scale (bool): scale values

        # Returns

        - pandas.DataFrame or dict: values
        """

        if gaz_sensors_type is None:
            return {gaz_sensors_type: sensor.get_all_values() for gaz_sensors_type, sensor in self.sensors.items()}

        if gaz_sensors_type not in self.sensors:
            raise ValueError(f"Sensor does not have {gaz_sensors_type}")

        return self.sensors[gaz_sensors_type].get_all_values()
    
    def get_current_index(self, gaz_sensors_type):
        if gaz_sensors_type not in self.sensors:
            raise ValueError(f"Sensor does not have {gaz_sensors_type}")

        return self.sensors[gaz_sensors_type].get_current_index()

    def get_excitement_index(self, gaz_sensors_type):
        if gaz_sensors_type not in self.sensors:
            raise ValueError(f"Sensor does not have {gaz_sensors_type}")

        return self.sensors[gaz_sensors_type].get_excitement_index()

    def get_gradient(self, gaz_sensors_type):
        if gaz_sensors_type not in self.sensors:
            raise ValueError(f"Sensor does not have {gaz_sensors_type}")

        self.sensors[gaz_sensors_type].get_gradient()

    def get_average_time_difference(self, gaz_sensors_type):
        """
        Get the average time difference between values for a sensor

        # Arguments

        - gaz_sensors_type (str): gaz sensor type

        # Returns

        - float: average time difference
        """

        if gaz_sensors_type not in self.sensors:
            raise ValueError(f"Sensor does not have {gaz_sensors_type}")

        return self.sensors[gaz_sensors_type].get_response_time()

    def __str__(self):
        return f"Sensor ({self.x}, {self.y}) :\n - Value {self.get_latest_values()}"