#!/usr/bin/env python
import argparse
import io
import json
import random
import sys
import time

import cv2 as cv
import paho.mqtt.client as mqtt
from PIL import Image


class MQTTClient:
    client = None
    host = None
    port = None
    client_id = None
    username = None
    password = None
    topic = None
    is_connected = False

    def __init__(self, host, port, client_id, username, password, topic):
        self.host = host
        try:
            self.port = int(port) if isinstance(port, str) else port
        except ValueError:
            self.port = 0
        self.client_id = client_id
        self.username = username
        self.password = password
        self.topic = topic

    def on_connect(self, client, userdata, flags, rc):
        if rc == 0:
            self.is_connected = True

    def on_disconnect(self, client, userdata, rc):
        self.is_connected = False

    def connect(self):
        self.client = mqtt.Client(
            client_id=self.client_id,
            clean_session=True,
            userdata=None,
            protocol=mqtt.MQTTv311,
            transport="tcp",
        )
        self.client.username_pw_set(username=self.username, password=self.password)
        self.client.on_connect = self.on_connect
        self.client.on_disconnect = self.on_disconnect
        try:
            self.client.loop_start()
            self.client.connect(self.host, self.port)
            for _ in range(10):
                if not self.is_connected:
                    time.sleep(1)
        except:
            pass

    def release(self):
        self.client.loop_stop()
        self.client.disconnect()
        self.client = None

    def subscribe(self):
        if self.is_connected:
            self.client.subscribe(self.topic)

    def publish_message(self, message):
        if self.is_connected:
            message = json.dumps(message)
            self.client.publish(topic=self.topic, payload=message)

    def publish_image(self, image):
        if self.is_connected:
            image = cv.cvtColor(image, cv.COLOR_BGR2RGB)
            image = Image.fromarray(image)
            image_binary = io.BytesIO()
            image.save(image_binary, format="png")
            self.client.publish(topic=self.topic, payload=image_binary.getvalue())


if __name__ == "__main__":
    TEMPERATURE = 20.0
    HUMIDITY = 60.0
    MESSAGE_TEXT = '{{"temperature": {temperature}, "humidity": {humidity}}}'

    # Arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--camera", help="Camera No", type=int, default=0)
    parser.add_argument("--width", help="Camera Width", type=int, default=1280)
    parser.add_argument("--height", help="Camera Height", type=int, default=780)
    parser.add_argument("--host", help="Broker Host", default="")
    parser.add_argument("--port", help="Broker Port", type=int, default=1883)
    parser.add_argument("--client_id", help="Client ID", default="")
    parser.add_argument("--username", help="Username", default="")
    parser.add_argument("--password", help="Password", default="")
    parser.add_argument("--topic", help="Topic", default="")
    parser.add_argument("--count", help="Message Count", type=int, default=5)
    parser.add_argument("--use_camera", action="store_true")
    args = parser.parse_args()

    # USB Camera
    if args.use_camera:
        cap = cv.VideoCapture(args.camera)
        cap.set(cv.CAP_PROP_FRAME_WIDTH, args.width)
        cap.set(cv.CAP_PROP_FRAME_HEIGHT, args.height)

    # Link service
    service = MQTTClient(
        host=args.host,
        port=args.port,
        client_id=args.client_id,
        username=args.username,
        password=args.password,
        topic=args.topic,
    )
    service.connect()
    if not service.is_connected:
        print("ConnectionError")
        sys.exit(1)

    # Send messages
    if args.use_camera:
        while cap.isOpened():
            ret, frame = cap.read()
            if not ret:
                break
            key = cv.waitKey(1) & 0xFF
            if key == ord("q"):
                break
            elif key == ord("p"):
                service.publish_image(frame)
                print("Published.")
            cv.imshow("Testing model - Prediction:p, Quit:q", frame)
        cap.release()
        cv.destroyAllWindows()
    else:
        for i in range(0, args.count):
            print("sending message #" + str(i + 1))
            temperature = TEMPERATURE + (random.random() * 15)
            humidity = HUMIDITY + (random.random() * 20)
            message = MESSAGE_TEXT.format(temperature=temperature, humidity=humidity)
            service.publish_message(message)
            time.sleep(1)

    # Release
    service.release()
