import logging

from gui.constants import Attribute, PinShape
from links.azure_iot_central.link import AzureIoTCentral
from links.azure_iot_hub.link import AzureIoTHub
from links.azure_iot_hub_dps.link import AzureIoTHubDPS
from nodes.edge_ai_pipeline.base import BaseNode

try:
    import dearpygui.dearpygui as dpg
except ImportError:
    pass


class EdgeAINode(BaseNode):
    def __init__(self, settings, logger=logging.getLogger(__name__)):
        self.version = "0.1.0"
        self.name = "Azure IoT Message"
        self.theme_titlebar = [102, 0, 102]
        self.theme_titlebar_selected = [153, 0, 153]
        self.settings = settings
        self.logger = logger
        self.configs = {}
        self.configs["links"] = {
            "Azure IoT Central": AzureIoTCentral,
            "Azure IoT Hub": AzureIoTHub,
            "Azure IoT Hub DPS": AzureIoTHubDPS,
        }
        self.configs["instances"] = {}
        self.configs["label_connect"] = "Connect"
        self.configs["label_connected"] = "Connected"
        self.forms = {}
        self.forms["connect"] = {}

    def add_node(self, parent, node_id, pos):
        # Describe node attribute tags
        dpg_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        dpg_pin_tags = self.get_tag_list(dpg_node_tag)
        self.forms["connect"][dpg_node_tag] = self.configs["label_connect"]

        if self.settings["gui"]:
            # Add a Popup window
            with dpg.window(
                label="Connection Failure",
                modal=True,
                show=False,
                width=200,
                pos=[200, 200],
                tag=dpg_node_tag + ":modal",
            ):
                dpg.add_button(
                    label="OK",
                    width=-1,
                    callback=lambda: dpg.configure_item(
                        dpg_node_tag + ":modal", show=False
                    ),
                )

            # Add a node to a node editor
            with dpg.node(
                tag=dpg_node_tag, parent=parent, label=self.name, pos=pos
            ) as dpg_node:
                # Set node color
                with dpg.theme() as dpg_theme:
                    with dpg.theme_component(dpg.mvNode):
                        dpg.add_theme_color(
                            dpg.mvNodeCol_TitleBar,
                            self.theme_titlebar,
                            category=dpg.mvThemeCat_Nodes,
                        )
                        dpg.add_theme_color(
                            dpg.mvNodeCol_TitleBarHovered,
                            self.theme_titlebar_selected,
                            category=dpg.mvThemeCat_Nodes,
                        )
                        dpg.add_theme_color(
                            dpg.mvNodeCol_TitleBarSelected,
                            self.theme_titlebar_selected,
                            category=dpg.mvThemeCat_Nodes,
                        )
                        dpg.add_theme_color(
                            dpg.mvNodeCol_NodeOutline,
                            self.theme_titlebar,
                            category=dpg.mvThemeCat_Nodes,
                        )
                        dpg.bind_item_theme(dpg_node, dpg_theme)

                # Add pins that allows linking inputs and outputs
                with dpg.node_attribute(
                    attribute_type=int(Attribute.INPUT),
                    shape=int(PinShape.QUAD),
                    tag=dpg_pin_tags[self.MESSAGE_IN],
                ):
                    dpg.add_text("MESSAGE IN")

                # Add a combo dropdown that allows selecting service link
                with dpg.node_attribute(attribute_type=int(Attribute.STATIC)):
                    dpg.add_spacer(height=5)
                    dpg.add_combo(
                        list(self.configs["links"].keys()),
                        default_value=list(self.configs["links"].keys())[0],
                        width=self.settings["node_width"],
                        callback=self.callback_combo_link,
                        user_data=dpg_node_tag,
                        tag=dpg_node_tag + ":link",
                    )

                # Add inputs for credentials
                with dpg.node_attribute(attribute_type=int(Attribute.STATIC)):
                    dpg.add_input_text(
                        label="Host",
                        no_spaces=True,
                        width=self.settings["node_width"] - 50,
                        show=False,
                        tag=dpg_node_tag + ":host",
                    )
                    with dpg.tooltip(dpg_node_tag + ":host"):
                        dpg.add_text(
                            "Provisioning Host",
                            show=False,
                            tag=dpg_node_tag + ":host:tooltip",
                        )
                    dpg.add_input_text(
                        label="Scope",
                        no_spaces=True,
                        width=self.settings["node_width"] - 50,
                        tag=dpg_node_tag + ":scope",
                    )
                    with dpg.tooltip(dpg_node_tag + ":scope"):
                        dpg.add_text(
                            "ID Scope",
                            tag=dpg_node_tag + ":scope:tooltip",
                        )
                    dpg.add_input_text(
                        label="ID",
                        no_spaces=True,
                        width=self.settings["node_width"] - 50,
                        tag=dpg_node_tag + ":rid",
                    )
                    with dpg.tooltip(dpg_node_tag + ":rid"):
                        dpg.add_text(
                            "Registration ID",
                            tag=dpg_node_tag + ":rid:tooltip",
                        )
                    dpg.add_input_text(
                        label="Key",
                        no_spaces=True,
                        width=self.settings["node_width"] - 50,
                        tag=dpg_node_tag + ":key",
                    )
                    with dpg.tooltip(dpg_node_tag + ":key"):
                        dpg.add_text(
                            "Symmetric Key",
                            tag=dpg_node_tag + ":key:tooltip",
                        )
                    dpg.add_input_text(
                        label="String",
                        no_spaces=True,
                        width=self.settings["node_width"] - 50,
                        show=False,
                        tag=dpg_node_tag + ":string",
                    )
                    with dpg.tooltip(dpg_node_tag + ":string"):
                        dpg.add_text(
                            "Connection String",
                            show=False,
                            tag=dpg_node_tag + ":string:tooltip",
                        )

                # Add a button for publishing
                with dpg.node_attribute(attribute_type=int(Attribute.STATIC)):
                    dpg.add_button(
                        label=self.forms["connect"][dpg_node_tag],
                        width=self.settings["node_width"],
                        callback=self.callback_button_connect,
                        user_data=dpg_node_tag,
                        tag=dpg_node_tag + ":connect",
                    )

        # Return Dear PyGui Tag
        return dpg_node_tag

    async def refresh(self, node_id, node_links, node_frames, node_messages):
        dpg_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        message = None

        # Get linked node tag
        for link in node_links:
            link_pin_shape = link[0].split(":")[2]
            if link_pin_shape == str(int(PinShape.QUAD)):
                linked_node_tag_message = ":".join(link[0].split(":")[:2])
                message = node_messages.get(linked_node_tag_message, None)

        # Publish message
        if message is not None:
            if self.forms["connect"][dpg_node_tag] == self.configs["label_connected"]:
                if dpg_node_tag in self.configs["instances"]:
                    self.configs["instances"][dpg_node_tag].send_message(message)

        # Return frame and message
        return None, None

    def close(self, node_id):
        dpg_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        if dpg_node_tag in self.configs["instances"]:
            self.configs["instances"][dpg_node_tag].release()

    def delete(self, node_id):
        dpg_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        if self.settings["gui"]:
            dpg.delete_item(dpg_node_tag + ":modal")
            dpg.delete_item(dpg_node_tag)

    def get_export_params(self, node_id):
        dpg_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        params = {}
        if self.settings["gui"]:
            params["version"] = self.version
            params["position"] = dpg.get_item_pos(dpg_node_tag)
            params["link"] = dpg.get_value(dpg_node_tag + ":link")
            if params["link"] == "Azure IoT Central":
                params["scope"] = dpg.get_value(dpg_node_tag + ":scope")
                params["rid"] = dpg.get_value(dpg_node_tag + ":rid")
                params["key"] = dpg.get_value(dpg_node_tag + ":key")
            elif params["link"] == "Azure IoT Hub":
                params["string"] = dpg.get_value(dpg_node_tag + ":string")
            elif params["link"] == "Azure IoT Hub DPS":
                params["host"] = dpg.get_value(dpg_node_tag + ":host")
                params["scope"] = dpg.get_value(dpg_node_tag + ":scope")
                params["rid"] = dpg.get_value(dpg_node_tag + ":rid")
                params["key"] = dpg.get_value(dpg_node_tag + ":key")
        return params

    def set_import_params(self, node_id, params):
        dpg_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        if self.settings["gui"]:
            if "link" in params:
                dpg.set_value(dpg_node_tag + ":link", params["link"])
            if "scope" in params:
                dpg.set_value(dpg_node_tag + ":scope", params["scope"])
            if "rid" in params:
                dpg.set_value(dpg_node_tag + ":rid", params["rid"])
            if "key" in params:
                dpg.set_value(dpg_node_tag + ":key", params["key"])
            if "string" in params:
                dpg.set_value(dpg_node_tag + ":string", params["string"])
            if "host" in params:
                dpg.set_value(dpg_node_tag + ":host", params["host"])

    def callback_combo_link(self, sender, data, user_data):
        dpg_node_tag = user_data
        if dpg.get_value(dpg_node_tag + ":link") == "Azure IoT Central":
            dpg.hide_item(dpg_node_tag + ":host")
            dpg.hide_item(dpg_node_tag + ":host:tooltip")
            dpg.show_item(dpg_node_tag + ":scope")
            dpg.show_item(dpg_node_tag + ":scope:tooltip")
            dpg.show_item(dpg_node_tag + ":rid")
            dpg.show_item(dpg_node_tag + ":rid:tooltip")
            dpg.show_item(dpg_node_tag + ":key")
            dpg.show_item(dpg_node_tag + ":key:tooltip")
            dpg.hide_item(dpg_node_tag + ":string")
            dpg.hide_item(dpg_node_tag + ":string:tooltip")
        elif dpg.get_value(dpg_node_tag + ":link") == "Azure IoT Hub":
            dpg.hide_item(dpg_node_tag + ":host")
            dpg.hide_item(dpg_node_tag + ":host:tooltip")
            dpg.hide_item(dpg_node_tag + ":scope")
            dpg.hide_item(dpg_node_tag + ":scope:tooltip")
            dpg.hide_item(dpg_node_tag + ":rid")
            dpg.hide_item(dpg_node_tag + ":rid:tooltip")
            dpg.hide_item(dpg_node_tag + ":key")
            dpg.hide_item(dpg_node_tag + ":key:tooltip")
            dpg.show_item(dpg_node_tag + ":string")
            dpg.show_item(dpg_node_tag + ":string:tooltip")
        elif dpg.get_value(dpg_node_tag + ":link") == "Azure IoT Hub DPS":
            dpg.show_item(dpg_node_tag + ":host")
            dpg.show_item(dpg_node_tag + ":host:tooltip")
            dpg.show_item(dpg_node_tag + ":scope")
            dpg.show_item(dpg_node_tag + ":scope:tooltip")
            dpg.show_item(dpg_node_tag + ":rid")
            dpg.show_item(dpg_node_tag + ":rid:tooltip")
            dpg.show_item(dpg_node_tag + ":key")
            dpg.show_item(dpg_node_tag + ":key:tooltip")
            dpg.hide_item(dpg_node_tag + ":string")
            dpg.hide_item(dpg_node_tag + ":string:tooltip")

    def callback_button_connect(self, sender, data, user_data):
        dpg_node_tag = user_data
        if self.forms["connect"][dpg_node_tag] == self.configs["label_connect"]:
            if dpg_node_tag not in self.configs["instances"]:
                link_class = self.configs["links"][
                    dpg.get_value(dpg_node_tag + ":link")
                    if dpg.does_item_exist(dpg_node_tag + ":link")
                    else None
                ]
                dpg.set_item_label(dpg_node_tag + ":connect", "...")
                self.configs["instances"][dpg_node_tag] = link_class()
                if dpg.get_value(dpg_node_tag + ":link") == "Azure IoT Central":
                    self.configs["instances"][dpg_node_tag].connect(
                        registration_id=dpg.get_value(dpg_node_tag + ":rid"),
                        id_scope=dpg.get_value(dpg_node_tag + ":scope"),
                        symmetric_key=dpg.get_value(dpg_node_tag + ":key"),
                    )
                elif dpg.get_value(dpg_node_tag + ":link") == "Azure IoT Hub":
                    self.configs["instances"][dpg_node_tag].connect(
                        connection_string=dpg.get_value(dpg_node_tag + ":string")
                    )
                elif dpg.get_value(dpg_node_tag + ":link") == "Azure IoT Hub DPS":
                    self.configs["instances"][dpg_node_tag].connect(
                        provisioning_host=dpg.get_value(dpg_node_tag + ":host"),
                        registration_id=dpg.get_value(dpg_node_tag + ":rid"),
                        id_scope=dpg.get_value(dpg_node_tag + ":scope"),
                        symmetric_key=dpg.get_value(dpg_node_tag + ":key"),
                    )
            if self.configs["instances"][dpg_node_tag].device_client is not None:
                dpg.set_item_label(
                    dpg_node_tag + ":connect", self.configs["label_connected"]
                )
                dpg.disable_item(dpg_node_tag + ":link")
                self.forms["connect"][dpg_node_tag] = self.configs["label_connected"]
            else:
                del self.configs["instances"][dpg_node_tag]
                dpg.set_item_label(
                    dpg_node_tag + ":connect", self.configs["label_connect"]
                )
                self.forms["connect"][dpg_node_tag] = self.configs["label_connect"]
                dpg.show_item(dpg_node_tag + ":modal")
        elif self.forms["connect"][dpg_node_tag] == self.configs["label_connected"]:
            self.configs["instances"][dpg_node_tag].release()
            del self.configs["instances"][dpg_node_tag]
            dpg.set_item_label(dpg_node_tag + ":connect", self.configs["label_connect"])
            dpg.enable_item(dpg_node_tag + ":link")
