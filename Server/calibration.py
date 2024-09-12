
# - - Time
import time
import datetime

class CalibrationClass:
    def __init__(self, configuration):
        self.configuration = configuration

        if self.configuration.enable:
            self.end = datetime.datetime.now() + datetime.timedelta(seconds=self.configuration.duration)
        else:
            self.end = None

    def state(self):
        if self.end is None:
            return None

        return self.end - datetime.datetime.now()

    def loop(self, sensors):
        # If the calibration is not enabled, return None
        if self.end is None:
            return None

        # If the calibration is not finished, return None
        if datetime.datetime.now() < self.end:
            return None
            
        # Disable the calibration
        self.end = None

        results = ""

        # Iterate over all sensors
        for name, sensor in sensors.items():
            results += f"- Sensor {name} :\n"

            # Iterate over all sensors type for the sensor
            for sensor_type, data in sensor.get_all_values().items():
                # Compute the mean and the standard deviation of the collected data
                results += f" - {sensor_type} R_0 : {data['resistance'].mean():.2f} ± {data['resistance'].std()/data['resistance'].mean()*100:.2f}%\n ({data['resistance'].shape[0]} samples)\n"

        return results


