from flask import Flask
from flask import render_template
from flask_restplus import Resource, Api
from tools import *
from variables import *
from RSA import RSA
import time
import time

rsa = None


app = Flask(__name__)
api = Api(app, version='1.0', title='Optical controller API',
          description='Rest API to configure OC Optical devices in TFS')
# app.config.from_object('config')
# appbuilder = AppBuilder(app, indexview=MyIndexView)
optical = api.namespace('OpticalTFS', description='TFS Optical APIs')


@app.route('/index')
def index():
    return render_template('index.html')


#@optical.route('/AddLightpath/<string:src>/<string:dst>/<int:bitrate>/<int:bidir>')
@optical.route('/AddLightpath/<string:src>/<string:dst>/<int:bitrate>')
@optical.response(200, 'Success')
@optical.response(404, 'Error, not found')
class AddLightpath(Resource):
    @staticmethod
    def put(src, dst, bitrate, bidir=1):

        print("INFO: New Lightpath request from {} to {} with rate {} ".format(src, dst, bitrate))
        t0 = time.time()*1000.0
        if debug:
            rsa.g.printGraph()

        if rsa is not None:
            flow_id = rsa.rsa_computation(src, dst, bitrate, bidir)
            if rsa.db_flows[flow_id]["op-mode"] == 0:
                return 'No path found', 404
            t1 = time.time()*1000.0
            elapsed = t1 - t0
            print("INFO: time elapsed = {} ms".format(elapsed))
            return rsa.db_flows[flow_id], 200
        else:
            return "Error", 404


#@optical.route('/AddFlexLightpath/<string:src>/<string:dst>/<int:bitrate>')
@optical.route('/AddFlexLightpath/<string:src>/<string:dst>/<int:bitrate>/<int:bidir>')
@optical.response(200, 'Success')
@optical.response(404, 'Error, not found')
class AddFlexLightpath(Resource):
    @staticmethod
    def put(src, dst, bitrate, bidir=1):

        print("INFO: New FlexLightpath request from {} to {} with rate {} ".format(src, dst, bitrate))
        t0 = time.time()*1000.0
        if debug:
            rsa.g.printGraph()

        if rsa is not None:
            flow_id, optical_band_id = rsa.rsa_fs_computation(src, dst, bitrate, bidir)
            if flow_id is not None:
                if rsa.db_flows[flow_id]["op-mode"] == 0:
                    return 'No path found', 404
                t1 = time.time() * 1000.0
                elapsed = t1 - t0
                print("INFO: time elapsed = {} ms".format(elapsed))

                return rsa.db_flows[flow_id], 200
            else:
                if len(rsa.optical_bands[optical_band_id]["flows"]) == 0:
                    return 'No path found', 404
                else:
                    t1 = time.time() * 1000.0
                    elapsed = t1 - t0
                    print("INFO: time elapsed = {} ms".format(elapsed))

                    return rsa.optical_bands[optical_band_id], 200
        else:
            return "Error", 404

@optical.route('/DelFlexLightpath/<int:flow_id>/<string:src>/<string:dst>/<int:bitrate>/<int:o_band_id>')
@optical.response(200, 'Success')
@optical.response(404, 'Error, not found')
class DelLightpath(Resource):
    @staticmethod
    def delete(flow_id, src, dst, bitrate, o_band_id):
        if flow_id in rsa.db_flows.keys():
            flow = rsa.db_flows[flow_id]
            bidir = flow["bidir"]
            match1 = flow["src"] == src and flow["dst"] == dst and flow["bitrate"] == bitrate
            if bidir:
                match2 = flow["src"] == dst and flow["dst"] == src and flow["bitrate"] == bitrate
                if match1 or match2:
                    ob_id = flow["parent_opt_band"]
                    rsa.del_flow(flow, ob_id)
                    rsa.db_flows[flow_id]["is_active"] = False
                    rsa.optical_bands[ob_id]["served_lightpaths"].remove(flow_id)
                    if rsa.optical_bands[ob_id]["reverse_optical_band_id"] != 0:
                        rev_ob_id = rsa.optical_bands[ob_id]["reverse_optical_band_id"]
                        rsa.optical_bands[rev_ob_id]["served_lightpaths"].remove(flow_id)

                    if debug:
                        print(links_dict)
                    return "flow {} deleted".format(flow_id), 200
                else:
                    return "flow {} not matching".format(flow_id), 404
            else:
                if match1:
                    ob_id = flow["parent_opt_band"]
                    rsa.del_flow(flow, ob_id)
                    rsa.db_flows[flow_id]["is_active"] = False
                    rsa.optical_bands[ob_id]["served_lightpaths"].remove(flow_id)
                    if debug:
                        print(links_dict)
                    return "flow {} deleted".format(flow_id), 200
                else:
                    return "flow {} not matching".format(flow_id), 404
        else:
            return "flow id {} does not exist".format(flow_id), 404



@optical.route('/DelLightpath/<int:flow_id>/<string:src>/<string:dst>/<int:bitrate>')
@optical.response(200, 'Success')
@optical.response(404, 'Error, not found')
class DelLightpath(Resource):
    @staticmethod
    def delete(flow_id, src, dst, bitrate):
        if flow_id in rsa.db_flows.keys():
            flow = rsa.db_flows[flow_id]
            match1 = flow["src"] == src and flow["dst"] == dst and flow["bitrate"] == bitrate
            match2 = flow["src"] == dst and flow["dst"] == src and flow["bitrate"] == bitrate
            if match1 or match2:
                rsa.del_flow(flow)
                rsa.db_flows[flow_id]["is_active"] = False
                if debug:
                    print(links_dict)
                return "flow {} deleted".format(flow_id), 200
            else:
                return "flow {} not matching".format(flow_id), 404
        else:
            return "flow id {} does not exist".format(flow_id), 404


@optical.route('/GetLightpaths')
@optical.response(200, 'Success')
@optical.response(404, 'Error, not found')
class GetFlows(Resource):
    @staticmethod
    def get():
        try:
            if debug:
                print(rsa.db_flows)
            return rsa.db_flows, 200
        except:
            return "Error", 404

@optical.route('/GetOpticalBands')
@optical.response(200, 'Success')
@optical.response(404, 'Error, not found')
class GetBands(Resource):
    @staticmethod
    def get():
        try:
            if debug:
                print(rsa.optical_bands)
            return rsa.optical_bands, 200
        except:
            return "Error", 404


@optical.route('/GetOpticalBand/<string:ob_id>')
@optical.response(200, 'Success')
@optical.response(404, 'Error, not found')
class GetBand(Resource):
    @staticmethod
    def get(ob_id):
        for ob_idx in rsa.optical_bands.keys():
            if str(ob_idx) == str(ob_id):
                if debug:
                    print(rsa.optical_bands[ob_id])
                return rsa.optical_bands[ob_idx], 200
        return {}, 404


@optical.route('/GetLinks')
@optical.response(200, 'Success')
@optical.response(404, 'Error, not found')
class GetFlows(Resource):
    @staticmethod
    def get():
        global links_dict
        try:
            if debug:
                print(links_dict)
            return links_dict, 200
        except:
            return "Error", 404


if __name__ == '__main__':

    nodes_dict, links_dict = readTopologyData(nodes_json, topology_json)
    rsa = RSA(nodes_dict, links_dict)
    print(rsa.init_link_slots(testing))

    app.run(host='0.0.0.0', port=5000)
