import paho.mqtt.client as mqtt
import time

MQTT_BROKER = "broker.hivemq.com" 
MQTT_PORT = 1883
MQTT_TOPIC = "your/topic"

def on_connect(client, userdata, flags, rc):
    if rc == 0:
        print("Connecté au broker MQTT")
        client.subscribe(MQTT_TOPIC)
    else:
        print("Échec de la connexion, code de retour:", rc)

def on_message(client, userdata, msg):
    print(f"Message reçu sur le topic {msg.topic}: {msg.payload.decode()}")

def main():
    client = mqtt.Client()
    client.on_connect = on_connect
    client.on_message = on_message

    client.connect(MQTT_BROKER, MQTT_PORT, 60)

    try:
        client.loop_start() 
        while True:
            
            
            time.sleep(1)  
    except KeyboardInterrupt:
        print("Déconnexion du client MQTT")
        client.loop_stop()
        client.disconnect()


if __name__ == "__main__":
    main()

