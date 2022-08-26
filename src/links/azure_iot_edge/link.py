#!/usr/bin/env python
import argparse
import json
import random
import sys
import time
import uuid

from azure.iot.device import IoTHubModuleClient, Message


class AzureIoTEdge:
    module_client = None

    def __init__(self):
        pass

    def connect(self):
        try:
            self.module_client = IoTHubModuleClient.create_from_edge_environment()
        except:
            self.module_client = None

    def send_message(self, message):
        if self.module_client is not None:
            message = json.dumps(message)
            message = Message(message)
            message.message_id = uuid.uuid4()
            message.correlation_id = "correlation-1211"
            message.custom_properties["wedx"] = "yes"
            message.content_encoding = "utf-8"
            message.content_type = "application/json"
            try:
                self.module_client.send_message_to_output(message, "output1")
            except:
                self.module_client = None

    def release(self):
        if self.module_client is not None:
            try:
                self.module_client.shutdown()
            except:
                pass
            self.module_client = None


if __name__ == "__main__":
    TEMPERATURE = 20.0
    HUMIDITY = 60.0
    MESSAGE_TEXT = '{{"temperature": {temperature}, "humidity": {humidity}}}'

    # Arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", help="Message Count", type=int, default=5)
    args = parser.parse_args()

    # Link service
    service = AzureIoTEdge()
    service.connect()
    if service.module_client is None:
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
