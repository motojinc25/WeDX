import json
import logging
import os

from azure.iot.device import MethodResponse

from gui.constants import tag
from links.azure_iot_central.link import AzureIoTCentral
from links.azure_iot_hub.link import AzureIoTHub
from links.azure_iot_hub_dps.link import AzureIoTHubDPS

try:
    import dearpygui.dearpygui as dpg
except ImportError:
    pass


class UserPreferences:
    settings = None
    edge_ai_pipeline = None
    logger = None
    toolbar = None
    user_settings = None
    links = {}
    iot_device_instance = None
    settings_filepath = None

    def __init__(self, settings, edge_ai_pipeline, logger=logging.getLogger(__name__)):
        self.settings = settings
        self.edge_ai_pipeline = edge_ai_pipeline
        self.logger = logger
        current_path = os.path.dirname(os.path.abspath(__file__))
        self.settings_filepath = os.path.abspath(
            os.path.join(current_path, "../.wedx/preferences.json")
        )
        if not os.path.exists(self.settings_filepath):
            with open(self.settings_filepath, "w") as fp:
                json.dump({}, fp, indent=2)
        with open(self.settings_filepath) as fp:
            self.preferences = json.load(fp)
        self.links = {
            "Azure IoT Central": AzureIoTCentral,
            "Azure IoT Hub": AzureIoTHub,
            "Azure IoT Hub DPS": AzureIoTHubDPS,
        }
        if not settings["gui"]:
            service = os.environ.get("SERVICE")
            self.preferences = {
                "iot_device": {
                    "link": list(self.links)[int(service)]
                    if service is not None
                    else None,
                    "host": os.environ.get("HOST"),
                    "scope": os.environ.get("SCOPE"),
                    "rid": os.environ.get("RID"),
                    "key": os.environ.get("KEY"),
                    "string": os.environ.get("STRING"),
                    "autoconnect": True,
                }
            }

    def create_gui_widgets(self):
        # Describe default values
        default_link = list(self.links.keys())[0]
        default_host = ""
        default_scope = ""
        default_rid = ""
        default_key = ""
        default_string = ""
        default_autoconnect = False
        if "iot_device" in self.preferences:
            if "link" in self.preferences["iot_device"]:
                for link in list(self.links.keys()):
                    if link == self.preferences["iot_device"]["link"]:
                        default_link = link
            if "host" in self.preferences["iot_device"]:
                default_host = self.preferences["iot_device"]["host"]
            if "scope" in self.preferences["iot_device"]:
                default_scope = self.preferences["iot_device"]["scope"]
            if "rid" in self.preferences["iot_device"]:
                default_rid = self.preferences["iot_device"]["rid"]
            if "key" in self.preferences["iot_device"]:
                default_key = self.preferences["iot_device"]["key"]
            if "string" in self.preferences["iot_device"]:
                default_string = self.preferences["iot_device"]["string"]
            if "autoconnect" in self.preferences["iot_device"]:
                default_autoconnect = self.preferences["iot_device"]["autoconnect"]

        if self.settings["gui"]:
            # Add a Failure Popup window
            with dpg.window(
                label="Connection Failure",
                modal=True,
                show=False,
                width=200,
                pos=[200, 200],
                tag=tag["window"]["iot_device_setting"] + ":modal:failure",
            ):
                dpg.add_button(
                    label="OK",
                    width=-1,
                    callback=lambda: dpg.configure_item(
                        tag["window"]["iot_device_setting"] + ":modal:failure",
                        show=False,
                    ),
                )

            # Add a Success Popup window
            with dpg.window(
                label="Connection is successful",
                modal=True,
                show=False,
                width=200,
                pos=[200, 200],
                tag=tag["window"]["iot_device_setting"] + ":modal:success",
            ):
                dpg.add_button(
                    label="OK",
                    width=-1,
                    callback=lambda: dpg.configure_item(
                        tag["window"]["iot_device_setting"] + ":modal:success",
                        show=False,
                    ),
                )

            # Add an IoT device setting window
            width = 450
            with dpg.window(
                tag=tag["window"]["iot_device_setting"],
                label="Azure IoT Device",
                min_size=(width, 300),
                show=False,
                pos=(100, 100),
            ):
                # WeDX announcing
                dpg.add_text(
                    "WeDX can be turned into an IoT device and controlled from the cloud."
                )
                dpg.add_spacer(height=5)

                # Add a combo dropdown that allows selecting service link
                dpg.add_combo(
                    list(self.links.keys()),
                    default_value=default_link,
                    width=width,
                    callback=self.callback_combo_link,
                    tag=tag["window"]["iot_device_setting"] + ":link",
                )

                # Add inputs for credentials
                dpg.add_input_text(
                    label="Provisioning Host",
                    no_spaces=True,
                    width=width - 100,
                    show=False,
                    default_value=default_host,
                    tag=tag["window"]["iot_device_setting"] + ":host",
                )
                dpg.add_input_text(
                    label="ID Scope",
                    no_spaces=True,
                    width=width - 100,
                    default_value=default_scope,
                    tag=tag["window"]["iot_device_setting"] + ":scope",
                )
                dpg.add_input_text(
                    label="Registration ID",
                    no_spaces=True,
                    width=width - 100,
                    default_value=default_rid,
                    tag=tag["window"]["iot_device_setting"] + ":rid",
                )
                dpg.add_input_text(
                    label="Symmetric Key",
                    no_spaces=True,
                    width=width - 100,
                    default_value=default_key,
                    tag=tag["window"]["iot_device_setting"] + ":key",
                )
                dpg.add_input_text(
                    label="Connection String",
                    no_spaces=True,
                    width=width - 100,
                    show=False,
                    default_value=default_string,
                    tag=tag["window"]["iot_device_setting"] + ":string",
                )

                # Add a button for connecting
                dpg.add_separator()
                dpg.add_spacer(height=5)
                dpg.add_checkbox(
                    label="Auto Connect",
                    default_value=default_autoconnect,
                    callback=self.callback_auto_connect,
                    tag=tag["window"]["iot_device_setting"] + ":autoconnect",
                )
                with dpg.group(horizontal=True):
                    dpg.add_button(
                        label="Connect",
                        width=340,
                        callback=self.callback_button_connect,
                        tag=tag["window"]["iot_device_setting"] + ":connect",
                    )
                    dpg.add_button(
                        label="Cancel",
                        width=100,
                        callback=lambda: dpg.configure_item(
                            tag["window"]["iot_device_setting"], show=False
                        ),
                    )

            # Connect IoT service
            if default_autoconnect:
                self.callback_combo_link(None, None, None)
                self.callback_button_connect(None, None, None)

            # Update link status
            self.edge_ai_pipeline.change_toolbar_link()
        else:
            self.connect_iot_device()

    def get_settings_data(self):
        settings_data = {
            "iot_device": {
                "link": dpg.get_value(tag["window"]["iot_device_setting"] + ":link"),
                "autoconnect": dpg.get_value(
                    tag["window"]["iot_device_setting"] + ":autoconnect"
                ),
            }
        }
        if (
            dpg.get_value(tag["window"]["iot_device_setting"] + ":link")
            == "Azure IoT Central"
        ):
            settings_data["iot_device"]["scope"] = dpg.get_value(
                tag["window"]["iot_device_setting"] + ":scope"
            )
            settings_data["iot_device"]["rid"] = dpg.get_value(
                tag["window"]["iot_device_setting"] + ":rid"
            )
            settings_data["iot_device"]["key"] = dpg.get_value(
                tag["window"]["iot_device_setting"] + ":key"
            )
        elif (
            dpg.get_value(tag["window"]["iot_device_setting"] + ":link")
            == "Azure IoT Hub"
        ):
            settings_data["iot_device"]["string"] = dpg.get_value(
                tag["window"]["iot_device_setting"] + ":string"
            )
        elif (
            dpg.get_value(tag["window"]["iot_device_setting"] + ":link")
            == "Azure IoT Hub DPS"
        ):
            settings_data["iot_device"]["host"] = dpg.get_value(
                tag["window"]["iot_device_setting"] + ":host"
            )
            settings_data["iot_device"]["scope"] = dpg.get_value(
                tag["window"]["iot_device_setting"] + ":scope"
            )
            settings_data["iot_device"]["rid"] = dpg.get_value(
                tag["window"]["iot_device_setting"] + ":rid"
            )
            settings_data["iot_device"]["key"] = dpg.get_value(
                tag["window"]["iot_device_setting"] + ":key"
            )
        return settings_data

    def callback_auto_connect(self, sender, data, user_data):
        if dpg.get_value(tag["window"]["iot_device_setting"] + ":autoconnect"):
            if (
                dpg.get_item_label(tag["window"]["iot_device_setting"] + ":connect")
                == "Connected"
            ):
                settings_data = self.get_settings_data()
                with open(self.settings_filepath, "w") as fp:
                    json.dump(settings_data, fp, indent=2)
        else:
            with open(self.settings_filepath, "w") as fp:
                json.dump({}, fp, indent=2)

    def callback_combo_link(self, sender, data, user_data):
        if (
            dpg.get_value(tag["window"]["iot_device_setting"] + ":link")
            == "Azure IoT Central"
        ):
            dpg.hide_item(tag["window"]["iot_device_setting"] + ":host")
            dpg.show_item(tag["window"]["iot_device_setting"] + ":scope")
            dpg.show_item(tag["window"]["iot_device_setting"] + ":rid")
            dpg.show_item(tag["window"]["iot_device_setting"] + ":key")
            dpg.hide_item(tag["window"]["iot_device_setting"] + ":string")
        elif (
            dpg.get_value(tag["window"]["iot_device_setting"] + ":link")
            == "Azure IoT Hub"
        ):
            dpg.hide_item(tag["window"]["iot_device_setting"] + ":host")
            dpg.hide_item(tag["window"]["iot_device_setting"] + ":scope")
            dpg.hide_item(tag["window"]["iot_device_setting"] + ":rid")
            dpg.hide_item(tag["window"]["iot_device_setting"] + ":key")
            dpg.show_item(tag["window"]["iot_device_setting"] + ":string")
        elif (
            dpg.get_value(tag["window"]["iot_device_setting"] + ":link")
            == "Azure IoT Hub DPS"
        ):
            dpg.show_item(tag["window"]["iot_device_setting"] + ":host")
            dpg.show_item(tag["window"]["iot_device_setting"] + ":scope")
            dpg.show_item(tag["window"]["iot_device_setting"] + ":rid")
            dpg.show_item(tag["window"]["iot_device_setting"] + ":key")
            dpg.hide_item(tag["window"]["iot_device_setting"] + ":string")

    def connect_iot_device(self):
        if (
            "iot_device" in self.preferences
            and self.preferences["iot_device"]["link"] is not None
        ):
            link_class = self.links[self.preferences["iot_device"]["link"]]
            self.iot_device_instance = link_class()
            if self.preferences["iot_device"]["link"] == "Azure IoT Central":
                self.iot_device_instance.connect(
                    registration_id=self.preferences["iot_device"]["rid"],
                    id_scope=self.preferences["iot_device"]["scope"],
                    symmetric_key=self.preferences["iot_device"]["key"],
                )
                self.logger.debug("Connect to Azure IoT Central")
            elif self.preferences["iot_device"]["link"] == "Azure IoT Hub":
                self.iot_device_instance.connect(
                    connection_string=self.preferences["iot_device"]["string"],
                )
                self.logger.debug("Connect to Azure IoT Hub")
            elif self.preferences["iot_device"]["link"] == "Azure IoT Hub DPS":
                self.iot_device_instance.connect(
                    provisioning_host=self.preferences["iot_device"]["host"],
                    registration_id=self.preferences["iot_device"]["rid"],
                    id_scope=self.preferences["iot_device"]["scope"],
                    symmetric_key=self.preferences["iot_device"]["key"],
                )
                self.logger.debug("Connect to Azure IoT Hub DPS")
            if self.iot_device_instance.device_client is not None:
                self.settings["iot_device_instance"] = self.iot_device_instance
                self.iot_device_instance.device_client.on_method_request_received = (
                    self.method_request_handler
                )
                self.logger.debug("Receive a method request")
            else:
                self.logger.debug("Not Connected")

    def callback_button_connect(self, sender, data, user_data):
        if (
            dpg.get_item_label(tag["window"]["iot_device_setting"] + ":connect")
            == "Connect"
        ):
            if self.iot_device_instance is None:
                link_class = self.links[
                    dpg.get_value(tag["window"]["iot_device_setting"] + ":link")
                    if dpg.does_item_exist(
                        tag["window"]["iot_device_setting"] + ":link"
                    )
                    else None
                ]
                dpg.set_item_label(
                    tag["window"]["iot_device_setting"] + ":connect", "..."
                )
                self.iot_device_instance = link_class()
                if (
                    dpg.get_value(tag["window"]["iot_device_setting"] + ":link")
                    == "Azure IoT Central"
                ):
                    self.iot_device_instance.connect(
                        registration_id=dpg.get_value(
                            tag["window"]["iot_device_setting"] + ":rid"
                        ),
                        id_scope=dpg.get_value(
                            tag["window"]["iot_device_setting"] + ":scope"
                        ),
                        symmetric_key=dpg.get_value(
                            tag["window"]["iot_device_setting"] + ":key"
                        ),
                    )
                elif (
                    dpg.get_value(tag["window"]["iot_device_setting"] + ":link")
                    == "Azure IoT Hub"
                ):
                    self.iot_device_instance.connect(
                        connection_string=dpg.get_value(
                            tag["window"]["iot_device_setting"] + ":string"
                        )
                    )
                elif (
                    dpg.get_value(tag["window"]["iot_device_setting"] + ":link")
                    == "Azure IoT Hub DPS"
                ):
                    self.iot_device_instance.connect(
                        provisioning_host=dpg.get_value(
                            tag["window"]["iot_device_setting"] + ":host"
                        ),
                        registration_id=dpg.get_value(
                            tag["window"]["iot_device_setting"] + ":rid"
                        ),
                        id_scope=dpg.get_value(
                            tag["window"]["iot_device_setting"] + ":scope"
                        ),
                        symmetric_key=dpg.get_value(
                            tag["window"]["iot_device_setting"] + ":key"
                        ),
                    )
            if self.iot_device_instance.device_client is not None:
                dpg.set_item_label(
                    tag["window"]["iot_device_setting"] + ":connect", "Connected"
                )
                dpg.disable_item(tag["window"]["iot_device_setting"] + ":link")
                dpg.show_item(tag["window"]["iot_device_setting"] + ":modal:success")
                dpg.configure_item(tag["window"]["iot_device_setting"], show=False)
                self.settings["iot_device_instance"] = self.iot_device_instance
                self.iot_device_instance.device_client.on_method_request_received = (
                    self.method_request_handler
                )
                if dpg.get_value(tag["window"]["iot_device_setting"] + ":autoconnect"):
                    settings_data = self.get_settings_data()
                    with open(self.settings_filepath, "w") as fp:
                        json.dump(settings_data, fp, indent=2)
            else:
                del self.iot_device_instance
                dpg.set_item_label(
                    tag["window"]["iot_device_setting"] + ":connect", "Connect"
                )
                dpg.show_item(tag["window"]["iot_device_setting"] + ":modal:failure")
        elif (
            dpg.get_item_label(tag["window"]["iot_device_setting"] + ":connect")
            == "Connected"
        ):
            self.iot_device_instance.release()
            del self.iot_device_instance
            del self.settings["iot_device_instance"]
            dpg.set_item_label(
                tag["window"]["iot_device_setting"] + ":connect", "Connect"
            )
            dpg.enable_item(tag["window"]["iot_device_setting"] + ":link")

        # Update link status
        self.edge_ai_pipeline.change_toolbar_link()

    # Define a handler to request method
    def method_request_handler(self, method_request):
        status = 200
        payload = {}
        if method_request.name == "startPipeline":
            self.logger.debug("Received startPipeline")
            self.edge_ai_pipeline.change_toolbar_start()
        elif method_request.name == "stopPipeline":
            self.logger.debug("Received stopPipeline")
            self.edge_ai_pipeline.change_toolbar_stop()
        elif method_request.name == "importPipeline":
            self.logger.debug("Received importPipeline")
            import_data = method_request.payload
            self.edge_ai_pipeline.new_pipeline()
            self.edge_ai_pipeline.import_pipeline(import_data)
        elif method_request.name == "exportPipeline":
            self.logger.debug("Received exportPipeline")
            export_data = self.edge_ai_pipeline.export_pipeline()
            payload = export_data
        else:
            payload = "unknown method"
            status = 400

        # Send the response
        method_response = MethodResponse.create_from_method_request(
            method_request, status, payload
        )
        self.iot_device_instance.device_client.send_method_response(method_response)

    def close(self):
        if self.iot_device_instance is not None:
            if self.iot_device_instance.device_client is not None:
                self.iot_device_instance.device_client.shutdown()
