import copy
import logging

from gui.constants import Attribute, PinShape
from models.onnx_yolox_nano.model import YOLOXNano
from nodes.edge_ai_pipeline.base import BaseNode

try:
    import dearpygui.dearpygui as dpg
except ImportError:
    pass


class EdgeAINode(BaseNode):
    def __init__(self, settings, logger=logging.getLogger(__name__)):
        self.version = "0.1.0"
        self.name = "Object Detection"
        self.theme_titlebar = [102, 51, 0]
        self.theme_titlebar_selected = [153, 76, 0]
        self.settings = settings
        self.logger = logger
        self.configs = {}
        self.configs["models"] = {
            "YOLOX Nano": YOLOXNano,
        }
        self.configs["instances"] = {}
        self.forms = {}
        self.forms["model"] = {}

    def add_node(self, parent, node_id, pos):
        # Describe node attribute tags
        dpg_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        dpg_pin_tags = self.get_tag_list(dpg_node_tag)
        self.forms["model"][dpg_node_tag] = list(self.configs["models"].keys())[0]

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
                with dpg.node_attribute(
                    attribute_type=int(Attribute.INPUT),
                    shape=int(PinShape.QUAD),
                    tag=dpg_pin_tags[self.MESSAGE_IN],
                ):
                    dpg.add_text("MESSAGE IN")
                with dpg.node_attribute(
                    attribute_type=int(Attribute.OUTPUT),
                    tag=dpg_pin_tags[self.VIDEO_OUT],
                ):
                    with dpg.group(horizontal=True):
                        dpg.add_text("VIDEO OUT")
                        dpg.add_spacer(width=self.settings["node_width"] - 100)
                        dpg.add_checkbox(
                            label="",
                            tag=dpg_node_tag + ":video_out",
                            default_value=True,
                        )
                with dpg.node_attribute(
                    attribute_type=int(Attribute.OUTPUT),
                    shape=int(PinShape.QUAD),
                    tag=dpg_pin_tags[self.MESSAGE_OUT],
                ):
                    with dpg.group(horizontal=True):
                        dpg.add_text("MESSAGE OUT")
                        dpg.add_spacer(width=self.settings["node_width"] - 120)
                        dpg.add_checkbox(
                            label="",
                            tag=dpg_node_tag + ":message_out",
                            default_value=True,
                        )

                # Add a combo dropdown that allows selecting model
                with dpg.node_attribute(attribute_type=int(Attribute.STATIC)):
                    dpg.add_spacer(height=5)
                    dpg.add_combo(
                        list(self.configs["models"].keys()),
                        default_value=self.forms["model"][dpg_node_tag],
                        width=self.settings["node_width"],
                        callback=self.callback_change_model,
                        user_data=dpg_node_tag,
                        tag=dpg_node_tag + ":model",
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
        model_name = self.forms["model"][dpg_node_tag]
        model_class = self.configs["models"][model_name]

        # Get linked node tag
        linked_node_tag = None
        for link in node_links:
            link_pin_shape = link[0].split(":")[2]
            if link_pin_shape == str(int(PinShape.QUAD)):
                linked_node_tag_message = ":".join(link[0].split(":")[:2])
                message = node_messages.get(linked_node_tag_message, None)
            if link_pin_shape == str(int(PinShape.CIRCLE_FILLED)):
                linked_node_tag = ":".join(link[0].split(":")[:2])

        # Inference
        linked_frame = node_frames.get(linked_node_tag, None)
        if linked_frame is not None:
            frame = copy.deepcopy(linked_frame)
            if model_name not in self.configs["instances"]:
                self.configs["instances"][model_name] = model_class()
            frame, inference_message = self.configs["instances"][model_name](frame)
            texture = self.get_image_texture(
                frame,
                self.settings["node_width"],
                self.settings["node_height"],
            )
            if self.settings["gui"]:
                if dpg.does_item_exist(dpg_node_tag + ":texture"):
                    dpg.set_value(dpg_node_tag + ":texture", texture)

            # Generate message
            if message is None:
                message = []
            message.append(
                {
                    "type": "processor",
                    "subtype": self.name.lower().replace(" ", "_"),
                    "inference": inference_message,
                }
            )

        # Control output
        if self.settings["gui"]:
            if not dpg.get_value(dpg_node_tag + ":message_out"):
                message = None
            if not dpg.get_value(dpg_node_tag + ":video_out"):
                frame = None

        # Return frame and message
        return frame, message

    def close(self, node_id):
        pass

    def delete(self, node_id):
        dpg_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        if self.settings["gui"]:
            dpg.delete_item(dpg_node_tag + ":texture")
            dpg.delete_item(dpg_node_tag)

    def get_export_params(self, node_id):
        dpg_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        params = {}
        params["version"] = self.version
        params["position"] = [0, 0]
        params["model"] = self.forms["model"][dpg_node_tag]
        if self.settings["gui"]:
            params["position"] = dpg.get_item_pos(dpg_node_tag)
        return params

    def set_import_params(self, node_id, params):
        dpg_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        if "model" in params:
            self.forms["model"][dpg_node_tag] = params["model"]
            if self.settings["gui"]:
                dpg.set_value(dpg_node_tag + ":model", params["model"])

    def callback_change_model(self, sender, data, user_data):
        dpg_node_tag = user_data
        self.forms["model"][dpg_node_tag] = data
