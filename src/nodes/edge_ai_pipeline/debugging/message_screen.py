import json

import dearpygui.dearpygui as dpg

from nodes.edge_ai_pipeline.base import BaseNode


class EdgeAINode(BaseNode):
    def __init__(self, settings):
        self.version = "0.1.0"
        self.name = "Message Screen"
        self.settings = settings

    def add_node(self, parent, node_id, pos=[0, 0]):
        # Describe node attribute tags
        dag_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        dag_pin_tags = self.get_tag_list(dag_node_tag)

        # Add a node to a node editor
        with dpg.node(tag=dag_node_tag, parent=parent, label=self.name, pos=pos):
            # Add text for message
            with dpg.node_attribute(
                attribute_type=dpg.mvNode_Attr_Input,
                shape=dpg.mvNode_PinShape_Quad,
                tag=dag_pin_tags[self.MESSAGE_IN],
            ):
                dpg.add_input_text(
                    multiline=True,
                    readonly=True,
                    width=self.settings["debugging_width"],
                    height=self.settings["debugging_height"],
                    tag=dag_node_tag + ":message",
                )

        # Return Dear PyGui Tag
        return dag_node_tag

    def update(self, node_id, node_links, node_frames, node_messages):
        dag_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        message = None

        # Get linked node tag
        for link in node_links:
            link_pin_shape = link[0].split(":")[2]
            if link_pin_shape == str(dpg.mvNode_PinShape_Quad):
                linked_node_tag_message = ":".join(link[0].split(":")[:2])
                message = node_messages.get(linked_node_tag_message, None)

        # Update console
        if message is not None:
            if dpg.does_item_exist(dag_node_tag + ":message"):
                dpg.set_value(dag_node_tag + ":message", json.dumps(message, indent=2))

        # Return frame and message
        return None, None

    def close(self, node_id):
        pass

    def delete(self, node_id):
        dag_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        dpg.delete_item(dag_node_tag)

    def get_export_params(self, node_id):
        dag_node_tag = str(node_id) + ":" + self.name.lower().replace(" ", "_")
        params = {}
        params["version"] = self.version
        params["position"] = dpg.get_item_pos(dag_node_tag)
        return params

    def set_import_params(self, node_id, params):
        pass
