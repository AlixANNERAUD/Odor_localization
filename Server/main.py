import paho.mqtt.client as mqtt
import time
from sensor import SensorClass
import numpy
import scipy 
import json
import matplotlib.pyplot as plt
import matplotlib.animation as animation

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
    global start

    message = json.loads(msg.payload.decode())

    identifier = message["sensor"]

    data = message["data"]

    timestamp = message["timestamp"]

    if start is None:
        start = timestamp

    for key, value in data.items():
        if not(sensors[identifier].update(key, value, timestamp)):
            print(f"Failed to update sensor {identifier} with data {data}")

def get_sensors_position():
    sensors_positions = []
    for _, sensor in sensors.items():
        sensors_positions.append(sensor.get_position())

    return numpy.array(sensors_positions)

def get_sensors_value(gaz_sensor_type):
    sensors_values = []
    for _, sensor in sensors.items():
        sensor_values = sensor.get_latest_values(gaz_sensor_type)
        if sensor_values is None:
            return None
        values, _ = sensor_values
        sensors_values.append(values)

    return numpy.array(sensors_values)

def localize_source():
    sensors_position = get_sensors_position()
    sensors_value = get_sensors_value("MQ3")
   
    print(f"Sensor value : {sensors_value}")

    if sensors_value is None:
        print("Not enough sensors !")
        return None

    # If we have less than 3 sensors
    if sensors_value.shape[0] < 3:
        x_1, y_1 = sensors_position[0]
        x_2, y_2 = sensors_position[1]

        

        max_value = numpy.max([sensors_value])

        r_1 = 1 + max_value - sensors_value[0]
        r_2 = 1 + max_value - sensors_value[1]

        d = numpy.sqrt((x_2 - x_1)**2 + (y_2 - y_1)**2)

        if d >= r_1 + r_2 or d <= numpy.abs(r_1 - r_2) or (d == 0 and r_1 != r_2):
            print("Failed !")
            return None

        a = (r_1**2 - r_2**2 + d**2) / (2 * d)

        h = numpy.sqrt(r_1**2 - a**2)

        x_3 = x_1 + a * (x_2 - x_1) / d

        y_3 = y_1 + a * (y_2 - y_1) / d

        intersection_1 = (x_3 + h * (y_2 - y_1) / d, y_3 - h * (x_2 - x_1) / d)
        intersection_2 = (x_3 - h * (y_2 - y_1) / d, y_3 + h * (x_2 - x_1) / d)

        angle = numpy.arctan2(intersection_1[1] - y_1, intersection_1[0] - x_1)

        angle_deg = numpy.degrees(angle)

        return angle_deg
    # If we have 3 sensors or more, we use delaunay triangulation
    else:
        triangulation = scipy.spatial.Delaunay(sensors_position)

        source_coordinates = numpy.average(sensors_position[triangulation.simplices], axes=1, weights=sensors_value)

        return source_coordinates

sensors = {
    "Sensor_1": SensorClass(23, 0),
    "Sensor_2": SensorClass(0, 0),
}

start = None

def plot_sensor_values(axes, gaz_sensor_type):
    axes.clear()
    axes.set_title(f"Sensors values for {gaz_sensor_type}")
    axes.set_xlabel("Time (s)")
    axes.set_ylabel("Value")

    any_plot = False

    for name, sensor in sensors.items():
        values = sensor.get_all_values(gaz_sensor_type)
        if values is not None:
            axes.plot((values[0] - start)/1000, values[1], label=name)
            any_plot = True

    if any_plot:
        axes.legend()
        plt.plot(block=False)

        plt.pause(0.1)

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

        figure = plt.figure()
        axes = figure.add_subplot(1,1,1)

        while True:
            localization = localize_source()
   
            if localization is None:
                print(f"Waiting for all sensors data ...")
            else:
                print(f"Source localized at {localization}.")
         
            plot_sensor_values(axes, "MQ3")

    except KeyboardInterrupt:
        print("Disconnecting from MQTT Broker")

        client.loop_stop()
        client.disconnect()




if __name__ == "__main__":
    main()

