import logging
import numpy

def get_current_timestamp(sensors, gaz_sensor_type):
    current_timestamp = 0
    # Iterate over the sensors
    for sensor in sensors.values():
        sensor_values = sensor.get_all_values(gaz_sensor_type)

        if sensor_values.shape[0] > 0:
            # Check if the last timestamp is greater than the latest timestamp
            if sensor.get_all_values("MQ3")["time"].values[-1] > current_timestamp:
                # Update the latest timestamp
                current_timestamp = sensor.get_all_values("MQ3")["time"].values[-1]

    return current_timestamp

class ExcitementClass:

    def __init__(self, gaz_sensor_type):
        
        self.excited_indexes = {}

        self.last_excitement_timestamp = None
        self.first_excitement_timestamp = None

        self.gaz_sensor_type = gaz_sensor_type

        self.timeout = 40000

    def get_last_excitement_timestamp(self):
        return self.last_excitement_timestamp

    def get_first_excitement_timestamp(self):
        return self.first_excitement_timestamp

    def get_excited_signals(self, sensors):

        excited_signals = {}
        
        for name, index in self.excited_indexes.items():

            
            #print(f"All values: {sensors[name].get_all_values(self.gaz_sensor_type)}")

            excited_signals[name] = sensors[name].get_all_values(self.gaz_sensor_type)[["time", "raw_value_filtered"]].iloc[index:]
            
            excited_signals[name].rename(columns={"raw_value_filtered": "value"}, inplace=True)

        return excited_signals

    def is_all_excited(self, sensors):
        return len(self.excited_indexes) == len(sensors)

    def loop(self, sensors):

        # Get the latest timestamp
        current_timestamp = get_current_timestamp(sensors, self.gaz_sensor_type)

        # Check for timeout
        if self.last_excitement_timestamp is not None:
            if current_timestamp - self.last_excitement_timestamp > self.timeout:
                self.last_excitement_timestamp = None
                self.first_excitement_timestamp = None
                self.excited_indexes = {}

                logging.info("Exc timeout")

        # Check for the first excitement timestamp
        for name, sensor in sensors.items():
            # Ignore the sensor if it is already excited
            excitement_index = sensor.get_excitement_index(self.gaz_sensor_type)

            if excitement_index is not None:

                if name not in self.excited_indexes:

                    logging.info(f"Excited: {name}")
                    
                    excitement_time = sensor.get_all_values(self.gaz_sensor_type)["time"][excitement_index]
                
                    # - Set the first excitement timestamp
                    if self.first_excitement_timestamp is None:
                        self.first_excitement_timestamp = excitement_time
                        logging.info(f"First excitement timestamp: {self.first_excitement_timestamp}")
                    
                    # Set the last excitement timestamp (for timeout)
                    self.last_excitement_timestamp = excitement_time
                    
                    # - Extract the start index of the excitement
                    i = numpy.where(sensor.get_all_values(self.gaz_sensor_type)["time"] >= self.first_excitement_timestamp)[0][0]
                    self.excited_indexes[name] = i

                 


    