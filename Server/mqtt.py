
# - Libraries

# - - MQTT
import paho.mqtt.client as mqtt

import configuration

import logging

import json

class MQTTClientClass:

    def __init__(self, configuration, update_sensors_callback):
        """
        MQTT class

        # Arguments

        - configuration (MQTTConfigurationClass): The MQTT configuration

        # Returns

        - MQTTClass: The MQTT class

        """

        self.configuration = configuration
        self.client = mqtt.Client(mqtt.CallbackAPIVersion.VERSION2)

        def on_connect(client, userdata, flags, reason_code, properties):
            if reason_code != 0:
                raise ValueError(f"Failed to connect to the MQTT broker: {reason_code}")

            client.subscribe(configuration.topic)
            logging.info("Connected to the MQTT broker")

        def on_message(client, userdata, message):
            data = json.loads(message.payload.decode("utf-8"))

            update_sensors_callback(data["sensor"], data["data"])

        self.client.on_connect = on_connect
        self.client.on_message = on_message
        
        self.client.connect(self.configuration.host, self.configuration.port)
        self.client.loop_start()

        
    def stop(self):
        self.client.loop_stop()
        self.client.disconnect()



