import paho.mqtt.client as mqtt
import time
from sensor import SensorClass
import numpy
import scipy 
import json

MQTT_BROKER = "alixloicrpi.local"
MQTT_PORT = 1883
MQTT_TOPIC = "sensors"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker")
        client.subscribe(MQTT_TOPIC)
    else:
        print(f"Failed to connect to MQTT Broker, return code {rc}\n")

def on_message(client, userdata, msg):
    message = json.loads(msg.payload.decode())

    identifier = message["sensor"]

    data = message["data"]

    timestamp = message["timestamp"]

    sensors[identifier].update(data, timestamp)

    for _, sensor in sensors.items():
        print(f"{str(sensor)}")

    print("\n")

def get_sensors_position():
    sensors_positions = []
    for _, sensor in sensors.items():
        sensors_positions.append(sensor.get_position())

    return numpy.array(sensors_positions)

def get_sensors_value():
    sensors_values = []
    for _, sensor in sensors.items():
        if sensor.get_value() is None:
            return None
        sensors_values.append(sensor.get_value())

    return numpy.array(sensors_values)

def localize_source():
    sensors_position = get_sensors_position()
    sensors_value = get_sensors_value()

    if sensors_value is None:
        return None

    triangulation = scipy.spatial.Delaunay(sensors_position)

    source_coordinates = numpy.average(sensors_position[triangulation.simplices], axis=1, weights=sensors_value)

    return source_coordinates

sensors = {
    "Sensor_1": SensorClass(0, 0),
    "Sensor_2": SensorClass(0, 1),
    "Sensor_3": SensorClass(1, 0),
}

def main():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
    except Exception as e:
        print("Failed to connect to MQTT Broker : ", e)
        return

    try:
        client.loop_start() 
        while True:
            localization = localize_source()

            if localization is None:
                print(f"Waiting for all sensors data ...")
            else:
                print(f"Source localized at {localization}.")
            
            time.sleep(1)  
    except KeyboardInterrupt:
        print("Disconnecting from MQTT Broker")
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()

