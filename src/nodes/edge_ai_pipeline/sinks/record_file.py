import datetime
import os

import cv2
import dearpygui.dearpygui as dpg

from nodes.edge_ai_pipeline.base import BaseNode


class EdgeAINode(BaseNode):
    def __init__(self, settings):
        self.version = "0.1.0"
        self.name = "Record File"
        self.settings = settings
        self.configs = {}
        self.configs["video_writer_classes"] = {}
        self.configs["label_start"] = "Start"
        self.configs["label_stop"] = "Stop"
        self.configs["prev_frame_flag"] = False

    def add_node(self, parent, node_id, pos=[0, 0]):
        # Describe node attribute tags
        dpg_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        dpg_pin_tags = self.get_tag_list(dpg_node_tag)

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

            # Add a button for recording
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static):
                dpg.add_spacer(height=5)
                dpg.add_button(
                    label=self.configs["label_start"],
                    width=self.settings["node_width"],
                    callback=self.callback_button_recording,
                    user_data=dpg_node_tag,
                    tag=dpg_node_tag + ":record",
                )

            # Add an image from a specified texture
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static):
                dpg.add_image(dpg_node_tag + ":texture")

        # Return Dear PyGui Tag
        return dpg_node_tag

    def update(self, node_id, node_links, node_frames, node_messages):
        dpg_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")

        # Get linked node tag
        linked_node_tag = None
        for link in node_links:
            link_pin_shape = link[0].split(":")[2]
            if link_pin_shape == str(dpg.mvNode_PinShape_CircleFilled):
                linked_node_tag = ":".join(link[0].split(":")[:2])

        # Get frame
        linked_frame = node_frames.get(linked_node_tag, None)
        if linked_frame is not None:
            if dpg_node_tag in self.configs["video_writer_classes"]:
                frame = cv2.resize(
                    linked_frame,
                    (
                        self.settings["video_writer_width"],
                        self.settings["video_writer_height"],
                    ),
                )
                self.configs["video_writer_classes"][dpg_node_tag].write(frame)
            texture = self.get_image_texture(
                linked_frame,
                self.settings["node_width"],
                self.settings["node_height"],
            )
            if dpg.does_item_exist(dpg_node_tag + ":texture"):
                dpg.set_value(dpg_node_tag + ":texture", texture)
            self.configs["prev_frame_flag"] = True
        else:
            label = dpg.get_item_label(dpg_node_tag + ":record")
            if label == self.configs["label_stop"] and self.configs["prev_frame_flag"]:
                self.callback_button_recording(None, None, dpg_node_tag)
            self.configs["prev_frame_flag"] = False

        # Return Dear PyGui Tag
        return None, None

    def close(self, node_id):
        dpg_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        if dpg_node_tag in self.configs["video_writer_classes"]:
            self.configs["video_writer_classes"][dpg_node_tag].release()
            self.configs["video_writer_classes"].pop(dpg_node_tag)

    def delete(self, node_id):
        dpg_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        dpg.delete_item(dpg_node_tag + ":texture")
        dpg.delete_item(dpg_node_tag)

    def get_export_params(self, node_id):
        dpg_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        params = {}
        params["version"] = self.version
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
            if dpg_node_tag not in self.configs["video_writer_classes"]:
                self.configs["video_writer_classes"][dpg_node_tag] = cv2.VideoWriter(
                    video_writer_directory + "/" + startup_time_text + ".mp4",
                    cv2.VideoWriter_fourcc(*"mp4v"),
                    self.settings["video_writer_fps"],
                    (
                        self.settings["video_writer_width"],
                        self.settings["video_writer_height"],
                    ),
                )
            dpg.set_item_label(dpg_node_tag + ":record", self.configs["label_stop"])
        elif dpg.get_item_label(dpg_node_tag + ":record") == self.configs["label_stop"]:
            self.configs["video_writer_classes"][dpg_node_tag].release()
            self.configs["video_writer_classes"].pop(dpg_node_tag)
            dpg.set_item_label(dpg_node_tag + ":record", self.configs["label_start"])
