#!/usr/bin/env python
"""WeDX - Edge AI Pipeline functionality"""

import argparse
import json
import os
import sys
import webbrowser

import cv2
import dearpygui.dearpygui as dpg

from managers.edge_ai_pipeline_window import EdgeAIPipelineWindow
from version import __version__


def callback_open_website(sender, app_data, user_data):
    webbrowser.open(user_data)


def main():
    # Arguments
    current_path = os.path.dirname(os.path.abspath(__file__))
    parser = argparse.ArgumentParser()
    parser.add_argument(
        "--settings",
        type=str,
        default=os.path.abspath(os.path.join(current_path, ".wedx/settings.json")),
    )
    parser.add_argument("--skip_detect_cameras", action="store_true")
    parser.add_argument("--detect_camera_count", type=int, default=2)
    args = parser.parse_args()

    # Set window settings
    settings = None
    with open(args.settings) as fp:
        settings = json.load(fp)

    # Detect all connected usb cameras
    valid_usb_cameras = []
    caps = []
    if not args.skip_detect_cameras:
        for i in range(args.detect_camera_count):
            cap = cv2.VideoCapture(i)
            if cap.isOpened():
                valid_usb_cameras.append(i)
        for usb_camera in valid_usb_cameras:
            cap = cv2.VideoCapture(usb_camera)
            cap.set(cv2.CAP_PROP_FRAME_WIDTH, settings["usb_camera_width"])
            cap.set(cv2.CAP_PROP_FRAME_HEIGHT, settings["usb_camera_height"])
            caps.append(cap)
    settings["device_no_list"] = valid_usb_cameras
    settings["camera_capture_list"] = caps

    # Create Dear PyGui Context
    dpg.create_context()

    # Set default font
    with dpg.font_registry():
        font_file = os.path.abspath(
            os.path.join(current_path, "assets/fonts/NotoSansCJKjp-Regular.otf")
        )
        with dpg.font(font_file, 16) as regular_font:
            dpg.add_font_range_hint(dpg.mvFontRangeHint_Default)
            dpg.add_font_range_hint(dpg.mvFontRangeHint_Japanese)
            dpg.add_font_range_hint(dpg.mvFontRangeHint_Korean)
            dpg.add_font_range_hint(dpg.mvFontRangeHint_Chinese_Full)
            dpg.add_font_range_hint(dpg.mvFontRangeHint_Chinese_Simplified_Common)
        dpg.bind_font(regular_font)

    # Create Dear PyGui Viewport
    dpg.create_viewport(
        title="WeDX",
        width=settings["viewport_width"],
        height=settings["viewport_height"],
        x_pos=settings["viewport_pos"][0],
        y_pos=settings["viewport_pos"][1],
    )

    # About WeDX window
    with dpg.window(
        tag="about_wedx_window",
        label="About WeDX",
        min_size=(480, 350),
        show=False,
        pos=(100, 100),
    ):
        dpg.add_text(f"WeDX: {__version__}")
        dpg.add_spacer()
        dpg.add_separator()
        dpg.add_text("Authors", color=(0, 255, 255))
        dpg.add_text("Jingun Jung @ motojin.com, Inc.", bullet=True)
        dpg.add_text(
            "".join(
                (
                    "WeDX is licensed under the GPLv3 License, see LiCENSE for more information.\n",
                    "Repository: https://github.com/motojinc25/WeDX",
                )
            )
        )
        with dpg.group(horizontal=True):
            dpg.add_button(
                label="Open repository",
                callback=callback_open_website,
                user_data="https://github.com/motojinc25/WeDX",
            )
            dpg.add_button(
                label="About Jingun Jung",
                callback=callback_open_website,
                user_data="https://www.linkedin.com/in/jingun-jung",
            )
            dpg.add_button(
                label="About motojin.com, Inc.",
                callback=callback_open_website,
                user_data="https://motojin.com",
            )
        dpg.add_spacer()
        dpg.add_separator()
        dpg.add_spacer(height=5)
        with dpg.group(horizontal=True):
            dpg.add_text("Created with Dear PyGui")
            dpg.add_button(
                label="Show About", callback=lambda: dpg.show_tool(dpg.mvTool_About)
            )
            dpg.add_button(
                label="Open Demo source code",
                callback=callback_open_website,
                user_data="https://github.com/hoffstadt/DearPyGui/blob/master/dearpygui/demo.py",
            )
        dpg.add_spacer()
        dpg.add_separator()
        dpg.add_text("Special thanks", color=(0, 255, 255))
        dpg.add_text("Kazuhito Takahashi - Image-Processing-Node-Editor", bullet=True)
        dpg.add_text(
            "Repository: https://github.com/Kazuhito00/Image-Processing-Node-Editor"
        )
        dpg.add_button(
            label="Open repository",
            callback=callback_open_website,
            user_data="https://github.com/Kazuhito00/Image-Processing-Node-Editor",
        )
        dpg.add_spacer()
        dpg.add_separator()
        dpg.add_spacer(height=5)
        dpg.add_button(
            label="Close", callback=lambda: dpg.hide_item("about_wedx_window")
        )

    # Primary Menu Bar
    with dpg.viewport_menu_bar(label="Primary Menu Bar", tag="viewport-bar"):
        with dpg.menu(label="File"):
            dpg.add_menu_item(label="Exit", callback=lambda: dpg.stop_dearpygui())

        with dpg.menu(label="Tools"):
            dpg.add_menu_item(
                label="About WeDX",
                callback=lambda: dpg.show_item("about_wedx_window"),
                shortcut="Ctrl + H",
            )
            dpg.add_spacer()
            dpg.add_separator()
            dpg.add_spacer()
            dpg.add_menu_item(
                label="Show Metrics", callback=lambda: dpg.show_tool(dpg.mvTool_Metrics)
            )
            dpg.add_menu_item(
                label="Show Documentation",
                callback=lambda: dpg.show_tool(dpg.mvTool_Doc),
            )
            dpg.add_menu_item(
                label="Show Debug", callback=lambda: dpg.show_tool(dpg.mvTool_Debug)
            )
            dpg.add_menu_item(
                label="Show Style Editor",
                callback=lambda: dpg.show_tool(dpg.mvTool_Style),
            )
            dpg.add_menu_item(
                label="Show Font Manager",
                callback=lambda: dpg.show_tool(dpg.mvTool_Font),
            )
            dpg.add_menu_item(
                label="Show Item Registry",
                callback=lambda: dpg.show_tool(dpg.mvTool_ItemRegistry),
            )
            dpg.add_menu_item(
                label="Show Demo",
                callback=lambda: dpg.show_imgui_demo(),
            )

    # Primary Window
    with dpg.window(label="Primary Window", tag="primary-window") as primary_window:
        # Spacing guide: menu bar
        dpg.add_spacer(width=10, height=14)

        # Primary tab bar
        with dpg.tab_bar():
            # Edge AI Pipeline tab
            with dpg.tab(label="Edge AI Pipeline"):
                tab_edge = EdgeAIPipelineWindow(settings=settings)
                tab_edge.create_widgets()

        # Set the primary window
        dpg.set_primary_window(primary_window, True)

    # Setup Dear PyGui
    dpg.setup_dearpygui()

    # Show Dear PyGui Viewport
    dpg.show_viewport()

    # Below replaces, dpg.start_dearpygui() for updating nodes
    node_frames = {}
    node_messages = {}
    while dpg.is_dearpygui_running():
        node_list = tab_edge.get_node_list()
        for node_id_name in node_list:
            if node_id_name not in node_frames:
                node_frames[node_id_name] = None
            if node_id_name not in node_messages:
                node_messages[node_id_name] = None
            node_id, node_name = node_id_name.split(":")
            node_instance = tab_edge.get_node_instance(node_name)
            frame, message = node_instance.update(
                node_id,
                tab_edge.node_link_graph.get(node_id_name, []),
                node_frames,
                node_messages,
            )
            node_frames[node_id_name] = frame
            node_messages[node_id_name] = message

        # Render Dear PyGui frame
        dpg.render_dearpygui_frame()

    # Release nodes
    node_list = tab_edge.get_node_list()
    for node_id_name in node_list:
        node_id, node_name = node_id_name.split(":")
        node_instance = tab_edge.get_node_instance(node_name)
        node_instance.close(node_id)

    # When everything done, release the capture
    for cap in settings["camera_capture_list"]:
        cap.release()

    # Destroy Dear PyGui
    dpg.destroy_context()


if __name__ == "__main__":
    if not sys.version >= "3.8":
        raise Exception(
            "WeDX requires python 3.8+. Current version of Python: %s" % sys.version
        )
    sys.exit(main())
