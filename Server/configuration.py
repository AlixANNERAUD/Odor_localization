import json

class CalibrationConfigurationClass:
    def __init__(self, data):
        """
        Calibration configuration

        # Arguments

        - calibration_enable (bool): If the calibration is enabled
        - calibration_time (int): The time in seconds to calibrate

        # Returns

        - CalibrationConfigurationClass: The calibration configuration
        """

        self.enable: bool = data["enable"]
        self.duration: int = data["duration"]

class MQTTConfigurationClass:
    def __init__(self, data):
        """
        MQTT configuration

        # Arguments

        - data (dict): The data with the configuration

        # Returns

        - MQTTConfigurationClass: The MQTT configuration

        """

        self.host:str = data["host"]
        self.port:int = data["port"]
        self.topic:str = data["topic"]

class SensorConfigurationClass:
    def __init__(self, data):
        self.maximum_values = 10000

        self.from_dictionary(data)

    def from_dictionary(self, data):
        for key, value in data.items():
            setattr(self, key, value)


def load(file):
    """
    Load sensors from a json file

    # Arguments

    - file (str): The path to the json file

    # Returns

    - (MQTTConfigurationClass, CalibrationConfigurationClass, dict): The MQTT configuration, the calibration configuration and the sensors
    """

    with open(file) as f:
        data = json.load(f)
    
    sensors = {}
    for name, configuration in data.items():
        if name == "mqtt":
            mqtt_configuration = MQTTConfigurationClass(configuration)
        elif name == "calibration":
            calibration_configuration = CalibrationConfigurationClass(configuration)
        elif name == "sensors":
            for sensor_identifier, sensor_configuration in configuration.items():
                sensors[sensor_identifier] = SensorConfigurationClass(sensor_configuration)
        else:
            raise ValueError(f"Unexpected configuration: {name}")


    return mqtt_configuration, calibration_configuration, sensors


