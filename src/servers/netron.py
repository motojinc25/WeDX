import logging

import netron


class NetronServer:
    address = None

    def __init__(self, settings, logger=logging.getLogger(__name__)):
        self.settings = settings
        self.logger = logger
        self.address = netron.start(
            None, address=("0.0.0.0", self.settings["netron_port"]), browse=False
        )

    def reload(self, onnx_file):
        if self.address is not None:
            self.stop()
        self.address = netron.start(
            onnx_file, address=("0.0.0.0", self.settings["netron_port"]), browse=False
        )

    def stop(self):
        netron.stop(self.address)
