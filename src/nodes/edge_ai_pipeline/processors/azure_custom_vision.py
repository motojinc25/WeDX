import copy

import dearpygui.dearpygui as dpg

from links.azure_custom_vision_api.link import AzureCustomVisionAPI
from nodes.edge_ai_pipeline.base import BaseNode


class EdgeAINode(BaseNode):
    def __init__(self, settings):
        self.version = "0.1.0"
        self.name = "Azure Custom Vision"
        self.settings = settings
        self.configs = {}
        self.configs["links"] = {
            "Prediction API": AzureCustomVisionAPI,
        }
        self.configs["instances"] = {}
        self.configs["state"] = {}
        self.configs["message"] = {}
        self.configs["label_start"] = "Connect"
        self.configs["label_stop"] = "Prediction"

    def add_node(self, parent, node_id, pos=[0, 0]):
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
        with dpg.node(tag=dpg_node_tag, parent=parent, label=self.name, pos=pos):
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
                    list(self.configs["links"].keys()),
                    default_value=list(self.configs["links"].keys())[0],
                    width=self.settings["node_width"],
                    callback=self.callback_combo_link,
                    user_data=dpg_node_tag,
                    tag=dpg_node_tag + ":link",
                )

            # Add inputs for credentials
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static):
                dpg.add_input_text(
                    label="URL",
                    no_spaces=True,
                    width=self.settings["node_width"] - 50,
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
                    tag=dpg_node_tag + ":key",
                )
                with dpg.tooltip(dpg_node_tag + ":key"):
                    dpg.add_text(
                        "Prediction API Key",
                        tag=dpg_node_tag + ":key:tooltip",
                    )

            # Add a button for prediction
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static):
                dpg.add_button(
                    label=self.configs["label_start"],
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
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static):
                dpg.add_image(dpg_node_tag + ":texture")

        # Return Dear PyGui Tag
        return dpg_node_tag

    def update(self, node_id, node_links, node_frames, node_messages):
        dpg_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        frame = None
        message = None

        # Get linked node tag
        linked_node_tag = None
        for link in node_links:
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
            if (
                dpg.get_item_label(dpg_node_tag + ":connect")
                == self.configs["label_stop"]
            ):
                if dpg_node_tag in self.configs["instances"]:
                    if dpg_node_tag in self.configs["state"]:
                        if self.configs["state"][dpg_node_tag] == "active":
                            dpg.configure_item(dpg_node_tag + ":loading", show=True)
                            frame, inference_message = self.configs["instances"][
                                dpg_node_tag
                            ](frame)
                            self.configs["message"][dpg_node_tag] = inference_message
                            self.configs["state"][dpg_node_tag] = "inactive"
                            dpg.configure_item(dpg_node_tag + ":loading", show=False)

            # Draw landmarks
            if dpg_node_tag in self.configs["message"]:
                frame = self.configs["instances"][dpg_node_tag].draw_landmarks(
                    frame, self.configs["message"][dpg_node_tag]
                )

                # Generate message
                if message is None:
                    message = []
                message.append(
                    {
                        "type": "processor",
                        "subtype": self.name.lower().replace(" ", "_"),
                        "inference": self.configs["message"][dpg_node_tag],
                    }
                )

            # Update texture
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
        dpg.delete_item(dpg_node_tag + ":texture")
        dpg.delete_item(dpg_node_tag)

    def get_export_params(self, node_id):
        dpg_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        params = {}
        params["version"] = self.version
        params["position"] = dpg.get_item_pos(dpg_node_tag)
        params["model"] = (
            dpg.get_value(dpg_node_tag + ":model")
            if dpg.does_item_exist(dpg_node_tag + ":model")
            else None
        )
        return params

    def set_import_params(self, node_id, params):
        dpg_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        if dpg.does_item_exist(dpg_node_tag + ":model"):
            dpg.set_value(dpg_node_tag + ":model", params["model"])

    def callback_combo_link(self, sender, data, user_data):
        dpg_node_tag = user_data
        if dpg.get_value(dpg_node_tag + ":link") == "Prediction API":
            pass

    def callback_button_connect(self, sender, data, user_data):
        dpg_node_tag = user_data
        if dpg.get_item_label(dpg_node_tag + ":connect") == self.configs["label_start"]:
            if dpg_node_tag not in self.configs["instances"]:
                link_class = self.configs["links"][
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
                    dpg_node_tag + ":connect", self.configs["label_stop"]
                )
                dpg.disable_item(dpg_node_tag + ":link")
                self.configs["state"][dpg_node_tag] = "inactive"
            else:
                del self.configs["instances"][dpg_node_tag]
                dpg.set_item_label(
                    dpg_node_tag + ":connect", self.configs["label_start"]
                )
                dpg.show_item(dpg_node_tag + ":modal")
        elif (
            dpg.get_item_label(dpg_node_tag + ":connect") == self.configs["label_stop"]
        ):
            self.configs["state"][dpg_node_tag] = "active"
