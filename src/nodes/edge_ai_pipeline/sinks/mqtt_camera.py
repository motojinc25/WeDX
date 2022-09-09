import logging

from gui.constants import Attribute, NoteState, PinShape
from links.mqtt_client.link import MQTTClient
from nodes.edge_ai_pipeline.base import BaseNode

try:
    import dearpygui.dearpygui as dpg
except ImportError:
    pass


class EdgeAINode(BaseNode):
    def __init__(self, settings, logger=logging.getLogger(__name__)):
        self.version = "0.1.0"
        self.name = "MQTT Camera"
        self.theme_titlebar = [102, 0, 102]
        self.theme_titlebar_selected = [153, 0, 153]
        self.settings = settings
        self.logger = logger
        self.configs = {}
        self.configs["protocols"] = {
            "MQTT V3.1.1": MQTTClient,
        }
        self.configs["instances"] = {}
        self.configs["states"] = {}
        self.forms = {}
        self.forms["protocol"] = {}
        self.forms["host"] = {}
        self.forms["port"] = {}
        self.forms["client_id"] = {}
        self.forms["username"] = {}
        self.forms["password"] = {}
        self.forms["topic"] = {}

    def add_node(self, parent, node_id, pos):
        # Describe node attribute tags
        dpg_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        dpg_pin_tags = self.get_tag_list(dpg_node_tag)
        self.configs["states"][dpg_node_tag] = NoteState.CONNECT
        self.forms["protocol"][dpg_node_tag] = list(self.configs["protocols"].keys())[0]
        self.forms["host"][dpg_node_tag] = ""
        self.forms["port"][dpg_node_tag] = ""
        self.forms["client_id"][dpg_node_tag] = ""
        self.forms["username"][dpg_node_tag] = ""
        self.forms["password"][dpg_node_tag] = ""
        self.forms["topic"][dpg_node_tag] = ""

        if self.settings["gui"]:
            # Add a dynamic texture and a raw texture
            with dpg.texture_registry(show=False):
                dpg.add_raw_texture(
                    self.settings["node_width"],
                    self.settings["node_height"],
                    self.get_blank_texture(
                        self.settings["node_width"], self.settings["node_height"]
                    ),
                    tag=dpg_node_tag + ":texture",
                    format=dpg.mvFormat_Float_rgba,
                )

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
                    tag=dpg_pin_tags[self.VIDEO_IN],
                ):
                    dpg.add_text("VIDEO IN")

                # Add a combo dropdown that allows selecting protocol
                with dpg.node_attribute(attribute_type=int(Attribute.STATIC)):
                    dpg.add_spacer(height=5)
                    dpg.add_combo(
                        list(self.configs["protocols"].keys()),
                        default_value=self.forms["protocol"][dpg_node_tag],
                        width=self.settings["node_width"],
                        tag=dpg_node_tag + ":protocol",
                    )

                # Add inputs for credentials
                with dpg.node_attribute(attribute_type=int(Attribute.STATIC)):
                    dpg.add_input_text(
                        label="Host",
                        no_spaces=True,
                        width=self.settings["node_width"] - 65,
                        show=True,
                        default_value=self.forms["host"][dpg_node_tag],
                        tag=dpg_node_tag + ":host",
                    )
                    with dpg.tooltip(dpg_node_tag + ":host"):
                        dpg.add_text(
                            "Broker Host",
                            show=True,
                            tag=dpg_node_tag + ":host:tooltip",
                        )
                    dpg.add_input_text(
                        label="Port",
                        no_spaces=True,
                        width=self.settings["node_width"] - 65,
                        default_value=self.forms["port"][dpg_node_tag],
                        tag=dpg_node_tag + ":port",
                    )
                    with dpg.tooltip(dpg_node_tag + ":port"):
                        dpg.add_text(
                            "Broker Port",
                            tag=dpg_node_tag + ":port:tooltip",
                        )
                    dpg.add_input_text(
                        label="Client ID",
                        no_spaces=True,
                        width=self.settings["node_width"] - 65,
                        default_value=self.forms["client_id"][dpg_node_tag],
                        tag=dpg_node_tag + ":client_id",
                    )
                    dpg.add_input_text(
                        label="Username",
                        no_spaces=True,
                        width=self.settings["node_width"] - 65,
                        default_value=self.forms["username"][dpg_node_tag],
                        tag=dpg_node_tag + ":username",
                    )
                    dpg.add_input_text(
                        label="Password",
                        no_spaces=True,
                        width=self.settings["node_width"] - 65,
                        show=True,
                        password=True,
                        default_value=self.forms["password"][dpg_node_tag],
                        tag=dpg_node_tag + ":password",
                    )
                    dpg.add_input_text(
                        label="Topic",
                        no_spaces=True,
                        width=self.settings["node_width"] - 65,
                        show=True,
                        default_value=self.forms["topic"][dpg_node_tag],
                        tag=dpg_node_tag + ":topic",
                    )

                # Add a button for publishing
                with dpg.node_attribute(attribute_type=int(Attribute.STATIC)):
                    dpg.add_button(
                        label=self.configs["states"][dpg_node_tag],
                        width=self.settings["node_width"],
                        callback=self.callback_button_connect,
                        user_data=dpg_node_tag,
                        tag=dpg_node_tag + ":connect",
                    )

                # Add an image from a specified texture
                with dpg.node_attribute(attribute_type=int(Attribute.STATIC)):
                    dpg.add_image(dpg_node_tag + ":texture")

        # Return Dear PyGui Tag
        return dpg_node_tag

    async def refresh(self, node_id, node_links, node_frames, node_messages):
        dpg_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")

        # Get linked node tag
        linked_node_tag = None
        for link in node_links:
            link_pin_shape = link[0].split(":")[2]
            if link_pin_shape == str(int(PinShape.CIRCLE_FILLED)):
                linked_node_tag = ":".join(link[0].split(":")[:2])

        # Publish
        linked_frame = node_frames.get(linked_node_tag, None)
        if linked_frame is not None:
            if self.configs["states"][dpg_node_tag] == NoteState.CONNECTED:
                if dpg_node_tag in self.configs["instances"]:
                    self.configs["instances"][dpg_node_tag].publish_image(linked_frame)
            texture = self.get_image_texture(
                linked_frame,
                self.settings["node_width"],
                self.settings["node_height"],
            )
            if self.settings["gui"]:
                if dpg.does_item_exist(dpg_node_tag + ":texture"):
                    dpg.set_value(dpg_node_tag + ":texture", texture)

        # Return frame and message
        return None, None

    def close(self, node_id):
        dpg_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        if dpg_node_tag in self.configs["instances"]:
            self.configs["instances"][dpg_node_tag].release()

    def delete(self, node_id):
        dpg_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        if dpg_node_tag in self.configs["instances"]:
            self.configs["instances"][dpg_node_tag].release()
        if self.settings["gui"]:
            dpg.delete_item(dpg_node_tag + ":modal")
            dpg.delete_item(dpg_node_tag + ":texture")
            dpg.delete_item(dpg_node_tag)

    def get_export_params(self, node_id):
        dpg_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        params = {}
        params["version"] = self.version
        params["position"] = [0, 0]
        params["protocol"] = self.forms["protocol"][dpg_node_tag]
        params["host"] = self.forms["host"][dpg_node_tag]
        params["port"] = self.forms["port"][dpg_node_tag]
        params["client_id"] = self.forms["client_id"][dpg_node_tag]
        params["username"] = self.forms["username"][dpg_node_tag]
        params["password"] = self.forms["password"][dpg_node_tag]
        params["topic"] = self.forms["topic"][dpg_node_tag]
        if self.settings["gui"]:
            params["position"] = dpg.get_item_pos(dpg_node_tag)
        return params

    def set_import_params(self, node_id, params):
        dpg_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        if "protocol" in params:
            self.forms["protocol"][dpg_node_tag] = params["protocol"]
            if self.settings["gui"]:
                dpg.set_value(dpg_node_tag + ":protocol", params["protocol"])
        if "host" in params:
            self.forms["host"][dpg_node_tag] = params["host"]
            if self.settings["gui"]:
                dpg.set_value(dpg_node_tag + ":host", params["host"])
        if "port" in params:
            self.forms["port"][dpg_node_tag] = params["port"]
            if self.settings["gui"]:
                dpg.set_value(dpg_node_tag + ":port", params["port"])
        if "client_id" in params:
            self.forms["client_id"][dpg_node_tag] = params["client_id"]
            if self.settings["gui"]:
                dpg.set_value(dpg_node_tag + ":client_id", params["client_id"])
        if "username" in params:
            self.forms["username"][dpg_node_tag] = params["username"]
            if self.settings["gui"]:
                dpg.set_value(dpg_node_tag + ":username", params["username"])
        if "password" in params:
            self.forms["password"][dpg_node_tag] = params["password"]
            if self.settings["gui"]:
                dpg.set_value(dpg_node_tag + ":password", params["password"])
        if "topic" in params:
            self.forms["topic"][dpg_node_tag] = params["topic"]
            if self.settings["gui"]:
                dpg.set_value(dpg_node_tag + ":topic", params["topic"])
        if (
            dpg_node_tag in self.forms["protocol"]
            and dpg_node_tag in self.forms["host"]
            and dpg_node_tag in self.forms["port"]
            and dpg_node_tag in self.forms["client_id"]
            and dpg_node_tag in self.forms["username"]
            and dpg_node_tag in self.forms["password"]
            and dpg_node_tag in self.forms["topic"]
        ):
            self.configs["instances"][dpg_node_tag] = MQTTClient(
                host=dpg.get_value(dpg_node_tag + ":host"),
                port=dpg.get_value(dpg_node_tag + ":port"),
                client_id=dpg.get_value(dpg_node_tag + ":client_id"),
                username=dpg.get_value(dpg_node_tag + ":username"),
                password=dpg.get_value(dpg_node_tag + ":password"),
                topic=dpg.get_value(dpg_node_tag + ":topic"),
            )
            if self.settings["gui"]:
                dpg.set_item_label(dpg_node_tag + ":connect", "...")
            self.configs["instances"][dpg_node_tag].connect()
            if self.configs["instances"][dpg_node_tag].is_connected:
                self.configs["states"][dpg_node_tag] = NoteState.CONNECTED
                if self.settings["gui"]:
                    dpg.set_item_label(dpg_node_tag + ":connect", NoteState.CONNECTED)
                    dpg.disable_item(dpg_node_tag + ":protocol")
                    dpg.disable_item(dpg_node_tag + ":host")
                    dpg.disable_item(dpg_node_tag + ":port")
                    dpg.disable_item(dpg_node_tag + ":client_id")
                    dpg.disable_item(dpg_node_tag + ":username")
                    dpg.disable_item(dpg_node_tag + ":password")
                    dpg.disable_item(dpg_node_tag + ":topic")
            else:
                if self.settings["gui"]:
                    dpg.set_item_label(dpg_node_tag + ":connect", NoteState.CONNECT)

    def callback_button_connect(self, sender, data, user_data):
        dpg_node_tag = user_data
        if self.configs["states"][dpg_node_tag] == NoteState.CONNECT:
            if dpg_node_tag not in self.configs["instances"]:
                dpg.set_item_label(dpg_node_tag + ":connect", "...")
                self.configs["instances"][dpg_node_tag] = MQTTClient(
                    host=dpg.get_value(dpg_node_tag + ":host"),
                    port=dpg.get_value(dpg_node_tag + ":port"),
                    client_id=dpg.get_value(dpg_node_tag + ":client_id"),
                    username=dpg.get_value(dpg_node_tag + ":username"),
                    password=dpg.get_value(dpg_node_tag + ":password"),
                    topic=dpg.get_value(dpg_node_tag + ":topic"),
                )
                self.configs["instances"][dpg_node_tag].connect()
            if self.configs["instances"][dpg_node_tag].is_connected:
                dpg.set_item_label(dpg_node_tag + ":connect", NoteState.CONNECTED)
                dpg.disable_item(dpg_node_tag + ":protocol")
                dpg.disable_item(dpg_node_tag + ":host")
                dpg.disable_item(dpg_node_tag + ":port")
                dpg.disable_item(dpg_node_tag + ":client_id")
                dpg.disable_item(dpg_node_tag + ":username")
                dpg.disable_item(dpg_node_tag + ":password")
                dpg.disable_item(dpg_node_tag + ":topic")
                self.configs["states"][dpg_node_tag] = NoteState.CONNECTED
                self.forms["host"][dpg_node_tag] = dpg.get_value(dpg_node_tag + ":host")
                self.forms["port"][dpg_node_tag] = dpg.get_value(dpg_node_tag + ":port")
                self.forms["client_id"][dpg_node_tag] = dpg.get_value(dpg_node_tag + ":client_id")
                self.forms["username"][dpg_node_tag] = dpg.get_value(dpg_node_tag + ":username")
                self.forms["password"][dpg_node_tag] = dpg.get_value(dpg_node_tag + ":password")
                self.forms["topic"][dpg_node_tag] = dpg.get_value(dpg_node_tag + ":topic")
            else:
                del self.configs["instances"][dpg_node_tag]
                dpg.set_item_label(dpg_node_tag + ":connect", NoteState.CONNECT)
                self.configs["states"][dpg_node_tag] = NoteState.CONNECT
                dpg.show_item(dpg_node_tag + ":modal")
        elif self.configs["states"][dpg_node_tag] == NoteState.CONNECTED:
            if dpg_node_tag in self.configs["instances"]:
                self.configs["instances"][dpg_node_tag].release()
                del self.configs["instances"][dpg_node_tag]
            self.configs["states"][dpg_node_tag] = NoteState.CONNECT
            dpg.set_item_label(dpg_node_tag + ":connect", NoteState.CONNECT)
            dpg.enable_item(dpg_node_tag + ":protocol")
            dpg.enable_item(dpg_node_tag + ":host")
            dpg.enable_item(dpg_node_tag + ":port")
            dpg.enable_item(dpg_node_tag + ":client_id")
            dpg.enable_item(dpg_node_tag + ":username")
            dpg.enable_item(dpg_node_tag + ":password")
            dpg.enable_item(dpg_node_tag + ":topic")
