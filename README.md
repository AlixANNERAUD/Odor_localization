<h1 align="center">Odor localization</h1>

# 📝 Description

TODO

## Architecture

```mermaid
graph LR
    
    subgraph "Sensors"
        MQ1((MQ1)) --> ESP32
        MQ2((MQ2)) --> ESP32
        MQ..((MQ..)) --> ESP32
    end
    
    subgraph "Raspberry Pi"
        Broker[MQTT Broker]
        ESP32 -->|MQTT| Broker
        Broker <-->|MQTT| Server
    end

    subgraph Client
        Broker -->|MQTT| UI["User interface"]
    end

```
