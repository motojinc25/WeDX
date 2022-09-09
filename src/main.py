#!/usr/bin/env python
"""WeDX - Building Edge AI Pipeline with No-Code"""

import argparse
import asyncio
import graphlib
import json
import logging
import logging.config
import multiprocessing
import multiprocessing.shared_memory as shared_memory
import os
import subprocess
import sys
import time

import cv2
import numpy as np

from gui.constants import tag
from gui.studio import WeDXStudio
from links.mq_req_rep.link import MessageQueueReqRep
from managers.edge_ai_pipeline import EdgeAIPipeline
from managers.user_preferences import UserPreferences
from servers.netron import NetronServer
from servers.webapi import run_api


async def refresh_frame(edge_ai_pipeline, dpg_node_tag, node_frames, node_messages):
    if dpg_node_tag not in node_frames:
        node_frames[dpg_node_tag] = None
    if dpg_node_tag not in node_messages:
        node_messages[dpg_node_tag] = None
    node_id, node_name = dpg_node_tag.split(":")
    node_instance = edge_ai_pipeline.get_node_instance(node_name)
    frame, message = await node_instance.refresh(
        node_id,
        edge_ai_pipeline.node_link_graph.get(dpg_node_tag, []),
        node_frames,
        node_messages,
    )
    node_frames[dpg_node_tag] = frame
    node_messages[dpg_node_tag] = message
    await asyncio.sleep(0)


async def main():
    # Arguments
    current_path = os.path.dirname(os.path.abspath(__file__))
    parser = argparse.ArgumentParser()
    parser.add_argument("--skip_detect_cameras", action="store_true")
    parser.add_argument("--no_gui", action="store_true")
    parser.add_argument("--no_webapi", action="store_true")
    parser.add_argument("--no_webapp", action="store_true")
    parser.add_argument("--iotedge", action="store_true")
    args = parser.parse_args()

    # Set window settings
    settings = None
    with open(os.path.abspath(os.path.join(current_path, ".wedx/settings.json"))) as fp:
        settings = json.load(fp)

    # Set Logger
    logging.config.dictConfig(settings["logger"])
    logger = logging.getLogger(__name__)
    logger.debug("settings.json=" + json.dumps(settings))

    # Detect all connected usb cameras
    valid_usb_cameras = []
    caps = []
    if not args.skip_detect_cameras:
        for i in range(settings["detect_camera_count"]):
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
    settings["gui"] = True
    settings["webapi"] = True
    settings["netron"] = None
    settings["webapp"] = True
    settings["iotedge"] = False
    settings["init"] = True
    if args.no_gui:
        settings["gui"] = False
    if args.no_webapi:
        settings["webapi"] = False
    if args.no_webapp:
        settings["webapp"] = False
    if args.iotedge:
        settings["iotedge"] = True
    shm_shape = np.zeros(
        (settings["video_streaming_height"], settings["video_streaming_width"], 3)
    ).astype(np.uint8)
    try:
        created_shm = shared_memory.SharedMemory(
            name="wedx_shm", create=True, size=shm_shape.nbytes
        )
    except FileExistsError:
        created_shm = shared_memory.SharedMemory(
            name="wedx_shm", create=False, size=shm_shape.nbytes
        )
    settings["shm"] = np.ndarray(
        shm_shape.shape, dtype=np.uint8, buffer=created_shm.buf
    )
    settings["shm"][:] = 1

    # Start Processes
    proc = {}
    if settings["webapi"]:
        proc["webapi"] = multiprocessing.Process(
            target=run_api,
            args=(
                (
                    settings["video_streaming_width"],
                    settings["video_streaming_height"],
                    settings["netron_port"],
                )
            ),
            kwargs={"host": "0.0.0.0", "port": settings["webapi_port"]},
        )
        proc["webapi"].start()
        settings["netron"] = NetronServer(settings)
    if settings["webapp"]:
        proc["webapp"] = subprocess.Popen(
            [
                sys.executable,
                "-m",
                "streamlit",
                "run",
                "servers/webapp.py",
                "--browser.gatherUsageStats=false",
                "--server.runOnSave=true",
                "--server.headless=true",
                "--server.port",
                str(settings["webapp_port"]),
            ],
            cwd=current_path,
            stdout=sys.stdout,
            stderr=sys.stderr,
        )

    # Create Dear PyGui Context
    wedx = WeDXStudio(settings=settings)
    wedx.create_context()

    # Set default font
    wedx.set_default_font()

    # Create Dear PyGui Viewport
    wedx.create_viewport()

    # Init Manager Windows
    edge_ai_pipeline = EdgeAIPipeline(settings)
    user_preferences = UserPreferences(settings, edge_ai_pipeline)

    # Create Message Queue
    settings["mq"] = MessageQueueReqRep()
    asyncio.create_task(settings["mq"].server(edge_ai_pipeline))

    # Create Viewport Menu Bar
    wedx.viewport_menu_bar()

    # Create Primary Window
    wedx.create_primary_window()

    # Create Tab widgets on Primary Window
    edge_ai_pipeline.create_gui_widgets(parent=tag["tab"]["edge_ai_pipeline"])

    # Create User Preferences widgets
    user_preferences.create_gui_widgets()

    # Setup Dear PyGui
    wedx.setup_dearpygui()

    # Show Dear PyGui Viewport
    wedx.show_viewport()

    # Updating nodes
    node_frames = {}
    node_messages = {}
    prev_frame_time = 0
    new_frame_time = 0
    while wedx.is_dearpygui_running():
        await asyncio.sleep(0)
        if settings["init"]:
            node_frames = {}
            node_messages = {}
            prev_frame_time = 0
            new_frame_time = 0
            settings["init"] = False
        new_frame_time = time.time()
        time_elapsed = new_frame_time - prev_frame_time
        if time_elapsed > 1.0 / settings["fps"]:
            prev_frame_time = new_frame_time
            if settings["state"] == "active":
                graph = edge_ai_pipeline.node_refresh_graph
                ts = graphlib.TopologicalSorter(graph)
                ts.prepare()
                while ts.is_active():
                    ready_nodes = ts.get_ready()
                    tasks = []
                    for dpg_node_tag in ready_nodes:
                        tasks.append(
                            asyncio.create_task(
                                refresh_frame(
                                    edge_ai_pipeline,
                                    dpg_node_tag,
                                    node_frames,
                                    node_messages,
                                )
                            )
                        )
                    await asyncio.wait(tasks)
                    ts.done(*ready_nodes)

        # Render Dear PyGui frame
        wedx.render_dearpygui_frame()

    # Release nodes
    node_list = edge_ai_pipeline.get_node_list()
    for node_id_name in node_list:
        node_id, node_name = node_id_name.split(":")
        node_instance = edge_ai_pipeline.get_node_instance(node_name)
        node_instance.close(node_id)

    # When everything done, release the capture
    for cap in settings["camera_capture_list"]:
        cap.release()

    # Destroy Dear PyGui
    wedx.destroy_context()

    # Finally, shut down the client
    user_preferences.close()

    # Terminate Processes
    if settings["webapi"]:
        proc["webapi"].terminate()
    if settings["webapp"]:
        proc["webapp"].terminate()
    if settings["netron"]:
        settings["netron"].stop()

    # Release shared memory
    created_shm.unlink()


if __name__ == "__main__":
    if not sys.version >= "3.9":
        raise Exception(
            "WeDX requires python 3.9+. Current version of Python: %s" % sys.version
        )
    sys.exit(asyncio.run(main()))
