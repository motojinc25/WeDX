import json
import os

import dearpygui.dearpygui as dpg
from azure.iot.device import MethodResponse

from links.azure_iot_central.link import AzureIoCentral
from links.azure_iot_hub.link import AzureIoTHub
from links.azure_iot_hub_dps.link import AzureIoTHubDPS


class UserSettingsWindow:
    dpg_window_tag = "iot_device_setting_window"
    sys_settings = None
    tab_edge = None
    toolbar = None
    user_settings = None
    links = {}
    iot_device_instance = None
    settings_filepath = None

    def __init__(self, settings, tab_edge, toolbar):
        self.sys_settings = settings
        self.tab_edge = tab_edge
        self.toolbar = toolbar
        current_path = os.path.dirname(os.path.abspath(__file__))
        self.settings_filepath = os.path.abspath(
            os.path.join(current_path, "../.wedx/user.json")
        )
        if not os.path.exists(self.settings_filepath):
            with open(self.settings_filepath, "w") as fp:
                json.dump({}, fp, indent=2)
        with open(self.settings_filepath) as fp:
            self.user_settings = json.load(fp)
        self.links = {
            "Azure IoT Central": AzureIoCentral,
            "Azure IoT Hub": AzureIoTHub,
            "Azure IoT Hub DPS": AzureIoTHubDPS,
        }

    def create_widgets(self):
        # Add a Failure Popup window
        with dpg.window(
            label="Connection Failure",
            modal=True,
            show=False,
            width=200,
            pos=[200, 200],
            tag=self.dpg_window_tag + ":modal:failure",
        ):
            dpg.add_button(
                label="OK",
                width=-1,
                callback=lambda: dpg.configure_item(
                    self.dpg_window_tag + ":modal:failure", show=False
                ),
            )

        # Describe default values
        default_link = list(self.links.keys())[0]
        default_host = ""
        default_scope = ""
        default_rid = ""
        default_key = ""
        default_string = ""
        default_autoconnect = False
        if "iot_device" in self.user_settings:
            if "link" in self.user_settings["iot_device"]:
                for link in list(self.links.keys()):
                    if link == self.user_settings["iot_device"]["link"]:
                        default_link = link
            if "host" in self.user_settings["iot_device"]:
                default_host = self.user_settings["iot_device"]["host"]
            if "scope" in self.user_settings["iot_device"]:
                default_scope = self.user_settings["iot_device"]["scope"]
            if "rid" in self.user_settings["iot_device"]:
                default_rid = self.user_settings["iot_device"]["rid"]
            if "key" in self.user_settings["iot_device"]:
                default_key = self.user_settings["iot_device"]["key"]
            if "string" in self.user_settings["iot_device"]:
                default_string = self.user_settings["iot_device"]["string"]
            if "autoconnect" in self.user_settings["iot_device"]:
                default_autoconnect = self.user_settings["iot_device"]["autoconnect"]

        # Add a Success Popup window
        with dpg.window(
            label="Connection is successful",
            modal=True,
            show=False,
            width=200,
            pos=[200, 200],
            tag=self.dpg_window_tag + ":modal:success",
        ):
            dpg.add_button(
                label="OK",
                width=-1,
                callback=lambda: dpg.configure_item(
                    self.dpg_window_tag + ":modal:success", show=False
                ),
            )

        # Add an IoT device setting window
        width = 450
        with dpg.window(
            tag=self.dpg_window_tag,
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
                tag=self.dpg_window_tag + ":link",
            )

            # Add inputs for credentials
            dpg.add_input_text(
                label="Provisioning Host",
                no_spaces=True,
                width=width - 100,
                show=False,
                default_value=default_host,
                tag=self.dpg_window_tag + ":host",
            )
            dpg.add_input_text(
                label="ID Scope",
                no_spaces=True,
                width=width - 100,
                default_value=default_scope,
                tag=self.dpg_window_tag + ":scope",
            )
            dpg.add_input_text(
                label="Registration ID",
                no_spaces=True,
                width=width - 100,
                default_value=default_rid,
                tag=self.dpg_window_tag + ":rid",
            )
            dpg.add_input_text(
                label="Symmetric Key",
                no_spaces=True,
                width=width - 100,
                default_value=default_key,
                tag=self.dpg_window_tag + ":key",
            )
            dpg.add_input_text(
                label="Connection String",
                no_spaces=True,
                width=width - 100,
                show=False,
                default_value=default_string,
                tag=self.dpg_window_tag + ":string",
            )

            # Add a button for connecting
            dpg.add_separator()
            dpg.add_spacer(height=5)
            dpg.add_checkbox(
                label="Auto Connect",
                default_value=default_autoconnect,
                callback=self.callback_auto_connect,
                tag=self.dpg_window_tag + ":autoconnect",
            )
            with dpg.group(horizontal=True):
                dpg.add_button(
                    label="Connect",
                    width=340,
                    callback=self.callback_button_connect,
                    tag=self.dpg_window_tag + ":connect",
                )
                dpg.add_button(
                    label="Cancel",
                    width=100,
                    callback=lambda: dpg.configure_item(
                        self.dpg_window_tag, show=False
                    ),
                )

        # Connect IoT service
        if default_autoconnect:
            self.callback_combo_link(None, None, None)
            self.callback_button_connect(None, None, None)

        # Update link status
        self.toolbar.change_toolbar_link()

    def get_settings_data(self):
        settings_data = {
            "iot_device": {
                "link": dpg.get_value(self.dpg_window_tag + ":link"),
                "autoconnect": dpg.get_value(self.dpg_window_tag + ":autoconnect"),
            }
        }
        if dpg.get_value(self.dpg_window_tag + ":link") == "Azure IoT Central":
            settings_data["iot_device"]["scope"] = dpg.get_value(
                self.dpg_window_tag + ":scope"
            )
            settings_data["iot_device"]["rid"] = dpg.get_value(
                self.dpg_window_tag + ":rid"
            )
            settings_data["iot_device"]["key"] = dpg.get_value(
                self.dpg_window_tag + ":key"
            )
        elif dpg.get_value(self.dpg_window_tag + ":link") == "Azure IoT Hub":
            settings_data["iot_device"]["string"] = dpg.get_value(
                self.dpg_window_tag + ":string"
            )
        elif dpg.get_value(self.dpg_window_tag + ":link") == "Azure IoT Hub DPS":
            settings_data["iot_device"]["host"] = dpg.get_value(
                self.dpg_window_tag + ":host"
            )
            settings_data["iot_device"]["scope"] = dpg.get_value(
                self.dpg_window_tag + ":scope"
            )
            settings_data["iot_device"]["rid"] = dpg.get_value(
                self.dpg_window_tag + ":rid"
            )
            settings_data["iot_device"]["key"] = dpg.get_value(
                self.dpg_window_tag + ":key"
            )
        return settings_data

    def callback_auto_connect(self, sender, data, user_data):
        if dpg.get_value(self.dpg_window_tag + ":autoconnect"):
            if dpg.get_item_label(self.dpg_window_tag + ":connect") == "Connected":
                settings_data = self.get_settings_data()
                with open(self.settings_filepath, "w") as fp:
                    json.dump(settings_data, fp, indent=2)
        else:
            with open(self.settings_filepath, "w") as fp:
                json.dump({}, fp, indent=2)

    def callback_combo_link(self, sender, data, user_data):
        if dpg.get_value(self.dpg_window_tag + ":link") == "Azure IoT Central":
            dpg.hide_item(self.dpg_window_tag + ":host")
            dpg.show_item(self.dpg_window_tag + ":scope")
            dpg.show_item(self.dpg_window_tag + ":rid")
            dpg.show_item(self.dpg_window_tag + ":key")
            dpg.hide_item(self.dpg_window_tag + ":string")
        elif dpg.get_value(self.dpg_window_tag + ":link") == "Azure IoT Hub":
            dpg.hide_item(self.dpg_window_tag + ":host")
            dpg.hide_item(self.dpg_window_tag + ":scope")
            dpg.hide_item(self.dpg_window_tag + ":rid")
            dpg.hide_item(self.dpg_window_tag + ":key")
            dpg.show_item(self.dpg_window_tag + ":string")
        elif dpg.get_value(self.dpg_window_tag + ":link") == "Azure IoT Hub DPS":
            dpg.show_item(self.dpg_window_tag + ":host")
            dpg.show_item(self.dpg_window_tag + ":scope")
            dpg.show_item(self.dpg_window_tag + ":rid")
            dpg.show_item(self.dpg_window_tag + ":key")
            dpg.hide_item(self.dpg_window_tag + ":string")

    def callback_button_connect(self, sender, data, user_data):
        if dpg.get_item_label(self.dpg_window_tag + ":connect") == "Connect":
            if self.iot_device_instance is None:
                link_class = self.links[
                    dpg.get_value(self.dpg_window_tag + ":link")
                    if dpg.does_item_exist(self.dpg_window_tag + ":link")
                    else None
                ]
                dpg.set_item_label(self.dpg_window_tag + ":connect", "...")
                self.iot_device_instance = link_class()
                if dpg.get_value(self.dpg_window_tag + ":link") == "Azure IoT Central":
                    self.iot_device_instance.connect(
                        registration_id=dpg.get_value(self.dpg_window_tag + ":rid"),
                        id_scope=dpg.get_value(self.dpg_window_tag + ":scope"),
                        symmetric_key=dpg.get_value(self.dpg_window_tag + ":key"),
                    )
                elif dpg.get_value(self.dpg_window_tag + ":link") == "Azure IoT Hub":
                    self.iot_device_instance.connect(
                        connection_string=dpg.get_value(self.dpg_window_tag + ":string")
                    )
                elif (
                    dpg.get_value(self.dpg_window_tag + ":link") == "Azure IoT Hub DPS"
                ):
                    self.iot_device_instance.connect(
                        provisioning_host=dpg.get_value(self.dpg_window_tag + ":host"),
                        registration_id=dpg.get_value(self.dpg_window_tag + ":rid"),
                        id_scope=dpg.get_value(self.dpg_window_tag + ":scope"),
                        symmetric_key=dpg.get_value(self.dpg_window_tag + ":key"),
                    )
            if self.iot_device_instance.device_client is not None:
                dpg.set_item_label(self.dpg_window_tag + ":connect", "Connected")
                dpg.disable_item(self.dpg_window_tag + ":link")
                dpg.show_item(self.dpg_window_tag + ":modal:success")
                dpg.configure_item(self.dpg_window_tag, show=False)
                self.sys_settings[
                    "iot_device_instance"
                ] = self.iot_device_instance
                self.iot_device_instance.device_client.on_method_request_received = (
                    self.method_request_handler
                )
                if dpg.get_value(self.dpg_window_tag + ":autoconnect"):
                    settings_data = self.get_settings_data()
                    with open(self.settings_filepath, "w") as fp:
                        json.dump(settings_data, fp, indent=2)
            else:
                del self.iot_device_instance
                dpg.set_item_label(self.dpg_window_tag + ":connect", "Connect")
                dpg.show_item(self.dpg_window_tag + ":modal:failure")
        elif dpg.get_item_label(self.dpg_window_tag + ":connect") == "Connected":
            self.iot_device_instance.release()
            del self.iot_device_instance
            del self.sys_settings["iot_device_instance"]
            dpg.set_item_label(self.dpg_window_tag + ":connect", "Connect")
            dpg.enable_item(self.dpg_window_tag + ":link")

        # Update link status
        self.toolbar.change_toolbar_link()

    # Define a handler to request method
    def method_request_handler(self, method_request):
        status = 200
        payload = {}
        if method_request.name == "startPipeline":
            self.toolbar.change_toolbar_start()
        elif method_request.name == "stopPipeline":
            self.toolbar.change_toolbar_stop()
        elif method_request.name == "importPipeline":
            import_data = method_request.payload
            self.tab_edge.new_pipeline()
            self.tab_edge.import_pipeline(import_data)
        elif method_request.name == "exportPipeline":
            export_data = self.tab_edge.export_pipeline()
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
            self.iot_device_instance.device_client.shutdown()
