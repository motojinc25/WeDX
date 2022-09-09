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
        self.name = "Image File"
        self.theme_titlebar = [51, 102, 0]
        self.theme_titlebar_selected = [76, 153, 0]
        self.settings = settings
        self.logger = logger
        self.configs = {}
        self.configs["image_paths"] = {}
        self.configs["prev_image_paths"] = {}

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

            # Add file dialog for image file
            with dpg.file_dialog(
                directory_selector=False,
                show=False,
                modal=True,
                height=int(self.settings["node_height"] * 3),
                default_path=os.path.abspath(
                    os.path.join(
                        os.path.dirname(os.path.abspath(__file__)),
                        "../../../assets/images/",
                    )
                ),
                user_data=dpg_node_tag,
                callback=self.callback_file_dialog,
                id="file_dialog_image:" + str(node_id),
            ):
                dpg.add_file_extension(
                    "Image (*.bmp *.jpg *.png *.gif){.bmp,.jpg,.png,.gif}"
                )
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
                with dpg.node_attribute(attribute_type=int(Attribute.STATIC)):
                    dpg.add_spacer(height=5)
                    with dpg.group(horizontal=True):
                        dpg.add_button(
                            label="1",
                            tag=dpg_node_tag + ":image_file:0",
                            width=self.settings["node_width"] * 0.075,
                            user_data=dpg_node_tag + ":image_file:0",
                            callback=self.callback_show_image,
                        )
                        dpg.add_button(
                            label="2",
                            tag=dpg_node_tag + ":image_file:1",
                            width=self.settings["node_width"] * 0.075,
                            user_data=dpg_node_tag + ":image_file:1",
                            callback=self.callback_show_image,
                        )
                        dpg.add_button(
                            label="3",
                            tag=dpg_node_tag + ":image_file:2",
                            width=self.settings["node_width"] * 0.075,
                            user_data=dpg_node_tag + ":image_file:2",
                            callback=self.callback_show_image,
                        )
                        dpg.add_button(
                            label="Select Image File",
                            width=self.settings["node_width"] * 0.65,
                            callback=lambda: dpg.show_item(
                                "file_dialog_image:" + str(node_id)
                            ),
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
        image_path = None
        prev_image_path = None

        # Get image path
        if dpg_node_tag in self.configs["image_paths"]:
            image_path = self.configs["image_paths"][dpg_node_tag]
        if dpg_node_tag in self.configs["prev_image_paths"]:
            prev_image_path = self.configs["prev_image_paths"][dpg_node_tag]
        if prev_image_path != image_path:
            frame = cv2.imread(image_path, cv2.IMREAD_UNCHANGED)
            self.configs["prev_image_paths"][dpg_node_tag] = image_path

        # Capture frame-by-frame
        if frame is not None:
            texture = self.get_image_texture(
                frame, self.settings["node_width"], self.settings["node_height"]
            )
            if self.settings["gui"]:
                if dpg.does_item_exist(dpg_node_tag + ":texture"):
                    dpg.set_value(dpg_node_tag + ":texture", texture)

            # Generate message
            h, w, _ = frame.shape
            message = [
                {
                    "type": "source",
                    "subtype": self.name.lower().replace(" ", "_"),
                    "image": {
                        "source": image_path,
                        "width": w,
                        "height": h,
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
        if dpg_node_tag in self.configs["prev_image_paths"]:
            del self.configs["prev_image_paths"][dpg_node_tag]
        if dpg_node_tag in self.configs["image_paths"]:
            del self.configs["image_paths"][dpg_node_tag]
        if self.settings["gui"]:
            dpg.delete_item(dpg_node_tag + ":texture")
            dpg.delete_item("file_dialog_image:" + str(node_id))
            dpg.delete_item(dpg_node_tag)

    def get_export_params(self, node_id):
        dpg_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        params = {}
        params["version"] = self.version
        params["position"] = [0, 0]
        params["image_filepath"] = (
            self.configs["image_paths"][dpg_node_tag]
            if dpg_node_tag in self.configs["image_paths"]
            else ""
        )
        if self.settings["gui"]:
            params["position"] = dpg.get_item_pos(dpg_node_tag)
        return params

    def set_import_params(self, node_id, params):
        dpg_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        if "image_filepath" in params and os.path.exists(params["image_filepath"]):
            self.configs["image_paths"][dpg_node_tag] = params["image_filepath"]

    def callback_file_dialog(self, sender, app_data, user_data):
        dpg_node_tag = user_data
        if app_data["file_name"] != ".":
            self.configs["image_paths"][dpg_node_tag] = app_data["file_path_name"]

    def callback_show_image(self, sender, app_data, user_data):
        node_id = user_data.split(":")[0]
        dpg_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        fileList = [
            "computer-g09cdd0896_1920.jpg",
            "people-g18920d86d_1920.jpg",
            "students-gf264b6953_1920.jpg",
        ]
        filePath = os.path.abspath(
            os.path.join(
                os.path.dirname(os.path.abspath(__file__)),
                "../../../assets/images/",
                fileList[int(user_data.split(":")[3])],
            )
        )
        self.configs["image_paths"][dpg_node_tag] = filePath
