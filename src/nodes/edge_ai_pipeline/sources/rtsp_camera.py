import logging

import cv2

from gui.constants import Attribute, PinShape
from nodes.edge_ai_pipeline.base import BaseNode

try:
    import dearpygui.dearpygui as dpg
except ImportError:
    pass


class EdgeAINode(BaseNode):
    def __init__(self, settings, logger=logging.getLogger(__name__)):
        self.version = "0.1.0"
        self.name = "RTSP Camera"
        self.theme_titlebar = [51, 102, 0]
        self.theme_titlebar_selected = [76, 153, 0]
        self.settings = settings
        self.logger = logger
        self.configs = {}
        self.configs["instances"] = {}
        self.configs["label_connect"] = "Connect"
        self.configs["label_connected"] = "Connected"
        self.forms = {}
        self.forms["url"] = {}
        self.forms["connect"] = {}

    def add_node(self, parent, node_id, pos):
        # Describe node attribute tags
        dpg_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        dpg_pin_tags = self.get_tag_list(dpg_node_tag)
        self.forms["url"][dpg_node_tag] = ""
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
                    attribute_type=int(Attribute.OUTPUT),
                    tag=dpg_pin_tags[self.VIDEO_OUT],
                ):
                    dpg.add_text("VIDEO OUT")
                with dpg.node_attribute(
                    attribute_type=int(Attribute.OUTPUT),
                    shape=int(PinShape.QUAD),
                    tag=dpg_pin_tags[self.MESSAGE_OUT],
                ):
                    dpg.add_text("MESSAGE OUT")

                # Add inputs for credentials
                with dpg.node_attribute(attribute_type=int(Attribute.STATIC)):
                    dpg.add_spacer(height=5)
                    dpg.add_input_text(
                        label="URL",
                        no_spaces=True,
                        width=self.settings["node_width"] - 50,
                        default_value=self.forms["url"][dpg_node_tag],
                        tag=dpg_node_tag + ":url",
                    )
                    with dpg.tooltip(dpg_node_tag + ":url"):
                        dpg.add_text(
                            "RTSP URL",
                            show=True,
                            tag=dpg_node_tag + ":url:tooltip",
                        )

                # Add a button for connecting
                with dpg.node_attribute(attribute_type=int(Attribute.STATIC)):
                    dpg.add_button(
                        label=self.forms["connect"][dpg_node_tag],
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
        frame = None
        message = None
        rtsp_url = self.forms["url"][dpg_node_tag]

        # Capture frame-by-frame
        if self.forms["connect"][dpg_node_tag] == self.configs["label_connected"]:
            if dpg_node_tag in self.configs["instances"]:
                ret, frame = self.configs["instances"][dpg_node_tag].read()
                if ret == True:
                    texture = self.get_image_texture(
                        frame, self.settings["node_width"], self.settings["node_height"]
                    )
                    if self.settings["gui"]:
                        if dpg.does_item_exist(dpg_node_tag + ":texture"):
                            dpg.set_value(dpg_node_tag + ":texture", texture)

                # Generate message
                message = [
                    {
                        "type": "source",
                        "subtype": self.name.lower().replace(" ", "_"),
                        "image": {
                            "source": rtsp_url,
                            "width": self.configs["instances"][dpg_node_tag].get(
                                cv2.CAP_PROP_FRAME_WIDTH
                            ),
                            "height": self.configs["instances"][dpg_node_tag].get(
                                cv2.CAP_PROP_FRAME_HEIGHT
                            ),
                        },
                    }
                ]

        # Return frame and message
        return frame, message

    def close(self, node_id):
        dpg_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        if dpg_node_tag in self.configs["instances"]:
            self.configs["instances"][dpg_node_tag].release()

    def delete(self, node_id):
        dpg_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        if self.settings["gui"]:
            dpg.delete_item(dpg_node_tag + ":modal")
            dpg.delete_item(dpg_node_tag + ":texture")
            dpg.delete_item(dpg_node_tag)

    def get_export_params(self, node_id):
        dpg_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        params = {}
        if self.settings["gui"]:
            params["version"] = self.version
            params["position"] = dpg.get_item_pos(dpg_node_tag)
            params["url"] = self.forms["url"][dpg_node_tag]
        return params

    def set_import_params(self, node_id, params):
        dpg_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        if "url" in params:
            self.forms["url"][dpg_node_tag] = params["url"]
            if self.settings["gui"]:
                dpg.set_value(dpg_node_tag + ":url", params["url"])

    def callback_button_connect(self, sender, app_data, user_data):
        dpg_node_tag = user_data
        if self.forms["connect"][dpg_node_tag] == self.configs["label_connect"]:
            rtsp_url = (
                dpg.get_value(dpg_node_tag + ":url")
                if dpg.does_item_exist(dpg_node_tag + ":url")
                else None
            )
            if rtsp_url is not None:
                dpg.set_item_label(dpg_node_tag + ":connect", "...")
                try:
                    cap = cv2.VideoCapture(rtsp_url)
                except:
                    pass
                if cap.isOpened():
                    self.configs["instances"][dpg_node_tag] = cap
                    dpg.set_item_label(
                        dpg_node_tag + ":connect", self.configs["label_connected"]
                    )
                    dpg.disable_item(dpg_node_tag + ":url")
                    self.forms["url"][dpg_node_tag] = dpg.get_value(
                        dpg_node_tag + ":url"
                    )
                    self.forms["connect"][dpg_node_tag] = self.configs["label_connected"]
                else:
                    dpg.set_item_label(
                        dpg_node_tag + ":connect", self.configs["label_connect"]
                    )
                    self.forms["connect"][dpg_node_tag] = self.configs["label_connect"]
                    dpg.show_item(dpg_node_tag + ":modal")
        elif self.forms["connect"][dpg_node_tag] == self.configs["label_connected"]:
            self.configs["instances"][dpg_node_tag].release()
            del self.configs["instances"][dpg_node_tag]
            dpg.set_item_label(dpg_node_tag + ":connect", self.configs["label_connect"])
            dpg.enable_item(dpg_node_tag + ":url")
