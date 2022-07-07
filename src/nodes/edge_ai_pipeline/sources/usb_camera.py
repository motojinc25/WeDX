import dearpygui.dearpygui as dpg

from nodes.edge_ai_pipeline.base import BaseNode


class EdgeAINode(BaseNode):
    def __init__(self, settings):
        self.version = "0.1.0"
        self.name = "USB Camera"
        self.settings = settings

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

            # Add a combo dropdown that allows selecting usb camera device number
            with dpg.node_attribute(attribute_type=dpg.mvNode_Attr_Static):
                dpg.add_spacer(height=5)
                dpg.add_combo(
                    self.settings["device_no_list"],
                    width=self.settings["node_width"] - 100,
                    label="Device",
                    tag=dag_node_tag + ":device",
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

        # Video capturing from USB Camera
        device_no = (
            dpg.get_value(dag_node_tag + ":device")
            if dpg.does_item_exist(dag_node_tag + ":device")
            else None
        )
        if device_no != "":
            device_no = int(device_no)
            camera_index = self.settings["device_no_list"].index(device_no)
            camera_capture = self.settings["camera_capture_list"][camera_index]

            # Capture frame-by-frame
            if camera_capture is not None:
                ret, frame = camera_capture.read()
                if ret == True:
                    texture = self.get_image_texture(
                        frame, self.settings["node_width"], self.settings["node_height"]
                    )
                    if dpg.does_item_exist(dag_node_tag + ":texture"):
                        dpg.set_value(dag_node_tag + ":texture", texture)

            # Generate message
            message = [
                {
                    "type": "source",
                    "subtype": self.name.lower().replace(" ", "_"),
                    "image": {
                        "source": device_no,
                        "width": self.settings["usb_camera_width"],
                        "height": self.settings["usb_camera_height"],
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
        dpg.delete_item(dag_node_tag)

    def get_export_params(self, node_id):
        dag_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        params = {}
        params["version"] = self.version
        params["position"] = dpg.get_item_pos(dag_node_tag)
        return params

    def set_import_params(self, node_id, params):
        pass
