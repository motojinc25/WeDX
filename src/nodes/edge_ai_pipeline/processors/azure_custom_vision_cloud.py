import copy
import logging

from gui.constants import Attribute, PinShape
from links.azure_custom_vision.link import AzureCustomVision
from nodes.edge_ai_pipeline.base import BaseNode

try:
    import dearpygui.dearpygui as dpg
except ImportError:
    pass


class EdgeAINode(BaseNode):
    def __init__(self, settings, logger=logging.getLogger(__name__)):
        self.version = "0.1.0"
        self.name = "Azure Custom Vision (Cloud)"
        self.theme_titlebar = [102, 51, 0]
        self.theme_titlebar_selected = [153, 76, 0]
        self.settings = settings
        self.logger = logger
        self.configs = {}
        self.configs["link"] = {
            "Prediction API": AzureCustomVision,
        }
        self.configs["instances"] = {}
        self.configs["messages"] = {}
        self.configs["frames"] = {}
        self.configs["label_connect"] = "Connect"
        self.configs["label_prediction"] = "Prediction"
        self.forms = {}
        self.forms["link"] = {}
        self.forms["url"] = {}
        self.forms["key"] = {}

    def add_node(self, parent, node_id, pos):
        # Describe node attribute tags
        dpg_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        dpg_pin_tags = self.get_tag_list(dpg_node_tag)
        self.forms["link"][dpg_node_tag] = list(self.configs["link"].keys())[0]
        self.forms["url"][dpg_node_tag] = ""
        self.forms["key"][dpg_node_tag] = ""

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
                    dpg.add_text("VIDEO OUT")
                with dpg.node_attribute(
                    attribute_type=int(Attribute.OUTPUT),
                    shape=int(PinShape.QUAD),
                    tag=dpg_pin_tags[self.MESSAGE_OUT],
                ):
                    dpg.add_text("MESSAGE OUT")

                # Add a combo dropdown that allows selecting model
                with dpg.node_attribute(attribute_type=int(Attribute.STATIC)):
                    dpg.add_spacer(height=5)
                    dpg.add_combo(
                        list(self.configs["link"].keys()),
                        default_value=self.forms["link"][dpg_node_tag],
                        width=self.settings["node_width"],
                        callback=self.callback_change_link,
                        user_data=dpg_node_tag,
                        tag=dpg_node_tag + ":link",
                    )

                # Add inputs for credentials
                with dpg.node_attribute(attribute_type=int(Attribute.STATIC)):
                    dpg.add_input_text(
                        label="URL",
                        no_spaces=True,
                        width=self.settings["node_width"] - 50,
                        default_value=self.forms["url"][dpg_node_tag],
                        tag=dpg_node_tag + ":url",
                    )
                    with dpg.tooltip(dpg_node_tag + ":url"):
                        dpg.add_text(
                            "Prediction API Image URL",
                            tag=dpg_node_tag + ":url:tooltip",
                        )
                    dpg.add_input_text(
                        label="Key",
                        no_spaces=True,
                        width=self.settings["node_width"] - 50,
                        default_value=self.forms["key"][dpg_node_tag],
                        tag=dpg_node_tag + ":key",
                    )
                    with dpg.tooltip(dpg_node_tag + ":key"):
                        dpg.add_text(
                            "Prediction API Key",
                            tag=dpg_node_tag + ":key:tooltip",
                        )

                # Add a button for prediction
                with dpg.node_attribute(attribute_type=int(Attribute.STATIC)):
                    dpg.add_button(
                        label=self.configs["label_connect"],
                        width=self.settings["node_width"],
                        callback=self.callback_button_connect,
                        user_data=dpg_node_tag,
                        tag=dpg_node_tag + ":connect",
                    )
                    dpg.add_loading_indicator(
                        style=0,
                        show=False,
                        tag=dpg_node_tag + ":loading",
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
            self.configs["frames"][dpg_node_tag] = frame

            # Draw landmarks
            if dpg_node_tag in self.configs["messages"]:
                frame = self.configs["instances"][dpg_node_tag].draw_landmarks(
                    frame, self.configs["messages"][dpg_node_tag]
                )

                # Generate message
                if message is None:
                    message = []
                message.append(
                    {
                        "type": "processor",
                        "subtype": self.name.lower().replace(" ", "_"),
                        "inference": self.configs["messages"][dpg_node_tag],
                    }
                )

            # Update texture
            texture = self.get_image_texture(
                frame,
                self.settings["node_width"],
                self.settings["node_height"],
            )
            if self.settings["gui"]:
                if dpg.does_item_exist(dpg_node_tag + ":texture"):
                    dpg.set_value(dpg_node_tag + ":texture", texture)

        # Return frame and message
        return frame, message

    def close(self, node_id):
        pass

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
            params["link"] = self.forms["model"][dpg_node_tag]
            if params["link"] == "Prediction API":
                params["url"] = self.forms["url"][dpg_node_tag]
                params["key"] = self.forms["key"][dpg_node_tag]
        return params

    def set_import_params(self, node_id, params):
        dpg_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        if "link" in params:
            self.forms["link"][dpg_node_tag] = params["link"]
            if self.settings["gui"]:
                dpg.set_value(dpg_node_tag + ":link", params["link"])
        if "url" in params:
            self.forms["url"][dpg_node_tag] = params["url"]
            if self.settings["gui"]:
                dpg.set_value(dpg_node_tag + ":url", params["url"])
        if "key" in params:
            self.forms["key"][dpg_node_tag] = params["key"]
            if self.settings["gui"]:
                dpg.set_value(dpg_node_tag + ":key", params["key"])

    def callback_change_link(self, sender, data, user_data):
        dpg_node_tag = user_data
        self.forms["link"][dpg_node_tag] = data

    def callback_button_connect(self, sender, data, user_data):
        dpg_node_tag = user_data
        if (
            dpg.get_item_label(dpg_node_tag + ":connect")
            == self.configs["label_connect"]
        ):
            if dpg_node_tag not in self.configs["instances"]:
                link_class = self.configs["link"][
                    dpg.get_value(dpg_node_tag + ":link")
                    if dpg.does_item_exist(dpg_node_tag + ":link")
                    else None
                ]
                dpg.set_item_label(dpg_node_tag + ":connect", "...")
                self.configs["instances"][dpg_node_tag] = link_class()
                if dpg.get_value(dpg_node_tag + ":link") == "Prediction API":
                    self.configs["instances"][dpg_node_tag].connect(
                        url=dpg.get_value(dpg_node_tag + ":url"),
                        key=dpg.get_value(dpg_node_tag + ":key"),
                    )
            if self.configs["instances"][dpg_node_tag].client:
                dpg.set_item_label(
                    dpg_node_tag + ":connect", self.configs["label_prediction"]
                )
                dpg.disable_item(dpg_node_tag + ":link")
                self.forms["url"][dpg_node_tag] = dpg.get_value(dpg_node_tag + ":url")
                self.forms["key"][dpg_node_tag] = dpg.get_value(dpg_node_tag + ":key")
            else:
                del self.configs["instances"][dpg_node_tag]
                dpg.set_item_label(
                    dpg_node_tag + ":connect", self.configs["label_connect"]
                )
                dpg.show_item(dpg_node_tag + ":modal")
        elif (
            dpg.get_item_label(dpg_node_tag + ":connect")
            == self.configs["label_prediction"]
        ):
            if dpg_node_tag in self.configs["frames"]:
                dpg.configure_item(dpg_node_tag + ":loading", show=True)
                frame, inference_message = self.configs["instances"][dpg_node_tag](
                    self.configs["frames"][dpg_node_tag]
                )
                self.configs["frames"][dpg_node_tag] = frame
                self.configs["messages"][dpg_node_tag] = inference_message
                dpg.configure_item(dpg_node_tag + ":loading", show=False)
