import os

import cv2
import dearpygui.dearpygui as dpg

from nodes.edge_ai_pipeline.base import BaseNode


class EdgeAINode(BaseNode):
    def __init__(self, settings):
        self.version = "0.1.0"
        self.name = "Image File"
        self.settings = settings
        self.configs = {}
        self.configs["images"] = {}
        self.configs["image_paths"] = {}
        self.configs["prev_image_paths"] = {}

    def add_node(self, parent, node_id, pos=[0, 0]):
        # Describe node attribute tags
        dag_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        dag_pin_tags = self.get_tag_list(dag_node_tag)

        # Add a dynamic texture and a raw texture
        with dpg.texture_registry(show=False):
            dpg.add_raw_texture(
                self.settings["node_width"],
                self.settings["node_height"],
                self.get_blank_texture(
                    self.settings["node_width"], self.settings["node_height"]
                ),
                tag=dag_node_tag + ":texture",
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
            callback=self.callback_file_dialog,
            id="file_dialog_image:" + str(node_id),
        ):
            dpg.add_file_extension(
                "Image (*.bmp *.jpg *.png *.gif){.bmp,.jpg,.png,.gif}"
            )
            dpg.add_file_extension("", color=(150, 255, 150, 255))

        # Add a node to a node editor
        with dpg.node(tag=dag_node_tag, parent=parent, label=self.name, pos=pos):
            # Add pins that allows linking inputs and outputs
            with dpg.node_attribute(
                attribute_type=dpg.mvNode_Attr_Output,
                tag=dag_pin_tags[self.VIDEO_OUT],
            ):
                dpg.add_text("VIDEO OUT")
            with dpg.node_attribute(
                attribute_type=dpg.mvNode_Attr_Output,
                shape=dpg.mvNode_PinShape_Quad,
                tag=dag_pin_tags[self.MESSAGE_OUT],
            ):
                dpg.add_text("MESSAGE OUT")

            # Add a file dialog
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static):
                dpg.add_spacer(height=5)
                dpg.add_button(
                    label="Select Image File",
                    width=self.settings["node_width"],
                    callback=lambda: dpg.show_item("file_dialog_image:" + str(node_id)),
                )

            # Add an image from a specified texture
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static):
                dpg.add_image(dag_node_tag + ":texture")

        # Return Dear PyGui Tag
        return dag_node_tag

    def update(self, node_id, node_links, node_frames, node_messages):
        dag_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        frame = None
        message = None

        # Get image path
        image_path = self.configs["image_paths"].get(str(node_id), None)
        prev_image_path = self.configs["prev_image_paths"].get(str(node_id), None)
        if prev_image_path != image_path:
            self.configs["images"][str(node_id)] = cv2.imread(
                image_path, cv2.IMREAD_UNCHANGED
            )
            self.configs["prev_image_paths"][str(node_id)] = image_path

        # Capture frame-by-frame
        frame = self.configs["images"].get(str(node_id), None)
        if frame is not None:
            texture = self.get_image_texture(
                frame, self.settings["node_width"], self.settings["node_height"]
            )
            if dpg.does_item_exist(dag_node_tag + ":texture"):
                dpg.set_value(dag_node_tag + ":texture", texture)

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

        # Return frame and message
        return frame, message

    def close(self, node_id):
        pass

    def delete(self, node_id):
        dag_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        dpg.delete_item(dag_node_tag + ":texture")
        dpg.delete_item("file_dialog_image:" + str(node_id))
        dpg.delete_item(dag_node_tag)

    def get_export_params(self, node_id):
        dag_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        params = {}
        params["version"] = self.version
        params["position"] = dpg.get_item_pos(dag_node_tag)
        return params

    def set_import_params(self, node_id, params):
        pass

    def callback_file_dialog(self, sender, app_data, user_data):
        if app_data["file_name"] != ".":
            node_id = sender.split(":")[1]
            self.configs["image_paths"][node_id] = app_data["file_path_name"]
