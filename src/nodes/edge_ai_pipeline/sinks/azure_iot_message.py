import dearpygui.dearpygui as dpg

from links.azure_iot_central.link import AzureIoCentral
from links.azure_iot_hub.link import AzureIoTHub
from links.azure_iot_hub_dps.link import AzureIoTHubDPS
from nodes.edge_ai_pipeline.base import BaseNode


class EdgeAINode(BaseNode):
    def __init__(self, settings):
        self.version = "0.1.0"
        self.name = "Azure IoT Message"
        self.settings = settings
        self.configs = {}
        self.configs["links"] = {
            "Azure IoT Central": AzureIoCentral,
            "Azure IoT Hub": AzureIoTHub,
            "Azure IoT Hub DPS": AzureIoTHubDPS,
        }
        self.configs["instances"] = {}
        self.configs["label_start"] = "Connect"
        self.configs["label_stop"] = "Connected"

    def add_node(self, parent, node_id, pos=[0, 0]):
        # Describe node attribute tags
        dag_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        dag_pin_tags = self.get_tag_list(dag_node_tag)

        # Add a Popup window
        with dpg.window(
            label="Connection Failure",
            modal=True,
            show=False,
            width=200,
            pos=[200, 200],
            tag=dag_node_tag + ":modal",
        ):
            dpg.add_button(
                label="OK",
                width=-1,
                callback=lambda: dpg.configure_item(
                    dag_node_tag + ":modal", show=False
                ),
            )

        # Add a node to a node editor
        with dpg.node(tag=dag_node_tag, parent=parent, label=self.name, pos=pos):
            # Add pins that allows linking inputs and outputs
            with dpg.node_attribute(
                attribute_type=dpg.mvNode_Attr_Input,
                shape=dpg.mvNode_PinShape_Quad,
                tag=dag_pin_tags[self.MESSAGE_IN],
            ):
                dpg.add_text("MESSAGE IN")

            # Add a combo dropdown that allows selecting service link
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static):
                dpg.add_spacer(height=5)
                dpg.add_combo(
                    list(self.configs["links"].keys()),
                    default_value=list(self.configs["links"].keys())[0],
                    width=self.settings["node_width"],
                    callback=self.callback_combo_link,
                    user_data=dag_node_tag,
                    tag=dag_node_tag + ":link",
                )

            # Add inputs for credentials
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static):
                dpg.add_input_text(
                    label="Host",
                    no_spaces=True,
                    width=self.settings["node_width"] - 50,
                    show=False,
                    tag=dag_node_tag + ":host",
                )
                with dpg.tooltip(dag_node_tag + ":host"):
                    dpg.add_text(
                        "Provisioning Host",
                        show=False,
                        tag=dag_node_tag + ":host:tooltip",
                    )
                dpg.add_input_text(
                    label="Scope",
                    no_spaces=True,
                    width=self.settings["node_width"] - 50,
                    tag=dag_node_tag + ":scope",
                )
                with dpg.tooltip(dag_node_tag + ":scope"):
                    dpg.add_text(
                        "ID Scope",
                        tag=dag_node_tag + ":scope:tooltip",
                    )
                dpg.add_input_text(
                    label="ID",
                    no_spaces=True,
                    width=self.settings["node_width"] - 50,
                    tag=dag_node_tag + ":rid",
                )
                with dpg.tooltip(dag_node_tag + ":rid"):
                    dpg.add_text(
                        "Registration ID",
                        tag=dag_node_tag + ":rid:tooltip",
                    )
                dpg.add_input_text(
                    label="Key",
                    no_spaces=True,
                    width=self.settings["node_width"] - 50,
                    tag=dag_node_tag + ":key",
                )
                with dpg.tooltip(dag_node_tag + ":key"):
                    dpg.add_text(
                        "Symmetric Key",
                        tag=dag_node_tag + ":key:tooltip",
                    )
                dpg.add_input_text(
                    label="String",
                    no_spaces=True,
                    width=self.settings["node_width"] - 50,
                    show=False,
                    tag=dag_node_tag + ":string",
                )
                with dpg.tooltip(dag_node_tag + ":string"):
                    dpg.add_text(
                        "Connection String",
                        show=False,
                        tag=dag_node_tag + ":string:tooltip",
                    )

            # Add a button for publishing
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static):
                dpg.add_button(
                    label=self.configs["label_start"],
                    width=self.settings["node_width"],
                    callback=self.callback_button_connect,
                    user_data=dag_node_tag,
                    tag=dag_node_tag + ":connect",
                )

        # Return Dear PyGui Tag
        return dag_node_tag

    def update(self, node_id, node_links, node_frames, node_messages):
        dag_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        message = None

        # Get linked node tag
        for link in node_links:
            link_pin_shape = link[0].split(":")[2]
            if link_pin_shape == str(dpg.mvNode_PinShape_Quad):
                linked_node_tag_message = ":".join(link[0].split(":")[:2])
                message = node_messages.get(linked_node_tag_message, None)

        # Publish message
        if message is not None:
            if (
                dpg.get_item_label(dag_node_tag + ":connect")
                == self.configs["label_stop"]
            ):
                if dag_node_tag in self.configs["instances"]:
                    self.configs["instances"][dag_node_tag].send_message(message)

        # Return frame and message
        return None, None

    def close(self, node_id):
        dag_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        if dag_node_tag in self.configs["instances"]:
            self.configs["instances"][dag_node_tag].release()

    def delete(self, node_id):
        dag_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        dpg.delete_item(dag_node_tag + ":modal")
        dpg.delete_item(dag_node_tag)

    def get_export_params(self, node_id):
        dag_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        params = {}
        params["version"] = self.version
        params["position"] = dpg.get_item_pos(dag_node_tag)
        return params

    def set_import_params(self, node_id, params):
        pass

    def callback_combo_link(self, sender, data, user_data):
        dag_node_tag = user_data
        if dpg.get_value(dag_node_tag + ":link") == "Azure IoT Central":
            dpg.hide_item(dag_node_tag + ":host")
            dpg.hide_item(dag_node_tag + ":host:tooltip")
            dpg.show_item(dag_node_tag + ":scope")
            dpg.show_item(dag_node_tag + ":scope:tooltip")
            dpg.show_item(dag_node_tag + ":rid")
            dpg.show_item(dag_node_tag + ":rid:tooltip")
            dpg.show_item(dag_node_tag + ":key")
            dpg.show_item(dag_node_tag + ":key:tooltip")
            dpg.hide_item(dag_node_tag + ":string")
            dpg.hide_item(dag_node_tag + ":string:tooltip")
        elif dpg.get_value(dag_node_tag + ":link") == "Azure IoT Hub":
            dpg.hide_item(dag_node_tag + ":host")
            dpg.hide_item(dag_node_tag + ":host:tooltip")
            dpg.hide_item(dag_node_tag + ":scope")
            dpg.hide_item(dag_node_tag + ":scope:tooltip")
            dpg.hide_item(dag_node_tag + ":rid")
            dpg.hide_item(dag_node_tag + ":rid:tooltip")
            dpg.hide_item(dag_node_tag + ":key")
            dpg.hide_item(dag_node_tag + ":key:tooltip")
            dpg.show_item(dag_node_tag + ":string")
            dpg.show_item(dag_node_tag + ":string:tooltip")
        elif dpg.get_value(dag_node_tag + ":link") == "Azure IoT Hub DPS":
            dpg.show_item(dag_node_tag + ":host")
            dpg.show_item(dag_node_tag + ":host:tooltip")
            dpg.show_item(dag_node_tag + ":scope")
            dpg.show_item(dag_node_tag + ":scope:tooltip")
            dpg.show_item(dag_node_tag + ":rid")
            dpg.show_item(dag_node_tag + ":rid:tooltip")
            dpg.show_item(dag_node_tag + ":key")
            dpg.show_item(dag_node_tag + ":key:tooltip")
            dpg.hide_item(dag_node_tag + ":string")
            dpg.hide_item(dag_node_tag + ":string:tooltip")

    def callback_button_connect(self, sender, data, user_data):
        dag_node_tag = user_data
        if dpg.get_item_label(dag_node_tag + ":connect") == self.configs["label_start"]:
            if dag_node_tag not in self.configs["instances"]:
                link_class = self.configs["links"][
                    dpg.get_value(dag_node_tag + ":link")
                    if dpg.does_item_exist(dag_node_tag + ":link")
                    else None
                ]
                dpg.set_item_label(dag_node_tag + ":connect", "...")
                self.configs["instances"][dag_node_tag] = link_class()
                if dpg.get_value(dag_node_tag + ":link") == "Azure IoT Central":
                    self.configs["instances"][dag_node_tag].connect(
                        registration_id=dpg.get_value(dag_node_tag + ":rid"),
                        id_scope=dpg.get_value(dag_node_tag + ":scope"),
                        symmetric_key=dpg.get_value(dag_node_tag + ":key"),
                    )
                elif dpg.get_value(dag_node_tag + ":link") == "Azure IoT Hub":
                    self.configs["instances"][dag_node_tag].connect(
                        connection_string=dpg.get_value(dag_node_tag + ":string")
                    )
                elif dpg.get_value(dag_node_tag + ":link") == "Azure IoT Hub DPS":
                    self.configs["instances"][dag_node_tag].connect(
                        provisioning_host=dpg.get_value(dag_node_tag + ":host"),
                        registration_id=dpg.get_value(dag_node_tag + ":rid"),
                        id_scope=dpg.get_value(dag_node_tag + ":scope"),
                        symmetric_key=dpg.get_value(dag_node_tag + ":key"),
                    )
            if self.configs["instances"][dag_node_tag].device_client is not None:
                dpg.set_item_label(
                    dag_node_tag + ":connect", self.configs["label_stop"]
                )
                dpg.disable_item(dag_node_tag + ":link")
            else:
                del self.configs["instances"][dag_node_tag]
                dpg.set_item_label(
                    dag_node_tag + ":connect", self.configs["label_start"]
                )
                dpg.show_item(dag_node_tag + ":modal")
        elif (
            dpg.get_item_label(dag_node_tag + ":connect") == self.configs["label_stop"]
        ):
            self.configs["instances"][dag_node_tag].release()
            del self.configs["instances"][dag_node_tag]
            dpg.set_item_label(dag_node_tag + ":connect", self.configs["label_start"])
            dpg.enable_item(dag_node_tag + ":link")
