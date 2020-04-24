from flask import Flask, request, Response
import cherrypy
import json
import logging
import paste.translogger
import requests
import os

app = Flask(__name__)
logger = logging.getLogger("entity-diff-service")

JWT = os.environ.get("JWT")
ENDPOINT = os.environ.get("SESAM_API")

def getPrevious(eid, prev, dataset):
    url = ENDPOINT + "/datasets/" + dataset + "/entities/" + eid + "?offset=" + str(prev)
    headers = {'Authorization': 'bearer ' + JWT}
    r = requests.get(url, headers=headers)
    return r.json()

@app.route('/transform/<dataset>', methods=['POST'])
def receiver(dataset):
    def generate(entities):
        yield "["
        for index, entity in enumerate(entities):
            if index > 0:
                yield ","
                
            # get previous
            eid = entity["_id"]
            pid = entity["_previous"]
            prevEntity = getPrevious(eid, pid, dataset)

            # check for modified or removed keys
            for k in prevEntity.keys():
                if k.startswith("_"):
                    continue

                if k in entity:
                    if prevEntity[k] != entity[k]:
                        c = {}
                        c["_id"] = eid + "-" + k + "-" + str(entity["_ts"])
                        c["entity"] = eid
                        c["timestamp"] = entity["_ts"]
                        c["oldvalue"] = prevEntity[k]
                        c["newvalue"] = entity[k]                         
                        yield json.dumps(c) 
                else:
                    c = {}
                    c["_id"] = eid + "-" + k + "-" + str(entity["_ts"])
                    c["entity"] = eid
                    c["timestamp"] = entity["_ts"]
                    c["oldvalue"] = prevEntity[k]
                    c["newvalue"] = ""                         
                    yield json.dumps(c)

            # check for new properties
            for k in entity.keys():
                if not k in prevEntity:
                    c = {}
                    c["_id"] = eid + "-" + k + "-" + str(entity["_ts"])
                    c["entity"] = eid
                    c["timestamp"] = entity["_ts"]
                    c["oldvalue"] = ""
                    c["newvalue"] = entity[k]                         
                    yield json.dumps(c)

        yield "]"

    # get entities from request
    entities = request.get_json()

    # create the response
    return Response(generate(entities), mimetype='application/json')


if __name__ == '__main__':
    format_string = '%(asctime)s - %(name)s - %(levelname)s - %(message)s'

    # Log to stdout, change to or add a (Rotating)FileHandler to log to a file
    stdout_handler = logging.StreamHandler()
    stdout_handler.setFormatter(logging.Formatter(format_string))
    logger.addHandler(stdout_handler)

    # Comment these two lines if you don't want access request logging
    app.wsgi_app = paste.translogger.TransLogger(app.wsgi_app, logger_name=logger.name,
                                                 setup_console_handler=False)
    app.logger.addHandler(stdout_handler)

    logger.propagate = False
    logger.setLevel(logging.INFO)

    cherrypy.tree.graft(app, '/')

    # Set the configuration of the web server to production mode
    cherrypy.config.update({
        'environment': 'production',
        'engine.autoreload_on': False,
        'log.screen': True,
        'server.socket_port': 5001,
        'server.socket_host': '0.0.0.0'
    })

    # Start the CherryPy WSGI web server
    cherrypy.engine.start()
    cherrypy.engine.block()


