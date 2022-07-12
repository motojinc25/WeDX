import os

import cv2
import dearpygui.dearpygui as dpg

from nodes.edge_ai_pipeline.base import BaseNode


class EdgeAINode(BaseNode):
    def __init__(self, settings):
        self.version = "0.1.0"
        self.name = "Video File"
        self.settings = settings
        self.configs = {}
        self.configs["video_captures"] = {}
        self.configs["movie_paths"] = {}
        self.configs["prev_movie_paths"] = {}
        self.configs["frame_counts"] = {}

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
            callback=self.callback_file_dialog,
            id="file_dialog_video:" + str(node_id),
        ):
            dpg.add_file_extension("Movie (*.mp4 *.avi){.mp4,.avi}")
            dpg.add_file_extension("", color=(150, 255, 150, 255))

        # Add a node to a node editor
        with dpg.node(tag=dpg_node_tag, parent=parent, label=self.name, pos=pos):
            # Add pins that allows linking inputs and outputs
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

            # Add a file dialog
            with dpg.node_attribute(
                attribute_type=dpg.mvNode_Attr_Static,
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
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static):
                with dpg.group(horizontal=True):
                    dpg.add_checkbox(
                        label="Loop",
                        tag=dpg_node_tag + ":loop",
                        user_data=dpg_node_tag,
                        default_value=True,
                    )
                    dpg.add_slider_int(
                        tag=dpg_node_tag + ":skiprate",
                        label="SkipRate",
                        width=int(self.settings["node_width"] / 2),
                        default_value=1,
                        min_value=1,
                        max_value=10,
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

        # Get video path
        movie_path = self.configs["movie_paths"].get(str(node_id), None)
        prev_movie_path = self.configs["prev_movie_paths"].get(str(node_id), None)
        if prev_movie_path != movie_path:
            video_capture = self.configs["video_captures"].get(str(node_id), None)
            if video_capture is not None:
                video_capture.release()
            self.configs["video_captures"][str(node_id)] = cv2.VideoCapture(movie_path)
            self.configs["prev_movie_paths"][str(node_id)] = movie_path
            self.configs["frame_counts"][str(node_id)] = 0
        video_capture = self.configs["video_captures"].get(str(node_id), None)
        loop_flag = (
            dpg.get_value(dpg_node_tag + ":loop")
            if dpg.does_item_exist(dpg_node_tag + ":loop")
            else None
        )
        skip_rate = int(
            dpg.get_value(dpg_node_tag + ":skiprate")
            if dpg.does_item_exist(dpg_node_tag + ":skiprate")
            else None
        )

        # capturing from Video file
        if video_capture is not None:
            while True:
                ret, frame = video_capture.read()
                if not ret:
                    if loop_flag:
                        video_capture.set(cv2.CAP_PROP_POS_FRAMES, 0)
                        _, frame = video_capture.read()
                    else:
                        video_capture.release()
                        video_capture = None
                        self.configs["movie_paths"].pop(str(node_id))
                        self.configs["prev_movie_paths"].pop(str(node_id))
                        self.configs["video_captures"].pop(str(node_id))
                        break
                self.configs["frame_counts"][str(node_id)] += 1
                if (self.configs["frame_counts"][str(node_id)] % skip_rate) == 0:
                    break

            # Capture frame-by-frame
            if frame is not None:
                texture = self.get_image_texture(
                    frame, self.settings["node_width"], self.settings["node_height"]
                )
                if dpg.does_item_exist(dpg_node_tag + ":texture"):
                    dpg.set_value(dpg_node_tag + ":texture", texture)

                # Generate message
                message = [
                    {
                        "type": "source",
                        "subtype": self.name.lower().replace(" ", "_"),
                        "image": {
                            "source": movie_path,
                            "width": video_capture.get(cv2.CAP_PROP_FRAME_WIDTH),
                            "height": video_capture.get(cv2.CAP_PROP_FRAME_HEIGHT),
                        },
                    }
                ]

        # Return frame and message
        return frame, message

    def close(self, node_id):
        pass

    def delete(self, node_id):
        dpg_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        dpg.delete_item(dpg_node_tag + ":texture")
        dpg.delete_item("file_dialog_video:" + str(node_id))
        dpg.delete_item(dpg_node_tag)

    def get_export_params(self, node_id):
        dpg_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        params = {}
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
        return params

    def set_import_params(self, node_id, params):
        dpg_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        if dpg.does_item_exist(dpg_node_tag + ":loop"):
            dpg.set_value(dpg_node_tag + ":loop", params["loop"])
        if dpg.does_item_exist(dpg_node_tag + ":skiprate"):
            dpg.set_value(dpg_node_tag + ":skiprate", params["skiprate"])

    def callback_file_dialog(self, sender, app_data, user_data):
        if app_data["file_name"] != ".":
            node_id = sender.split(":")[1]
            self.configs["movie_paths"][node_id] = app_data["file_path_name"]

    def callback_show_video(self, sender, app_data, user_data):
        node_id = user_data.split(":")[0]
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
        self.configs["movie_paths"][node_id] = filePath
