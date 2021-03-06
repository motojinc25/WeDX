import copy
import os

import dearpygui.dearpygui as dpg

from models.onnx_custom_vision.model import (
    CustomVisionClassification,
    CustomVisionObjectDetection,
)
from nodes.edge_ai_pipeline.base import BaseNode


class EdgeAINode(BaseNode):
    def __init__(self, settings):
        self.version = "0.1.0"
        self.name = "Azure Custom Vision (Offline)"
        self.theme_titlebar = [102, 51, 0]
        self.theme_titlebar_selected = [153, 76, 0]
        self.settings = settings
        self.configs = {}
        self.configs["models"] = {
            "ONNX Model Classification": CustomVisionClassification,
            "ONNX Model Object Detector": CustomVisionObjectDetection,
        }
        self.configs["instances"] = {}
        self.configs["statuses"] = {}
        self.configs["model_filepaths"] = {}
        self.configs["labels_filepaths"] = {}
        self.configs["label_connect"] = "Connect"
        self.configs["label_connected"] = "Connected"

    def add_node(self, parent, node_id, pos):
        # Describe node attribute tags
        dpg_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        dpg_pin_tags = self.get_tag_list(dpg_node_tag)

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

        # Model/Labels file dialog
        current_path = os.path.dirname(os.path.abspath(__file__))
        with dpg.file_dialog(
            label="ONNX Model",
            directory_selector=False,
            show=False,
            modal=True,
            height=int(self.settings["viewport_height"] / 2),
            default_path=os.path.abspath(
                os.path.join(current_path, "../../../models/onnx_custom_vision")
            ),
            user_data=dpg_node_tag,
            callback=self.callback_file_dialog_model,
            id=dpg_node_tag + ":file_dialog_model",
            tag=dpg_node_tag + ":file_dialog_model",
        ):
            dpg.add_file_extension(".onnx")
            dpg.add_file_extension("", color=(150, 255, 150, 255))
        with dpg.file_dialog(
            label="Model Labels",
            directory_selector=False,
            show=False,
            modal=True,
            height=int(self.settings["viewport_height"] / 2),
            default_path=os.path.abspath(
                os.path.join(current_path, "../../../models/onnx_custom_vision")
            ),
            user_data=dpg_node_tag,
            callback=self.callback_file_dialog_labels,
            id=dpg_node_tag + ":file_dialog_labels",
            tag=dpg_node_tag + ":file_dialog_labels",
        ):
            dpg.add_file_extension(".txt")
            dpg.add_file_extension("", color=(150, 255, 150, 255))

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
                attribute_type=dpg.mvNode_Attr_Input,
                tag=dpg_pin_tags[self.VIDEO_IN],
            ):
                dpg.add_text("VIDEO IN")
            with dpg.node_attribute(
                attribute_type=dpg.mvNode_Attr_Input,
                shape=dpg.mvNode_PinShape_Quad,
                tag=dpg_pin_tags[self.MESSAGE_IN],
            ):
                dpg.add_text("MESSAGE IN")
            with dpg.node_attribute(
                attribute_type=dpg.mvNode_Attr_Output,
                tag=dpg_pin_tags[self.VIDEO_OUT],
            ):
                dpg.add_text("VIDEO OUT")
            with dpg.node_attribute(
                attribute_type=dpg.mvNode_Attr_Output,
                shape=dpg.mvNode_PinShape_Quad,
                tag=dpg_pin_tags[self.MESSAGE_OUT],
            ):
                dpg.add_text("MESSAGE OUT")

            # Add a combo dropdown that allows selecting model
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static):
                dpg.add_spacer(height=5)
                dpg.add_combo(
                    list(self.configs["models"].keys()),
                    default_value=list(self.configs["models"].keys())[0],
                    width=self.settings["node_width"],
                    callback=self.callback_combo_link,
                    user_data=dpg_node_tag,
                    tag=dpg_node_tag + ":model",
                )

            # Add model and labels file dialog buttons
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static):
                with dpg.group(horizontal=True):
                    dpg.add_text(
                        "Select ONNX Model : not yet",
                        bullet=True,
                        tag=dpg_node_tag + ":modelfile:text",
                    )
                    dpg.add_button(
                        label="File",
                        callback=lambda: dpg.show_item(
                            dpg_node_tag + ":file_dialog_model"
                        ),
                        user_data=dpg_node_tag,
                        tag=dpg_node_tag + ":modelfile",
                    )
                with dpg.group(horizontal=True):
                    dpg.add_text(
                        "Select Model Labels : not yet",
                        bullet=True,
                        tag=dpg_node_tag + ":labelsfile:text",
                    )
                    dpg.add_button(
                        label="File",
                        callback=lambda: dpg.show_item(
                            dpg_node_tag + ":file_dialog_labels"
                        ),
                        user_data=dpg_node_tag,
                        tag=dpg_node_tag + ":labelsfile",
                    )

            # Add a button for connecting
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static):
                dpg.add_button(
                    label=self.configs["label_connect"],
                    width=self.settings["node_width"],
                    callback=self.callback_button_connect,
                    user_data=dpg_node_tag,
                    tag=dpg_node_tag + ":connect",
                )

            # Add an image from a specified texture
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static):
                dpg.add_image(dpg_node_tag + ":texture")

        # Return Dear PyGui Tag
        return dpg_node_tag

    async def refresh(self, node_id, node_models, node_frames, node_messages):
        dpg_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        frame = None
        message = None

        # Get linked node tag
        linked_node_tag = None
        for link in node_models:
            link_pin_shape = link[0].split(":")[2]
            if link_pin_shape == str(dpg.mvNode_PinShape_Quad):
                linked_node_tag_message = ":".join(link[0].split(":")[:2])
                message = node_messages.get(linked_node_tag_message, None)
            if link_pin_shape == str(dpg.mvNode_PinShape_CircleFilled):
                linked_node_tag = ":".join(link[0].split(":")[:2])

        # Inference
        linked_frame = node_frames.get(linked_node_tag, None)
        if linked_frame is not None:
            frame = copy.deepcopy(linked_frame)
            if dpg_node_tag in self.configs["instances"]:
                frame, inference_message = self.configs["instances"][dpg_node_tag](
                    frame
                )
                if message is None:
                    message = []
                message.append(
                    {
                        "type": "processor",
                        "subtype": self.name.lower().replace(" ", "_"),
                        "inference": inference_message,
                    }
                )
            texture = self.get_image_texture(
                frame,
                self.settings["node_width"],
                self.settings["node_height"],
            )
            if dpg.does_item_exist(dpg_node_tag + ":texture"):
                dpg.set_value(dpg_node_tag + ":texture", texture)

        # Return frame and message
        return frame, message

    def close(self, node_id):
        pass

    def delete(self, node_id):
        dpg_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        dpg.delete_item(dpg_node_tag + ":modal")
        dpg.delete_item(dpg_node_tag + ":file_dialog_model")
        dpg.delete_item(dpg_node_tag + ":file_dialog_labels")
        dpg.delete_item(dpg_node_tag + ":texture")
        dpg.delete_item(dpg_node_tag)

    def get_export_params(self, node_id):
        dpg_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        params = {}
        params["version"] = self.version
        params["position"] = dpg.get_item_pos(dpg_node_tag)
        params["model"] = dpg.get_value(dpg_node_tag + ":model")
        params["model_filepath"] = ""
        if dpg_node_tag in self.configs["model_filepaths"]:
            params["model_filepath"] = self.configs["model_filepaths"][dpg_node_tag]
        params["labels_filepath"] = ""
        if dpg_node_tag in self.configs["labels_filepaths"]:
            params["labels_filepath"] = self.configs["labels_filepaths"][dpg_node_tag]
        return params

    def set_import_params(self, node_id, params):
        dpg_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        if "model" in params:
            dpg.set_value(dpg_node_tag + ":model", params["model"])
        if "model_filepath" in params and os.path.exists(params["model_filepath"]):
            self.configs["model_filepaths"][dpg_node_tag] = params["model_filepath"]
            dpg.set_value(
                item=dpg_node_tag + ":modelfile:text",
                value="Select ONNX Model : selected",
            )
        if "labels_filepath" in params and os.path.exists(params["labels_filepath"]):
            self.configs["labels_filepaths"][dpg_node_tag] = params["labels_filepath"]
            dpg.set_value(
                item=dpg_node_tag + ":labelsfile:text",
                value="Select Model Labels : selected",
            )

    def callback_combo_link(self, sender, data, user_data):
        dpg_node_tag = user_data
        if dpg.get_value(dpg_node_tag + ":model") == "ONNX Model Classification":
            pass
        elif dpg.get_value(dpg_node_tag + ":model") == "ONNX Model Object Detector":
            pass

    def callback_button_connect(self, sender, data, user_data):
        dpg_node_tag = user_data
        if (
            dpg.get_item_label(dpg_node_tag + ":connect")
            == self.configs["label_connect"]
        ):
            if dpg_node_tag not in self.configs["instances"]:
                link_class = self.configs["models"][
                    dpg.get_value(dpg_node_tag + ":model")
                    if dpg.does_item_exist(dpg_node_tag + ":model")
                    else None
                ]
                dpg.set_item_label(dpg_node_tag + ":connect", "...")
                self.configs["instances"][dpg_node_tag] = link_class()
                if (
                    dpg_node_tag in self.configs["model_filepaths"]
                    and dpg_node_tag in self.configs["labels_filepaths"]
                ):
                    self.configs["instances"][dpg_node_tag].connect(
                        model_filepath=self.configs["model_filepaths"][dpg_node_tag],
                        labels_filepath=self.configs["labels_filepaths"][dpg_node_tag],
                    )
            if self.configs["instances"][dpg_node_tag].is_active:
                dpg.set_item_label(
                    dpg_node_tag + ":connect", self.configs["label_connected"]
                )
                dpg.disable_item(dpg_node_tag + ":model")
                dpg.disable_item(dpg_node_tag + ":modelfile")
                dpg.disable_item(dpg_node_tag + ":labelsfile")
                self.configs["statuses"][dpg_node_tag] = "active"
            else:
                del self.configs["instances"][dpg_node_tag]
                dpg.set_item_label(
                    dpg_node_tag + ":connect", self.configs["label_connect"]
                )
                dpg.show_item(dpg_node_tag + ":modal")
        elif (
            dpg.get_item_label(dpg_node_tag + ":connect")
            == self.configs["label_connected"]
        ):
            del self.configs["instances"][dpg_node_tag]
            dpg.set_item_label(dpg_node_tag + ":connect", self.configs["label_connect"])
            self.configs["statuses"][dpg_node_tag] = "inactive"
            dpg.enable_item(dpg_node_tag + ":model")
            dpg.enable_item(dpg_node_tag + ":modelfile")
            dpg.enable_item(dpg_node_tag + ":labelsfile")

    def callback_file_dialog_model(self, sender, app_data, user_data):
        dpg_node_tag = user_data
        self.configs["model_filepaths"][dpg_node_tag] = app_data["file_path_name"]
        dpg.set_value(
            item=dpg_node_tag + ":modelfile:text", value="Select ONNX Model : selected"
        )

    def callback_file_dialog_labels(self, sender, app_data, user_data):
        dpg_node_tag = user_data
        self.configs["labels_filepaths"][dpg_node_tag] = app_data["file_path_name"]
        dpg.set_value(
            item=dpg_node_tag + ":labelsfile:text",
            value="Select Model Labels : selected",
        )
