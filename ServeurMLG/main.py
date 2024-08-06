import paho.mqtt.client as mqtt
import time
from sensor import SensorClass
import numpy
import scipy 
import json
import matplotlib.pyplot as plt
import matplotlib.animation as animation
import numpy as np

MQTT_BROKER = "alixloicrpi.local"
MQTT_PORT = 1883
MQTT_TOPIC = "sensors"

sensors = {
    "Sensor_1": SensorClass(),
    "Sensor_2": SensorClass(),
}

start = None
valuechangeV1 = False
valuechangeV2 = False

# -------- A compléter --------
v1Min = 0.08
v1Max = 0.60
v2Min = 0.30
v2Max = 1
# -----------------------------



def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connected to MQTT Broker")
        client.subscribe(MQTT_TOPIC)
    else:
        print(f"Failed to connect to MQTT Broker, return code {rc}\n")


def on_message(client, userdata, msg):
    global start
    global valuechangeV1
    global valuechangeV2

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
        # Faire une normalisation des valeurs suivant la formule : (x - min) / (max - min) et l'indentificateur du capteur
        if identifier == "Sensor_1" :
            value = (value - v1Min) / (v1Max - v1Min) 
        elif identifier == "Sensor_2" :
            value = (value - v2Min) / (v2Max - v2Min)
        else:
            print("Unknown sensor")
            return
        
        if not(sensors[identifier].update( key, value, timestamp)):
            print(f"Failed to update sensor {identifier} with data {data}")
        else:
            if identifier == "Sensor_1" :
                valuechangeV1 = True
            elif identifier == "Sensor_2" :
                valuechangeV2 = True
            else:
                print("Unknown sensor")
                return
        


def arrivee(): 
    while True:
        print("Sensor_1 : ")
        print(sensors["Sensor_1"].get_latest_values("MQ3", False))
        print("Sensor_2 : ")
        print(sensors["Sensor_2"].get_latest_values("MQ3", False))
        time.sleep(1)

def waySource():
    global valuechangeV1
    global valuechangeV2
    global sensors

    direction = 0

    sensors1Values = []
    sensors2Values = []
    while True:

        if valuechangeV1  and len(sensors1Values) <= 20:
            valuechangeV1 = False
            t1, v1 = sensors["Sensor_1"].get_latest_values("MQ3", False) 
            sensors1Values.append(v1)

        elif valuechangeV2 and len(sensors2Values) <= 20:
            valuechangeV2 = False
            t2, v2 = sensors["Sensor_2"].get_latest_values("MQ3", False) 
            sensors2Values.append(v2)

        elif (len(sensors1Values) >= 20) and (len(sensors2Values) >= 20):

            #print("Sensor_1 : ", sensors1Values)
            #print("Sensor_2 : ", sensors2Values)

            # Calculer la moyenne des valeurs
            sensors1ValuesNP = np.array(sensors1Values)
            sensors2ValuesNP = np.array(sensors2Values)

            # Calculer les dérivées
            derivative1 = np.diff(sensors1ValuesNP)
            derivative2 = np.diff(sensors2ValuesNP)
            # Calculer la moyenne des dérivées
            mean_derivative1 = np.mean(derivative1)*100 + np.mean(sensors1ValuesNP)
            mean_derivative2 = np.mean(derivative2)*100 + np.mean(sensors2ValuesNP)
            if mean_derivative1 < 0 and mean_derivative1 > -1:
                mean_derivative1 = abs(mean_derivative1)
            if mean_derivative2 < 0 and mean_derivative2 > -1:
                mean_derivative2 = abs(mean_derivative2)

            print("La moyenne des dérivées de Sensor_1 est : ", mean_derivative1)
            print("La moyenne des dérivées de Sensor_2 est : ", mean_derivative2)

            # Calculer la direction

            if mean_derivative1 > 0 and mean_derivative2 > 0 :
                if mean_derivative1 > mean_derivative2:
                    direction = mean_derivative1 / (mean_derivative2*1.0)
                    direction = direction * (- 1)
                else:
                    direction = mean_derivative2 / (mean_derivative1*1.0)
                    
                print("la direction est : ", direction)
            
            #si la direction etait mauvaise
            elif mean_derivative1 < 0 or mean_derivative2 < 0 :
                print("Mauvaise direction : revenir en arrière (180 degrés) et prendre la direction ", direction)
            else:
                print("Pas de direction : essayer une direction aléatoire et recommencer")
                direction = 0.0
            
            sensors1Values.clear()
            sensors2Values.clear()

        time.sleep(1)





def main():
    try: 
        client = mqtt.Client()
        client.on_connect = on_connect
        client.on_message = on_message
    #try:
        client.connect(MQTT_BROKER, MQTT_PORT, 60)
    except Exception as e:
        print("Failed to connect to MQTT Broker : ", e)
        return


    try:
        client.loop_start() 
        waySource()
        #arrivee()
    


    except KeyboardInterrupt:
    
        print("Disconnecting from MQTT Broker")

        client.loop_stop()
        client.disconnect()




if __name__ == "__main__":
    main()

