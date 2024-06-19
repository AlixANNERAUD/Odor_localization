import paho.mqtt.client as mqtt
import time
from sensor import SensorClass
import numpy
import scipy 

MQTT_BROKER = "alixloicrpi.local"
MQTT_PORT = 1883
MQTT_SENSORS_TOPIC = "sensors"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connecté au broker MQTT")
        client.subscribe(MQTT_TOPIC)
    else:
        print("Échec de la connexion, code de retour:", rc)

def on_message(client, userdata, msg):
    if not(msg.topic.startswith(MQTT_SENSORS_TOPIC)):
        return

    sensor_identifier = msg.topic.split("/")[-1]

    if sensor_identifier not in sensors:
        print(f"Capteur inconnu: {sensor_identifier}")
        return

    sensors[sensor_identifier].update(msg.payload.decode())

def get_sensors_position():
    sensors_positions = []
    for _, sensor in sensors.items():
        sensors_positions.append(sensor.get_position())

    return numpy.array(sensors_positions)

def get_sensors_value():
    sensors_values = []
    for _, sensor in sensors.items():
        sensors_values.append(sensor.get_value())

    return numpy.array(sensors_values)

def localize_source():
    sensors_position = get_sensors_position()
    sensors_value = get_sensors_value()

    triangulation = scipy.spatial.Delaunay(sensors_position)

    source_coordinates = numpy.average(sensors_position[triangulation.simplices], axis=1, weights=sensors_value)

    return source_coordinates

sensors = {
    "sensor1": SensorClass(0, 0),
    "sensor2": SensorClass(0, 1),
    "sensor3": SensorClass(1, 0),
}

def main():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_BROKER, MQTT_PORT, 60)

    try:
        client.loop_start() 
        while True:
            localization = localize_source()

            print(f"Source localisée en ({localization[0]}, {localization[1]})")   
            
            time.sleep(1)  
    except KeyboardInterrupt:
        print("Déconnexion du client MQTT")
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()

