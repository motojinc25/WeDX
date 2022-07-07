#!/usr/bin/env python
import argparse
import json
import random
import sys
import time

from azure.iot.device import IoTHubDeviceClient, Message, ProvisioningDeviceClient


class AzureIoTHubDPS:
    device_client = None

    def __init__(self):
        pass

    def connect(
        self,
        id_scope,
        registration_id,
        symmetric_key,
        provisioning_host,
    ):
        try:
            provisioning_device_client = (
                ProvisioningDeviceClient.create_from_symmetric_key(
                    provisioning_host=provisioning_host,
                    registration_id=registration_id,
                    id_scope=id_scope,
                    symmetric_key=symmetric_key,
                )
            )
            registration_result = provisioning_device_client.register()
            if registration_result.status == "assigned":
                self.device_client = IoTHubDeviceClient.create_from_symmetric_key(
                    symmetric_key=symmetric_key,
                    hostname=registration_result.registration_state.assigned_hub,
                    device_id=registration_result.registration_state.device_id,
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
    parser.add_argument("--id_scope", help="ID Scope")
    parser.add_argument("--registration_id", help="Registration ID")
    parser.add_argument("--symmetric_key", help="Symmetric Key")
    parser.add_argument("--provisioning_host", help="Provisioning Host")
    parser.add_argument("--count", help="Message Count", type=int, default=5)
    args = parser.parse_args()

    # Link service
    service = AzureIoTHubDPS()
    service.connect(
        id_scope=args.id_scope,
        registration_id=args.registration_id,
        symmetric_key=args.symmetric_key,
        provisioning_host=args.provisioning_host,
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
