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

    if identifier not in sensors:
        print(f"Unknown sensor {identifier}")
        return

    data = message["data"]

    for key, sensor in data.items():

        # We get the timestamp and the value from the sensor
        timestamp = sensor["timestamp"]
        # We use the first timestamp as the reference
        if start is None:
            start = timestamp

        # We get the time since the first timestamp
        if timestamp >= start:
            timestamp -= start
        else:
            timestamp = 0

        value = sensor["value"]        

        if value is None:
            continue

        # Try to update the sensor with the new data
        if not(sensors[identifier].update(key, value, timestamp)):
            print(f"Failed to update sensor {identifier} with data {data}")

def get_sensors_position():
    positions = numpy.zeros((len(sensors), 2))

    for i, (_, sensor) in enumerate(sensors.items()):
        position = sensor.get_position()
        positions[i, :] = position

    return positions

def get_sensors_value(gaz_sensor_type):
    values = numpy.zeros(len(sensors))

    for i, (_, sensor) in enumerate(sensors.items()):
        sensor_values = sensor.get_latest_values(gaz_sensor_type)
        if sensor_values is None:
            return None
        values[i] = sensor_values[1]
    
    return values

def locate_delaunay(sensors_position, sensors_value):
    # Create the Delaunay triangulation
    triangle = scipy.spatial.Delaunay(sensors_position)

    # Compute the barycenter of each triangle
    source_coordinates = numpy.average(sensors_position[triangle.simplices], axis=1, weights=sensors_value)

    return source_coordinates[0]

def locate_optimize(sensors_position, sensors_value):
    # Positions des capteurs
    positions = sensors_position

    # Concentrations mesurées
    concentrations = sensors_value

    # Fonction de modèle
    def model(params, positions, concentrations):
        x, y, K = params
        predicted_concentrations = K / numpy.linalg.norm(positions - numpy.array([x, y]), axis=1)**2
        return numpy.sum((concentrations - predicted_concentrations)**2)

    # Estimation initiale (peut être ajustée)
    initial_guess = [0.5, 0.5, 1]

    # Optimisation pour minimiser l'erreur
    result = scipy.optimize.minimize(model, initial_guess, args=(positions, concentrations))

    # Résultat de l'optimisation
    x_source, y_source, K_source = result.x

    print(f"Position de la source : ({x_source}, {y_source})")
    print(f"Constante K : {K_source}")

    return numpy.array([x_source, y_source])


def localize_source(axes, map_size):
    sensors_position = get_sensors_position()
    sensors_value = get_sensors_value("MQ3")

    if sensors_value is None:
        print("Not enough sensors values")
        return

    if sensors_value.shape[0] < 3:
        print("Not enough sensors")
        return

    if sensors_value.sum() == 0:
        print("No gaz detected")
        return

    #delaunay_position = locate_delaunay(sensors_position, sensors_value)

    #print(f"Source coordinates : {delaunay_position}")

    optimize_position = locate_optimize(sensors_position, sensors_value)

    print(f"Source coordinates : {optimize_position}")

    plot_source_position(axes, map_size, optimize_position)


def get_map_size():
    x = numpy.zeros(len(sensors))
    y = numpy.zeros(len(sensors))

    for i, (_, sensor) in enumerate(sensors.items()):
        position = sensor.get_position()
        x[i] = position[0]
        y[i] = position[1]

    

    return (x.min(), x.max(), y.min(), y.max())


sensors = {
    "Sensor_1": SensorClass(0, 0),
    "Sensor_2": SensorClass(0, 1),
    "Sensor_3": SensorClass(1, 1),
}

start = None

def plot_sensor_values(axes, gaz_sensor_type, center):
    axes.clear()
    axes.set_title(f"Sensors values for {gaz_sensor_type} center={center}")
    axes.set_xlabel("Time (s)")
    axes.set_ylabel("Value")

    any_plot = False

    for name, sensor in sensors.items():
        label = f"{name} {sensor.get_position()}"

        values = sensor.get_all_values(gaz_sensor_type, center=center)

        if values is not None:
            axes.plot((values[0]/1000), values[1], label=label)
            any_plot = True

    if any_plot:
        axes.legend()
        plt.plot(block=False)

        plt.pause(0.1)

def plot_source_position(axes, map_size, source_position):
    axes.clear()
    axes.set_title("Source position")
    axes.set_xlabel("X")
    axes.set_ylabel("Y")

    axes.set_xlim(map_size[0], map_size[1])
    axes.set_ylim(map_size[2], map_size[3])
    
    axes.scatter(source_position[0], source_position[1])

    plt.plot(block=False)
    plt.pause(0.1)

def plot_growth(axes, gaz_sensor_type):
    axes.clear()
    axes.set_title(f"Sensor growth for {gaz_sensor_type}")
    axes.set_xlabel("Time (s)")
    axes.set_ylabel("Value")

    any_plot = False

    for name, sensor in sensors.items():
        label = f"{name} {sensor.get_position()}"

        growth = sensor.get_growth_rate(gaz_sensor_type)

        if growth is not None:
            axes.plot((growth[0]/1000), numpy.absolute(growth[1]), label=label)
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
        mq3_axes = figure.add_subplot(2,2,1)
        #mq136_axes = figure.add_subplot(2,2,2)
        mq3_norm_axes = figure.add_subplot(2,2,2)
        growth_axes = figure.add_subplot(2,2,4)

        location_axes = figure.add_subplot(2,2,3)

        map_size = get_map_size()

        while True:
            localize_source(location_axes, map_size)
        
            plot_sensor_values(mq3_axes, "MQ3", False)
            plot_sensor_values(mq3_norm_axes, "MQ3", True)
            plot_growth(growth_axes, "MQ3")
            #plot_sensor_values(mq136_axes, "MQ136")


    except KeyboardInterrupt:
    
        print("Disconnecting from MQTT Broker")

        client.loop_stop()
        client.disconnect()




if __name__ == "__main__":
    main()

