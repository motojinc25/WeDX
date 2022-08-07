import json
import logging

from gui.constants import Attribute, PinShape
from nodes.edge_ai_pipeline.base import BaseNode

try:
    import dearpygui.dearpygui as dpg
except ImportError:
    pass


class EdgeAINode(BaseNode):
    def __init__(self, settings, logger=logging.getLogger(__name__)):
        self.version = "0.1.0"
        self.name = "Message Screen"
        self.theme_titlebar = [0, 51, 102]
        self.theme_titlebar_selected = [0, 76, 153]
        self.settings = settings
        self.logger = logger
        self.configs = {}
        self.configs["message_input_count"] = {}
        self.configs["label_on"] = "ON"
        self.configs["label_off"] = "OFF"

    def add_node(self, parent, node_id, pos):
        # Describe node attribute tags
        dpg_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        dpg_pin_tags = self.get_tag_list(dpg_node_tag)
        self.configs["message_input_count"][dpg_node_tag] = 1

        if self.settings["gui"]:
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

                # Add a button for adding source
                with dpg.node_attribute(
                    attribute_type=int(Attribute.STATIC),
                    tag=dpg_node_tag + ":button",
                ):
                    dpg.add_button(
                        label="+",
                        width=self.settings["node_width"] - 200,
                        callback=self.callback_button_add,
                        user_data=dpg_node_tag,
                        tag=dpg_node_tag + ":add",
                    )

                # Add pins that allows linking inputs and outputs
                message_id = self.configs["message_input_count"][dpg_node_tag] - 1
                self.add_message_input_node_attribute(
                    dpg_node_tag, dpg_pin_tags, message_id, self.configs["label_on"]
                )

                # Add text for message
                with dpg.node_attribute(
                    attribute_type=int(Attribute.STATIC),
                ):
                    dpg.add_input_text(
                        multiline=True,
                        readonly=True,
                        width=self.settings["debugging_width"],
                        height=self.settings["debugging_height"],
                        tag=dpg_node_tag + ":message",
                    )

        # Return Dear PyGui Tag
        return dpg_node_tag

    async def refresh(self, node_id, node_links, node_frames, node_messages):
        dpg_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        message = None

        if self.settings["gui"]:
            # Get linked node tag
            for link in node_links:
                link_pin_shape = link[0].split(":")[2]
                message_id = link[1].split(":")[4]
                message_switch_tag = dpg_node_tag + ":message_switch:" + str(message_id)
                if (
                    link_pin_shape == str(int(PinShape.QUAD))
                    and dpg.get_item_label(message_switch_tag)
                    == self.configs["label_on"]
                ):
                    linked_node_tag_message = ":".join(link[0].split(":")[:2])
                    message = node_messages.get(linked_node_tag_message, None)

            # Update console
            if message is not None:
                if dpg.does_item_exist(dpg_node_tag + ":message"):
                    dpg.set_value(
                        dpg_node_tag + ":message", json.dumps(message, indent=2)
                    )

        # Return frame and message
        return None, None

    def close(self, node_id):
        pass

    def delete(self, node_id):
        dpg_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        del self.configs["message_input_count"][dpg_node_tag]
        if self.settings["gui"]:
            dpg.delete_item(dpg_node_tag)

    def get_export_params(self, node_id):
        dpg_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        params = {}
        if self.settings["gui"]:
            params["version"] = self.version
            params["position"] = dpg.get_item_pos(dpg_node_tag)
            params["message_input_count"] = self.configs["message_input_count"][
                dpg_node_tag
            ]
        return params

    def set_import_params(self, node_id, params):
        dpg_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        dpg_pin_tags = self.get_tag_list(dpg_node_tag)
        if self.settings["gui"]:
            if "message_input_count" in params:
                self.configs["message_input_count"][dpg_node_tag] = params[
                    "message_input_count"
                ]
                for message_id in range(
                    1, self.configs["message_input_count"][dpg_node_tag]
                ):
                    self.add_message_input_node_attribute(
                        dpg_node_tag,
                        dpg_pin_tags,
                        message_id,
                        self.configs["label_off"],
                    )

    def add_message_input_node_attribute(
        self, dpg_node_tag, dpg_pin_tags, message_id, label
    ):
        with dpg.node_attribute(
            parent=dpg_node_tag,
            attribute_type=int(Attribute.INPUT),
            shape=int(PinShape.QUAD),
            before=dpg_node_tag + ":button",
            tag=dpg_pin_tags[self.MESSAGE_IN] + ":" + str(message_id),
        ):
            with dpg.group(horizontal=True):
                dpg.add_text("MESSAGE IN")
                dpg.add_button(
                    label=label,
                    width=self.settings["node_width"] - 200,
                    callback=self.callback_button_switch,
                    user_data=dpg_node_tag + ":message_switch:" + str(message_id),
                    tag=dpg_node_tag + ":message_switch:" + str(message_id),
                )

    def callback_button_add(self, sender, data, user_data):
        dpg_node_tag = user_data
        dpg_pin_tags = self.get_tag_list(dpg_node_tag)
        self.configs["message_input_count"][dpg_node_tag] += 1
        message_id = self.configs["message_input_count"][dpg_node_tag] - 1
        self.add_message_input_node_attribute(
            dpg_node_tag, dpg_pin_tags, message_id, self.configs["label_off"]
        )

    def callback_button_switch(self, sender, data, user_data):
        button_dpg_node_tag = user_data
        node_id = user_data.split(":")[0]
        dpg_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        for message_id in range(self.configs["message_input_count"][dpg_node_tag]):
            dpg.set_item_label(
                dpg_node_tag + ":message_switch:" + str(message_id),
                self.configs["label_off"],
            )
        if dpg.get_item_label(button_dpg_node_tag) == self.configs["label_off"]:
            dpg.set_item_label(button_dpg_node_tag, self.configs["label_on"])
        else:
            dpg.set_item_label(button_dpg_node_tag, self.configs["label_off"])
