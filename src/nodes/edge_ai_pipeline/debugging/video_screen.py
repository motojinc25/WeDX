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
        self.name = "Video Screen"
        self.theme_titlebar = [0, 51, 102]
        self.theme_titlebar_selected = [0, 76, 153]
        self.settings = settings
        self.logger = logger
        self.configs = {}
        self.configs["video_input_count"] = {}
        self.configs["label_on"] = "ON"
        self.configs["label_off"] = "OFF"

    def add_node(self, parent, node_id, pos):
        # Describe node attribute tags
        dpg_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        dpg_pin_tags = self.get_tag_list(dpg_node_tag)
        self.configs["video_input_count"][dpg_node_tag] = 1

        if self.settings["gui"]:
            # Add a dynamic texture and a raw texture
            with dpg.texture_registry(show=False):
                dpg.add_raw_texture(
                    self.settings["debugging_width"],
                    self.settings["debugging_height"],
                    self.get_blank_texture(
                        self.settings["debugging_width"],
                        self.settings["debugging_height"],
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
                video_id = self.configs["video_input_count"][dpg_node_tag] - 1
                self.add_video_input_node_attribute(
                    dpg_node_tag, dpg_pin_tags, video_id, self.configs["label_on"]
                )

                # Add an image from a specified texture and add pin
                with dpg.node_attribute(
                    attribute_type=int(Attribute.STATIC),
                ):
                    dpg.add_image(dpg_node_tag + ":texture")

        # Return Dear PyGui Tag
        return dpg_node_tag

    async def refresh(self, node_id, node_links, node_frames, node_messages):
        dpg_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")

        if self.settings["gui"]:
            # Get linked node tag
            linked_node_tag = None
            for link in node_links:
                link_pin_shape = link[0].split(":")[2]
                video_id = link[1].split(":")[4]
                video_switch_tag = dpg_node_tag + ":video_switch:" + str(video_id)
                if (
                    link_pin_shape == str(int(PinShape.CIRCLE_FILLED))
                    and dpg.get_item_label(video_switch_tag) == self.configs["label_on"]
                ):
                    linked_node_tag = ":".join(link[0].split(":")[:2])

            # Get frame
            frame = node_frames.get(linked_node_tag, None)
            if frame is not None:
                texture = self.get_image_texture(
                    frame,
                    self.settings["debugging_width"],
                    self.settings["debugging_height"],
                )
                if dpg.does_item_exist(dpg_node_tag + ":texture"):
                    dpg.set_value(dpg_node_tag + ":texture", texture)

        # Return frame and message
        return None, None

    def close(self, node_id):
        pass

    def delete(self, node_id):
        dpg_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        del self.configs["video_input_count"][dpg_node_tag]
        if self.settings["gui"]:
            dpg.delete_item(dpg_node_tag + ":texture")
            dpg.delete_item(dpg_node_tag)

    def get_export_params(self, node_id):
        dpg_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        params = {}
        if self.settings["gui"]:
            params["version"] = self.version
            params["position"] = dpg.get_item_pos(dpg_node_tag)
            params["video_input_count"] = self.configs["video_input_count"][
                dpg_node_tag
            ]
        return params

    def set_import_params(self, node_id, params):
        dpg_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        dpg_pin_tags = self.get_tag_list(dpg_node_tag)
        if self.settings["gui"]:
            if "video_input_count" in params:
                self.configs["video_input_count"][dpg_node_tag] = params[
                    "video_input_count"
                ]
                for video_id in range(
                    1, self.configs["video_input_count"][dpg_node_tag]
                ):
                    self.add_video_input_node_attribute(
                        dpg_node_tag, dpg_pin_tags, video_id, self.configs["label_off"]
                    )

    def add_video_input_node_attribute(
        self, dpg_node_tag, dpg_pin_tags, video_id, label
    ):
        with dpg.node_attribute(
            parent=dpg_node_tag,
            attribute_type=int(Attribute.INPUT),
            before=dpg_node_tag + ":button",
            tag=dpg_pin_tags[self.VIDEO_IN] + ":" + str(video_id),
        ):
            with dpg.group(horizontal=True):
                dpg.add_text("VIDEO IN")
                dpg.add_button(
                    label=label,
                    width=self.settings["node_width"] - 200,
                    callback=self.callback_button_switch,
                    user_data=dpg_node_tag + ":video_switch:" + str(video_id),
                    tag=dpg_node_tag + ":video_switch:" + str(video_id),
                )

    def callback_button_add(self, sender, data, user_data):
        dpg_node_tag = user_data
        dpg_pin_tags = self.get_tag_list(dpg_node_tag)
        self.configs["video_input_count"][dpg_node_tag] += 1
        video_id = self.configs["video_input_count"][dpg_node_tag] - 1
        self.add_video_input_node_attribute(
            dpg_node_tag, dpg_pin_tags, video_id, self.configs["label_off"]
        )

    def callback_button_switch(self, sender, data, user_data):
        button_dpg_node_tag = user_data
        node_id = user_data.split(":")[0]
        dpg_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        for video_id in range(self.configs["video_input_count"][dpg_node_tag]):
            dpg.set_item_label(
                dpg_node_tag + ":video_switch:" + str(video_id),
                self.configs["label_off"],
            )
        if dpg.get_item_label(button_dpg_node_tag) == self.configs["label_off"]:
            dpg.set_item_label(button_dpg_node_tag, self.configs["label_on"])
        else:
            dpg.set_item_label(button_dpg_node_tag, self.configs["label_off"])
