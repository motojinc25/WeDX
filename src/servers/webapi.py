import json
import multiprocessing.shared_memory as shared_memory
import os

import cv2
import numpy as np
from flasgger import Swagger
from flask import Flask, Response, render_template, request

from links.mq_req_rep.link import MessageQueueReqRep

app = Flask(__name__)
mq = MessageQueueReqRep()
shared_frame = None
web_netron_port = None
Swagger(app)

# Set WeDX settings
settings = None
current_path = os.path.dirname(os.path.abspath(__file__))
with open(os.path.abspath(os.path.join(current_path, "../.wedx/settings.json"))) as fp:
    settings = json.load(fp)


@app.route("/", methods=["GET"])
async def index():
    return render_template("index.html")


@app.route("/netron", methods=["GET"])
async def netron():
    iframe = "http://" + request.host.split(":")[0] + ":" + str(web_netron_port)
    return render_template("netron.html", iframe=iframe)


@app.route("/apis", methods=["GET"])
async def apis():
    iframe = (
        "http://"
        + request.host.split(":")[0]
        + ":"
        + str(settings["webapi_port"])
        + "/apidocs"
    )
    return render_template("apis.html", iframe=iframe)


@app.route("/startpipeline", methods=["POST"])
async def start_pipeline():
    """Start pipeline
    ---
    tags:
        - WeDX Web API List
    responses:
        200:
            description: OK
    """
    message = await mq.client(message={"method": "start_pipeline"})
    return "Call Start Pipeline method : " + message


@app.route("/stoppipeline", methods=["POST"])
async def stop_pipeline():
    """Stop pipeline
    ---
    tags:
        - WeDX Web API List
    responses:
        200:
            description: OK
    """
    message = await mq.client(message={"method": "stop_pipeline"})
    return "Call Stop Pipeline method : " + message


@app.route("/importpipeline", methods=["POST"])
async def import_pipeline():
    """Import pipeline
    ---
    tags:
        - WeDX Web API List
    parameters:
        -
            name: body
            in: body
            required: true
            type: string
    responses:
        200:
            description: OK
    """
    data = request.data.decode("utf-8")
    payload = json.loads(data)
    message = await mq.client(message={"method": "import_pipeline", "payload": payload})
    return "Call Import Pipeline method : " + message


@app.route("/exportpipeline", methods=["POST"])
async def export_pipeline():
    """Export pipeline
    ---
    tags:
        - WeDX Web API List
    responses:
        200:
            description: OK
    """
    message = await mq.client(message={"method": "export_pipeline"})
    return message


@app.route("/stream", methods=["GET"])
async def stream():
    return render_template("stream.html")


def gen():
    while True:
        _, frame = cv2.imencode(".jpg", shared_frame)
        if frame is not None:
            yield (
                b"--frame\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + frame.tobytes() + b"\r\n"
            )


@app.route("/video_feed", methods=["GET"])
async def video_feed():
    return Response(gen(), mimetype="multipart/x-mixed-replace; boundary=frame")


def run_api(width, height, netron_port, **kwargs):
    global shared_frame
    global web_netron_port
    existing_shm = shared_memory.SharedMemory(name="wedx_shm")
    shared_frame = np.ndarray(
        (height, width, 3), dtype=np.uint8, buffer=existing_shm.buf
    )
    web_netron_port = netron_port
    app.run(**kwargs)
