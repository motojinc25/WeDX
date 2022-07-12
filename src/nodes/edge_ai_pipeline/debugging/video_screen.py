import dearpygui.dearpygui as dpg

from nodes.edge_ai_pipeline.base import BaseNode


class EdgeAINode(BaseNode):
    def __init__(self, settings):
        self.version = "0.1.0"
        self.name = "Video Screen"
        self.settings = settings

    def add_node(self, parent, node_id, pos=[0, 0]):
        # Describe node attribute tags
        dpg_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        dpg_pin_tags = self.get_tag_list(dpg_node_tag)

        # Add a dynamic texture and a raw texture
        with dpg.texture_registry(show=False):
            dpg.add_raw_texture(
                self.settings["debugging_width"],
                self.settings["debugging_height"],
                self.get_blank_texture(
                    self.settings["debugging_width"], self.settings["debugging_height"]
                ),
                tag=dpg_node_tag + ":texture",
                format=dpg.mvFormat_Float_rgba,
            )

        # Add a node to a node editor
        with dpg.node(tag=dpg_node_tag, parent=parent, label=self.name, pos=pos):
            # Add an image from a specified texture and add pin
            with dpg.node_attribute(
                attribute_type=dpg.mvNode_Attr_Input,
                tag=dpg_pin_tags[self.VIDEO_IN],
            ):
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
        frame = node_frames.get(linked_node_tag, None)
        if frame is not None:
            texture = self.get_image_texture(
                frame, self.settings["debugging_width"], self.settings["debugging_height"]
            )
            if dpg.does_item_exist(dpg_node_tag + ":texture"):
                dpg.set_value(dpg_node_tag + ":texture", texture)

        # Return frame and message
        return None, None

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
        return params

    def set_import_params(self, node_id, params):
        pass
