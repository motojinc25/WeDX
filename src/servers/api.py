import json

from flask import Flask, request

from links.mq_req_rep.link import MessageQueueReqRep

app = Flask(__name__)
mq = MessageQueueReqRep()


@app.route("/", methods=["GET"])
async def hello():
    message = await mq.client(message={"method": "root"})
    return "WeDX Web API - " + message


@app.route("/startpipeline", methods=["POST"])
async def start_pipeline():
    message = await mq.client(message={"method": "start_pipeline"})
    return "Call Start Pipeline method : " + message


@app.route("/stoppipeline", methods=["POST"])
async def stop_pipeline():
    message = await mq.client(message={"method": "stop_pipeline"})
    return "Call Stop Pipeline method : " + message


@app.route("/importpipeline", methods=["POST"])
async def import_pipeline():
    data = request.data.decode("utf-8")
    payload = json.loads(data)
    message = await mq.client(message={"method": "import_pipeline", "payload": payload})
    return "Call Import Pipeline method : " + message


@app.route("/exportpipeline", methods=["POST"])
async def export_pipeline():
    message = await mq.client(message={"method": "export_pipeline"})
    return message


def run_api(**kwargs):
    app.run(**kwargs)
