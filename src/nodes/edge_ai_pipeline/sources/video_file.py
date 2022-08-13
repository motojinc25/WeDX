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
        self.name = "Video File"
        self.theme_titlebar = [51, 102, 0]
        self.theme_titlebar_selected = [76, 153, 0]
        self.settings = settings
        self.logger = logger
        self.configs = {}
        self.configs["video_captures"] = {}
        self.configs["video_paths"] = {}
        self.configs["prev_video_paths"] = {}
        self.configs["frame_counts"] = {}
        self.forms = {}
        self.forms["loop"] = {}
        self.forms["skiprate"] = {}

    def add_node(self, parent, node_id, pos):
        # Describe node attribute tags
        dpg_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        dpg_pin_tags = self.get_tag_list(dpg_node_tag)
        self.forms["loop"][dpg_node_tag] = True
        self.forms["skiprate"][dpg_node_tag] = 1

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

            # Add file dialog for video file
            with dpg.file_dialog(
                directory_selector=False,
                show=False,
                modal=True,
                height=int(self.settings["node_height"] * 3),
                default_path=os.path.abspath(
                    os.path.join(
                        os.path.dirname(os.path.abspath(__file__)),
                        "../../../assets/videos/",
                    )
                ),
                user_data=dpg_node_tag,
                callback=self.callback_file_dialog,
                id="file_dialog_video:" + str(node_id),
            ):
                dpg.add_file_extension("Movie (*.mp4 *.avi){.mp4,.avi}")
                dpg.add_file_extension("", color=(150, 255, 150, 255))

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

                # Add a file dialog
                with dpg.node_attribute(
                    attribute_type=int(Attribute.STATIC),
                ):
                    dpg.add_spacer(height=5)
                    with dpg.group(horizontal=True):
                        dpg.add_button(
                            label="1",
                            tag=dpg_node_tag + ":video_file:0",
                            width=self.settings["node_width"] * 0.075,
                            user_data=dpg_node_tag + ":video_file:0",
                            callback=self.callback_show_video,
                        )
                        dpg.add_button(
                            label="2",
                            tag=dpg_node_tag + ":video_file:1",
                            width=self.settings["node_width"] * 0.075,
                            user_data=dpg_node_tag + ":video_file:1",
                            callback=self.callback_show_video,
                        )
                        dpg.add_button(
                            label="3",
                            tag=dpg_node_tag + ":video_file:2",
                            width=self.settings["node_width"] * 0.075,
                            user_data=dpg_node_tag + ":video_file:2",
                            callback=self.callback_show_video,
                        )
                        dpg.add_button(
                            label="Select Video File",
                            width=self.settings["node_width"] * 0.65,
                            callback=lambda: dpg.show_item(
                                "file_dialog_video:" + str(node_id)
                            ),
                        )

                # Add a checkbox for video loop and Add slider for skip rate
                with dpg.node_attribute(attribute_type=int(Attribute.STATIC)):
                    with dpg.group(horizontal=True):
                        dpg.add_checkbox(
                            label="Loop",
                            default_value=self.forms["loop"][dpg_node_tag],
                            callback=self.callback_change_loop,
                            user_data=dpg_node_tag,
                            tag=dpg_node_tag + ":loop",
                        )
                        dpg.add_slider_int(
                            label="SkipRate",
                            width=int(self.settings["node_width"] / 2),
                            default_value=self.forms["skiprate"][dpg_node_tag],
                            min_value=1,
                            max_value=10,
                            callback=self.callback_change_skiprate,
                            user_data=dpg_node_tag,
                            tag=dpg_node_tag + ":skiprate",
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
        movie_path = None
        prev_movie_path = None

        # Get video path
        if dpg_node_tag in self.configs["video_paths"]:
            movie_path = self.configs["video_paths"][dpg_node_tag]
        if dpg_node_tag in self.configs["prev_video_paths"]:
            prev_movie_path = self.configs["prev_video_paths"][dpg_node_tag]
        if prev_movie_path != movie_path:
            if dpg_node_tag in self.configs["video_captures"]:
                self.configs["video_captures"][dpg_node_tag].release()
            self.configs["video_captures"][dpg_node_tag] = cv2.VideoCapture(movie_path)
            self.configs["prev_video_paths"][dpg_node_tag] = movie_path
            self.configs["frame_counts"][dpg_node_tag] = 0
        loop_flag = self.forms["loop"][dpg_node_tag]
        skip_rate = int(self.forms["skiprate"][dpg_node_tag])

        # capturing from Video file
        if dpg_node_tag in self.configs["video_captures"]:
            while True:
                ret, frame = self.configs["video_captures"][dpg_node_tag].read()
                if not ret:
                    if loop_flag:
                        self.configs["video_captures"][dpg_node_tag].set(
                            cv2.CAP_PROP_POS_FRAMES, 0
                        )
                        _, frame = self.configs["video_captures"][dpg_node_tag].read()
                    else:
                        self.configs["video_captures"][dpg_node_tag].release()
                        del self.configs["video_captures"][dpg_node_tag]
                        del self.configs["video_paths"][dpg_node_tag]
                        self.configs["prev_video_paths"][dpg_node_tag]
                        break
                self.configs["frame_counts"][dpg_node_tag] += 1
                if (self.configs["frame_counts"][dpg_node_tag] % skip_rate) == 0:
                    break

            # Capture frame-by-frame
            if frame is not None:
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
                            "source": movie_path,
                            "width": self.configs["video_captures"][dpg_node_tag].get(
                                cv2.CAP_PROP_FRAME_WIDTH
                            ),
                            "height": self.configs["video_captures"][dpg_node_tag].get(
                                cv2.CAP_PROP_FRAME_HEIGHT
                            ),
                        },
                    }
                ]

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
        if dpg_node_tag in self.configs["prev_video_paths"]:
            del self.configs["prev_video_paths"][dpg_node_tag]
        if dpg_node_tag in self.configs["video_paths"]:
            del self.configs["video_paths"][dpg_node_tag]
        if self.settings["gui"]:
            dpg.delete_item(dpg_node_tag + ":texture")
            dpg.delete_item("file_dialog_video:" + str(node_id))
            dpg.delete_item(dpg_node_tag)

    def get_export_params(self, node_id):
        dpg_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        params = {}
        if self.settings["gui"]:
            params["version"] = self.version
            params["position"] = dpg.get_item_pos(dpg_node_tag)
            params["loop"] = (
                dpg.get_value(dpg_node_tag + ":loop")
                if dpg.does_item_exist(dpg_node_tag + ":loop")
                else None
            )
            params["skiprate"] = int(
                dpg.get_value(dpg_node_tag + ":skiprate")
                if dpg.does_item_exist(dpg_node_tag + ":skiprate")
                else None
            )
            params["video_filepath"] = ""
            if dpg_node_tag in self.configs["video_paths"]:
                params["video_filepath"] = self.configs["video_paths"][dpg_node_tag]
        return params

    def set_import_params(self, node_id, params):
        dpg_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        if self.settings["gui"]:
            if "loop" in params:
                dpg.set_value(dpg_node_tag + ":loop", params["loop"])
            if "skiprate" in params:
                dpg.set_value(dpg_node_tag + ":skiprate", params["skiprate"])
            if "video_filepath" in params and os.path.exists(params["video_filepath"]):
                self.configs["video_paths"][dpg_node_tag] = params["video_filepath"]

    def callback_file_dialog(self, sender, app_data, user_data):
        dpg_node_tag = user_data
        if app_data["file_name"] != ".":
            self.configs["video_paths"][dpg_node_tag] = app_data["file_path_name"]

    def callback_show_video(self, sender, app_data, user_data):
        node_id = user_data.split(":")[0]
        dpg_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        fileList = [
            "airport_-_36510(Original).mp4",
            "D0002161071_00000.mp4",
            "pexels-nataliya-vaitkevich-8830590.mp4",
        ]
        filePath = os.path.abspath(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "../../../assets/videos/",
                fileList[int(user_data.split(":")[3])],
            )
        )
        self.configs["video_paths"][dpg_node_tag] = filePath

    def callback_change_loop(self, sender, data, user_data):
        dpg_node_tag = user_data
        self.forms["loop"][dpg_node_tag] = data

    def callback_change_skiprate(self, sender, data, user_data):
        dpg_node_tag = user_data
        self.forms["skiprate"][dpg_node_tag] = data
