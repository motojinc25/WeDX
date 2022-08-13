#!/usr/bin/env python
import argparse
import asyncio
import json
import logging
import random

import zmq
from zmq.asyncio import Context


class MessageQueueReqRep:
    context = Context()
    logger = None

    def __init__(self, logger=logging.getLogger(__name__)):
        self.logger = logger

    async def server(self, edge_ai_pipeline, **kwargs):
        socket = self.context.socket(zmq.REP)
        if "port" not in kwargs:
            kwargs["port"] = 5555
        socket.bind("tcp://*:%s" % kwargs["port"])
        while True:
            request = await socket.recv_json()
            self.logger.debug("Received request: {}".format(request))
            response = "running"
            if request["method"] == "start_pipeline":
                edge_ai_pipeline.change_toolbar_start()
                response = "done"
            elif request["method"] == "stop_pipeline":
                edge_ai_pipeline.change_toolbar_stop()
                response = "done"
            elif request["method"] == "import_pipeline":
                edge_ai_pipeline.new_pipeline()
                edge_ai_pipeline.import_pipeline(request["payload"])
            elif request["method"] == "export_pipeline":
                response = edge_ai_pipeline.export_pipeline()
            await socket.send_json(response)

    async def client(self, **kwargs):
        socket = self.context.socket(zmq.REQ)
        if "port" not in kwargs:
            kwargs["port"] = 5555
        socket.connect("tcp://localhost:%s" % kwargs["port"])
        if "message" in kwargs:
            await socket.send_json(kwargs["message"])
            reply = await socket.recv_json()
            self.logger.debug("Received reply: {}".format(reply))
            return reply


async def test():
    TEMPERATURE = 20.0
    HUMIDITY = 60.0
    MESSAGE_TEXT = (
        '{{"method": "root", "temperature": {temperature}, "humidity": {humidity}}}'
    )

    # Arguments
    parser = argparse.ArgumentParser()
    parser.add_argument("--count", help="Message Count", type=int, default=5)
    args = parser.parse_args()

    # Logger
    logging.basicConfig(
        level=logging.DEBUG,
        format="%(asctime)s- %(name)s - %(levelname)s - %(message)s",
    )
    logger = logging.getLogger(__name__)

    # Link service
    service = MessageQueueReqRep(logger)
    asyncio.create_task(service.server(None))

    # Send messages
    for i in range(0, args.count):
        temperature = TEMPERATURE + (random.random() * 15)
        humidity = HUMIDITY + (random.random() * 20)
        message = MESSAGE_TEXT.format(temperature=temperature, humidity=humidity)
        await service.client(message=json.loads(message))


if __name__ == "__main__":
    asyncio.run(test())
