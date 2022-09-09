import datetime
import logging
import os

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
        self.name = "Record File"
        self.theme_titlebar = [102, 0, 102]
        self.theme_titlebar_selected = [153, 0, 153]
        self.settings = settings
        self.logger = logger
        self.configs = {}
        self.configs["video_writers"] = {}
        self.configs["prev_frame_flags"] = {}
        self.configs["label_start"] = "Start"
        self.configs["label_stop"] = "Stop"
        self.configs["video_fps"] = {}
        self.configs["timer_on"] = {}
        self.configs["timer_sec"] = {}
        self.configs["start_time"] = {}

    def add_node(self, parent, node_id, pos):
        # Describe node attribute tags
        dpg_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        dpg_pin_tags = self.get_tag_list(dpg_node_tag)

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

                # Add inputs for timer
                with dpg.node_attribute(attribute_type=int(Attribute.STATIC)):
                    dpg.add_spacer(height=5)
                    dpg.add_input_int(
                        label="Timer(sec)",
                        width=self.settings["node_width"] - 100,
                        show=True,
                        min_value=0,
                        default_value=0,
                        tag=dpg_node_tag + ":timer",
                    )
                    dpg.add_text(
                        default_value="?.mp4",
                        tag=dpg_node_tag + ":filepath",
                    )

                # Add a button for recording
                with dpg.node_attribute(attribute_type=int(Attribute.STATIC)):
                    dpg.add_button(
                        label=self.configs["label_start"],
                        width=self.settings["node_width"],
                        callback=self.callback_button_recording,
                        user_data=dpg_node_tag,
                        tag=dpg_node_tag + ":record",
                    )

                # Add an image from a specified texture
                with dpg.node_attribute(attribute_type=int(Attribute.STATIC)):
                    dpg.add_image(dpg_node_tag + ":texture")

        # Return Dear PyGui Tag
        return dpg_node_tag

    async def refresh(self, node_id, node_links, node_frames, node_messages):
        dpg_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        if dpg_node_tag not in self.configs["prev_frame_flags"]:
            self.configs["prev_frame_flags"][dpg_node_tag] = False

        # Get linked node tag
        linked_node_tag = None
        for link in node_links:
            link_pin_shape = link[0].split(":")[2]
            if link_pin_shape == str(int(PinShape.CIRCLE_FILLED)):
                linked_node_tag = ":".join(link[0].split(":")[:2])

        # Get frame
        linked_frame = node_frames.get(linked_node_tag, None)
        if linked_frame is not None:
            if dpg_node_tag in self.configs["video_writers"]:
                frame = cv2.resize(
                    linked_frame,
                    (
                        self.settings["video_writer_width"],
                        self.settings["video_writer_height"],
                    ),
                )
                self.configs["video_writers"][dpg_node_tag].write(frame)

                # Check if fps change
                if dpg_node_tag in self.configs["video_fps"]:
                    if self.configs["video_fps"][dpg_node_tag] != self.settings["fps"]:
                        self.configs["video_fps"][dpg_node_tag] = self.settings["fps"]
                        if dpg_node_tag in self.configs["video_writers"]:
                            self.configs["video_writers"][dpg_node_tag].release()
                            del self.configs["video_writers"][dpg_node_tag]
                            if self.settings["gui"]:
                                dpg.set_item_label(
                                    dpg_node_tag + ":record",
                                    self.configs["label_start"],
                                )
                        self.callback_button_recording(None, None, dpg_node_tag)

                # Timer
                if dpg_node_tag in self.configs["timer_on"]:
                    if self.configs["timer_on"][dpg_node_tag]:
                        left_time = (
                            self.configs["timer_sec"][dpg_node_tag]
                            - (
                                datetime.datetime.now()
                                - self.configs["start_time"][dpg_node_tag]
                            ).seconds
                        )

                        # Stop recording
                        if left_time <= 0:
                            self.configs["timer_on"][dpg_node_tag] = False
                            self.configs["video_writers"][dpg_node_tag].release()
                            del self.configs["video_writers"][dpg_node_tag]
                            if self.settings["gui"]:
                                dpg.set_item_label(
                                    dpg_node_tag + ":record",
                                    self.configs["label_start"],
                                )
                                dpg.enable_item(dpg_node_tag + ":timer")
                        if left_time >= 0:
                            if self.settings["gui"]:
                                dpg.set_value(dpg_node_tag + ":timer", left_time)
                    else:
                        self.configs["timer_on"][dpg_node_tag] = False

            texture = self.get_image_texture(
                linked_frame,
                self.settings["node_width"],
                self.settings["node_height"],
            )
            if self.settings["gui"]:
                if dpg.does_item_exist(dpg_node_tag + ":texture"):
                    dpg.set_value(dpg_node_tag + ":texture", texture)
            self.configs["prev_frame_flags"][dpg_node_tag] = True
        else:
            if self.settings["gui"]:
                label = dpg.get_item_label(dpg_node_tag + ":record")
                if (
                    label == self.configs["label_stop"]
                    and self.configs["prev_frame_flags"][dpg_node_tag]
                ):
                    self.callback_button_recording(None, None, dpg_node_tag)
                self.configs["prev_frame_flags"][dpg_node_tag] = False

        # Return Dear PyGui Tag
        return None, None

    def close(self, node_id):
        dpg_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        if dpg_node_tag in self.configs["video_writers"]:
            self.configs["video_writers"][dpg_node_tag].release()
            del self.configs["video_writers"][dpg_node_tag]

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
        if self.settings["gui"]:
            params["position"] = dpg.get_item_pos(dpg_node_tag)
        return params

    def set_import_params(self, node_id, params):
        pass

    def callback_button_recording(self, sender, data, user_data):
        dpg_node_tag = user_data
        if dpg.get_item_label(dpg_node_tag + ":record") == self.configs["label_start"]:
            datetime_now = datetime.datetime.now()
            startup_time_text = datetime_now.strftime("%Y%m%d_%H%M%S")
            video_writer_directory = self.settings["video_writer_directory"]
            os.makedirs(video_writer_directory, exist_ok=True)

            # Set timer
            duration = dpg.get_value(dpg_node_tag + ":timer")
            if int(duration) > 0:
                self.configs["timer_on"][dpg_node_tag] = True
                self.configs["timer_sec"][dpg_node_tag] = int(duration)
                self.configs["start_time"][dpg_node_tag] = datetime.datetime.now()
            fileName = video_writer_directory + "/" + startup_time_text + ".mp4"
            if dpg_node_tag not in self.configs["video_writers"]:
                self.configs["video_writers"][dpg_node_tag] = cv2.VideoWriter(
                    fileName,
                    cv2.VideoWriter_fourcc(*"mp4v"),
                    self.settings["fps"],
                    (
                        self.settings["video_writer_width"],
                        self.settings["video_writer_height"],
                    ),
                )
            dpg.set_item_label(dpg_node_tag + ":record", self.configs["label_stop"])
            dpg.disable_item(dpg_node_tag + ":timer")
            self.configs["video_fps"][dpg_node_tag] = self.settings["fps"]

            # Update record file
            dpg.set_value(dpg_node_tag + ":filepath", fileName)
        elif dpg.get_item_label(dpg_node_tag + ":record") == self.configs["label_stop"]:
            self.configs["video_writers"][dpg_node_tag].release()
            self.configs["timer_on"][dpg_node_tag] = False
            del self.configs["video_writers"][dpg_node_tag]
            dpg.set_item_label(dpg_node_tag + ":record", self.configs["label_start"])
            dpg.enable_item(dpg_node_tag + ":timer")
