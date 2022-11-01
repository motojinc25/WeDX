from enum import IntEnum

tag = {
    "file_dialog": {
        "export_pipeline": "export_pipeline_file_dialog",
        "import_pipeline": "import_pipeline_file_dialog",
    },
    "window": {
        "primary": "primary_window",
        "about_wedx": "about_wedx_window",
        "iot_device_setting": "iot_device_setting_window",
        "logging_level_setting": "logging_level_setting_window",
        "check_for_updates":"check_for_updates_window"
    },
    "tab_bar": {
        "primary": "primary_tab_bar",
    },
    "tab": {
        "edge_ai_pipeline": "edge_ai_pipeline_tab",
    },
    "node_editor": {
        "edge_ai_pipeline": "edge_ai_pipeline_node_editor",
    },
}


class PinShape(IntEnum):
    CIRCLE = 0  # mvNode_PinShape_Circle
    CIRCLE_FILLED = 1  # mvNode_PinShape_CircleFilled
    TRIANGLE = 2  # mvNode_PinShape_Triangle
    TRIANGLE_FILLED = 3  # mvNode_PinShape_TriangleFilled
    QUAD = 4  # mvNode_PinShape_Quad
    QUAD_FILLED = 5  # mvNode_PinShape_QuadFilled


class Attribute(IntEnum):
    INPUT = 0  # mvNode_Attr_Input
    OUTPUT = 1  # mvNode_Attr_Output
    STATIC = 2  # mvNode_Attr_Static


class NoteState:
    CONNECT = "Connect"
    CONNECTED = "Connected"
