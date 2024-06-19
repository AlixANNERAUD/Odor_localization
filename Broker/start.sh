#!/bin/bash

apt install ufw

mkdir /mosquitto

cp ./mosquitto.conf /mosquitto/

ufw allow 1883 
ufw enable

docker compose up --remove-orphans -d