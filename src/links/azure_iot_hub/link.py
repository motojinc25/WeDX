#!/usr/bin/env python
import argparse
import json
import random
import sys
import time

from azure.iot.device import IoTHubDeviceClient, Message


class AzureIoTHub:
    device_client = None

    def __init__(self):
        pass

    def connect(self, connection_string):
        try:
            self.device_client = IoTHubDeviceClient.create_from_connection_string(
                connection_string
            )
            self.device_client.connect()
        except:
            self.device_client = None

    def send_message(self, message):
        if self.device_client is not None:
            message = json.dumps(message)
            message = Message(message)
            message.content_encoding = "utf-8"
            message.content_type = "application/json"
            try:
                self.device_client.send_message(message)
            except:
                self.device_client = None

    def release(self):
        if self.device_client is not None:
            try:
                self.device_client.disconnect()
            except:
                pass
            self.device_client = None


if __name__ == "__main__":
    TEMPERATURE = 20.0
    HUMIDITY = 60.0
    MESSAGE_TEXT = '{{"temperature": {temperature}, "humidity": {humidity}}}'

    # Arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--connection_string", help="Connection String")
    parser.add_argument("--count", help="Message Count", type=int, default=5)
    args = parser.parse_args()

    # Link service
    service = AzureIoTHub()
    service.connect(
        connection_string=args.connection_string,
    )
    if service.device_client is None:
        print("CredentialError")
        sys.exit(1)

    # Send messages
    for i in range(0, args.count):
        print("sending message #" + str(i + 1))
        temperature = TEMPERATURE + (random.random() * 15)
        humidity = HUMIDITY + (random.random() * 20)
        message = MESSAGE_TEXT.format(temperature=temperature, humidity=humidity)
        service.send_message(message=message)
        time.sleep(1)

    # Release
    service.release()
