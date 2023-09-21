import json
import dijsktra
import numpy as np

from flask import Flask
from flask import render_template
from flask_restplus import Resource, Api

testing = 1

g = None
nodes_json = 'json_files/nodes.json'
topology_json = 'json_files/topology-optical2.json'

nodes_dict = None
links_dict = None
flows = {}

running = True
debug = 0

flow_id = 0
db_flows = {}

Fl = 184800
Fc = 192000
Fs = 196200

Nl = 550
Nc = 320
#Nc = 10
Ns = 720


app = Flask(__name__)
api = Api(app, version='1.0', title='Optical controller API',
          description='Rest API to configure OC Optical devices in TFS')
# app.config.from_object('config')
# appbuilder = AppBuilder(app, indexview=MyIndexView)
optical = api.namespace('OpticalTFS', description='TFS Optical APIs')




@app.route('/index')
def index():
    return render_template('index.html')


@optical.route('/AddLightpath/<string:src>/<string:dst>/<int:bitrate>')
@optical.response(200, 'Success')
@optical.response(404, 'Error, not found')
class AddLightpath(Resource):
    @staticmethod
    def put(src, dst, bitrate):
        global flow_id
        flow_id += 1
        print("INFO: New request with id {}, from {} to {} with rate {} ".format(flow_id, src, dst, bitrate))
        db_flows[flow_id] = {}
        db_flows[flow_id]["src"] = src
        db_flows[flow_id]["dst"] = dst
        db_flows[flow_id]["bitrate"] = bitrate
        if debug:
            g.printGraph()

        links, path = compute_path(src, dst)
        if len(path) < 2:
            return 'Error', 404
        flows, band, slots, fiber_f, fiber_b, op, n_slots = rsa(links, path, bitrate)
        if debug:
            print(flows, slots)
        if flows is None:
            return 'Error', 404
        slots_i = []
        for i in slots:
            slots_i.append(int(i))

        db_flows[flow_id]["flows"] = flows
        db_flows[flow_id]["band"] = band
        db_flows[flow_id]["slots"] = slots_i
        db_flows[flow_id]["fiber_forward"] = fiber_f
        db_flows[flow_id]["fiber_backward"] = fiber_b
        db_flows[flow_id]["op-mode"] = op
        db_flows[flow_id]["n_slots"] = n_slots
        db_flows[flow_id]["links"] = links
        db_flows[flow_id]["path"] = path
        db_flows[flow_id]["is_active"] = True

        return flow_id, 200


@optical.route('/DelLightpath/<int:flow_id>/<string:src>/<string:dst>/<int:bitrate>')
@optical.response(200, 'Success')
@optical.response(404, 'Error, not found')
class DelLightpath(Resource):
    @staticmethod
    def delete(flow_id, src, dst, bitrate):
        global db_flows
        flow = db_flows[flow_id]
        if flow["src"] == src and flow["dst"] == dst and flow["bitrate"] == bitrate:
            del_flow(flow)
            db_flows[flow_id]["is_active"] = False
            if debug:
                print(links_dict)
            return "flow {} deleted".format(flow_id), 200
        else:
            return "flow {} Not found".format(flow_id), 404


@optical.route('/GetFlows')
@optical.response(200, 'Success')
@optical.response(404, 'Error, not found')
class GetFlows(Resource):
    @staticmethod
    def get():
        global db_flows
        try:
            if debug:
                print(db_flows)
            return db_flows, 200
        except:
            return "Error", 404


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


def common_slots(a, b):
    return list(np.intersect1d(a, b))


def readTopologyData(nodes, topology):
    nodes_file = open(nodes, 'r')
    topo_file = open(topology, 'r')

    nodes = json.load(nodes_file)
    topo = json.load(topo_file)

    nodes_file.close()
    topo_file.close()

    return nodes, topo


def initGraph():
    global nodes_dict
    global links_dict

    g = dijsktra.Graph()
    for n in nodes_dict:
        g.add_vertex(n)

    for l in links_dict:
        if debug:
            print(l)
        [s, d] = l.split('-')
        ps = links_dict[l]["source"]
        pd = links_dict[l]["target"]
        g.add_edge(s, d, ps, pd, 1)

    print("INFO: Graph initiated.")
    if debug:
        g.printGraph()

    return g


def compute_path(src, dst):
    global g
    global nodes_dict
    global links_dict
    path = dijsktra.shortest_path(g, g.get_vertex(src), g.get_vertex(dst))
    print("INFO: Path from {} to {} with distance: {}".format(src, dst, g.get_vertex(dst).get_distance()))
    if debug:
        print(path)
    links = []
    for i in range(0, len(path) - 1):
        s = path[i]
        if debug:
            print(s)
        # print("device id", nodes_dict[s]["id"])
        # print("ip ", nodes_dict[s]["ip"] + ":" + nodes_dict[s]["port"])
        if i < len(path) - 1:
            d = path[i + 1]
            link_id = "{}-{}".format(s, d)
            if debug:
                print(link_id, links_dict[link_id])
            links.append(link_id)
    g.reset_graph()
    return links, path


def map_modulation_to_op(mod):
    if mod == "DP-QPSK":
        return 1
    if mod == "DP-16QAM":
        return 7


def map_rate_to_slot(rate):
    if rate == 100:
        mod = "DP-QPSK"
        slots = 4
        op = map_modulation_to_op(mod)
        return op, slots
    if rate == 400:
        mod = "DP-16QAM"
        slots = 8
        op = map_modulation_to_op(mod)
        return op, slots
    else:
        return 2, 5


def consecutives(x, val):
    res = []
    temp = []
    x.sort()
    temp.append(x[0])
    y = 1
    for i in range(1, len(x)):
        if x[i] == x[i - 1] + 1:
            y += 1
            temp.append(x[i])
        else:
            if y >= val:
                res.extend(temp)
            temp = [x[i]]
            y = 1
        if i == len(x) - 1 and y >= val:
            res.extend(temp)
    return res


def combine(ls1, ls2):
    temp = ls1
    for i in ls2:
        if i not in ls1:
            temp.append(i)
    temp.sort()
    return temp


def get_slots(links, val):
    c_sts = []
    l_sts = []
    s_sts = []
    c_slots = {}
    l_slots = {}
    s_slots = {}
    add = links[0]
    drop = links[-1]
    for l in links:
        c_slots[l] = []
        l_slots[l] = []
        s_slots[l] = []
        found = 0
        for f in links_dict[l]['fibers'].keys():
            fib = links_dict[l]['fibers'][f]
            if l == add:
                if fib["used"]:
                    #if debug:
                    print("ERROR: link {}, fiber {} is already in use".format(l, f))
                    continue
            if l == drop:
                if fib["used"]:
                    #if debug:
                    print("EROOR: link {}, fiber {} is already in use".format(l, f))
                    continue
            if len(fib["c_slots"])> 0:
                c_slots[l] = combine(c_slots[l], consecutives(fib["c_slots"], val))
            if len(fib["l_slots"]) > 0:

                l_slots[l] = combine(l_slots[l], consecutives(fib["l_slots"], val))
            if len(fib["s_slots"]) > 0:

                s_slots[l] = combine(s_slots[l], consecutives(fib["s_slots"], val))
            print(l, c_slots[l])
            found = 1
        if found == 0:
            return [], [], []
    if debug:
        print(c_slots)
    keys = list(c_slots.keys())
    if debug:
        print(len(keys))
    if debug:
        print(keys[0])
    # intersection among the slots over all links
    for i in range(1, len(keys)):
        if debug:
            print(keys[i])
        # set a for the intersection
        if i == 1:
            a_c = c_slots[keys[i - 1]]
            a_l = l_slots[keys[i - 1]]
            a_s = s_slots[keys[i - 1]]
        else:
            a_c = c_sts
            a_l = l_sts
            a_s = s_sts
        # set b for the intersection
        b_c = c_slots[keys[i]]
        b_l = l_slots[keys[i]]
        b_s = s_slots[keys[i]]

        c_sts = common_slots(a_c, b_c)
        l_sts = common_slots(a_l, b_l)
        s_sts = common_slots(a_s, b_s)
    return c_sts, l_sts, s_sts


def slot_selection(c, l, s, n_slots):
    # First Fit
    if len(c) >= n_slots:
        return "c_slots", c[0: n_slots]
    elif len(l) >= n_slots:
        return "l_slots", l[0: n_slots]
    elif len(l) >= n_slots:
        return "s_slots", s[0: n_slots]
    else:
        return None, None


def list_in_list(a, b):
    # convert list A to numpy array
    a_arr = np.array(a)
    # convert list B to numpy array
    b_arr = np.array(b)

    for i in range(len(b_arr)):
        if np.array_equal(a_arr, b_arr[i:i + len(a_arr)]):
            return True
    return False


def update_link(fib, slots, band):
    for i in slots:
        fib[band].remove(i)
    if 'used' in fib:
        fib['used'] = True


def restore_link(fib, slots, band):
    for i in slots:
        fib[band].append(int(i))

    #fib[band].extend(slots)
    if 'used' in fib:
        fib['used'] = False
    fib[band].sort()


def del_flow(flow):
    global links_dict
    flows = flow["flows"]
    band = flow["band"]
    slots = flow["slots"]
    fiber_f = flow["fiber_forward"]
    fiber_b = flow["fiber_backward"]
    op = flow["op-mode"]
    n_slots = flow["n_slots"]
    path = flow["path"]
    links = flow["links"]
    for l in fiber_f.keys():
        if debug:
            print(l)
            print(fiber_f[l])
        # if debug:

        link = links_dict[l]
        for f in link["fibers"].keys():
            fib = links_dict[l]['fibers'][f]
            if not list_in_list(slots, fib[band]):
                restore_link(fib, slots, band)
                if debug:
                    print(fib[band])
    for rl in fiber_b.keys():
        if debug:
            print(rl)
            print(fiber_b[rl])
        # if debug:
        #    print(rl)
        #    print(fiber_b[rl])
        rlink = links_dict[rl]
        for rf in rlink["fibers"].keys():
            rfib = links_dict[rl]['fibers'][rf]
            if not list_in_list(slots, rfib[band]):
                restore_link(rfib, slots, band)
                if debug:
                    print(rfib[band])
    return True


def init_link_slots():
    global links_dict
    for l in links_dict:
        for f in links_dict[l]["fibers"]:
            fib = links_dict[l]["fibers"][f]
            if len(fib["c_slots"]) > 0:
                fib["c_slots"] = list(range(0, Nc))
            if len(fib["l_slots"]) > 0:
                fib["l_slots"] = list(range(0, Nl))
            if len(fib["s_slots"]) > 0:
                fib["s_slots"] = list(range(0, Ns))
        print(fib)


def get_fibers_forward(links, slots, band):
    fiber_list = {}
    add = links[0]
    drop = links[-1]
    for l in links:
        for f in links_dict[l]['fibers'].keys():
            fib = links_dict[l]['fibers'][f]
            if l == add:
                if fib["used"]:
                    if debug:
                        print("link {}, fiber {} is already in use".format(l, f))
                    continue
            if l == drop:
                if fib["used"]:
                    if debug:
                        print("link {}, fiber {} is already in use".format(l, f))
                    continue
            if list_in_list(slots, fib[band]):
                fiber_list[l] = f
                update_link(fib, slots, band)
                '''
                else:
                    update_link(fib, slots, band, False)
                '''
                break
    print("INFO: Path forward computation completed")
    return fiber_list


def reverse_link(link):
    s, d = link.split('-')
    r_link = "{}-{}".format(d, s)
    return r_link


def get_fibers_backward(links, fibers, slots, band):
    fiber_list = {}
    r_drop = reverse_link(links[0])
    r_add = reverse_link(links[-1])
    for l in fibers.keys():
        if debug:
            print(l)
            print(fibers[l])
        port = links_dict[l]["fibers"][fibers[l]]["src_port"]
        r_l = reverse_link(l)
        r_link = links_dict[r_l]
        for f in r_link["fibers"].keys():
            fib = links_dict[r_l]['fibers'][f]
            if r_link["fibers"][f]["remote_peer_port"] == port:
                if list_in_list(slots, fib[band]):
                    fiber_list[r_l] = f
                    # if l == r_drop or l == r_add:
                    update_link(fib, slots, band)
                    # else:
                    #    update_link(fib, slots, band, False)
    print("INFO: Path backward computation completed")

    return fiber_list


def select_slots_and_ports(links, n_slots, c, l, s):
    global links_dict
    global nodes_dict
    global flows

    if debug:
        print(links_dict)
    band, slots = slot_selection(c, l, s, n_slots)
    if band is None:
        print("No slots available in the three bands")
        return None, None, None
    if debug:
        print(band, slots)
    fibers_f = get_fibers_forward(links, slots, band)
    fibers_b = get_fibers_backward(links, fibers_f, slots, band)

    if debug:
        print("forward")
        print(fibers_f)
        print("backward")
        print(fibers_b)

    add = links[0]
    drop = links[-1]
    inport = 0
    outport = 0
    r_inport = 0
    r_outport = 0
    t_flows = {}

    for lx in fibers_f:
        if l == add:
            inport = 0
            r_outport = 0
        if l == drop:
            outport = 0
            r_inport = 0
        f = fibers_f[lx]
        src, dst = lx.split("-")
        outport = links_dict[lx]['fibers'][f]["src_port"]
        flows[src] = []
        t_flows[src] = []
        flows[src].append({"in": inport, "out": outport})
        t_flows[src].append({"in": inport, "out": outport})

        r_inport = links_dict[lx]['fibers'][f]["local_peer_port"]
        flows[src].append({"in": r_inport, "out": r_outport})
        t_flows[src].append({"in": r_inport, "out": r_outport})

        inport = links_dict[lx]['fibers'][f]["dst_port"]
        r_outport = links_dict[lx]['fibers'][f]["remote_peer_port"]
    flows[dst] = []
    t_flows[dst] = []
    flows[dst].append({"in": inport, "out": 0})
    t_flows[dst].append({"in": inport, "out": 0})
    flows[dst].append({"in": 0, "out": r_outport})
    t_flows[dst].append({"in": 0, "out": r_outport})

    if debug:
        print(links_dict)

    if debug:
        print(flows)
    print("INFO: Flow matrix computed")

    return t_flows, band, slots, fibers_f, fibers_b


def rsa(links, path, rate):
    global links_dict
    global nodes_dict
    path_len = 0
    op, num_slots = map_rate_to_slot(rate)
    c_slots, l_slots, s_slots = get_slots(links, num_slots)
    if debug:
        print(c_slots)
        print(l_slots)
        print(s_slots)
    if len(c_slots) > 0 or len(l_slots) > 0 or len(s_slots) > 0:
        flow_list, band, slots, fiber_f, fiber_b = select_slots_and_ports(links, num_slots, c_slots, l_slots, s_slots)
        print("INFO: RSA completed")

        return flow_list, band, slots, fiber_f, fiber_b, op, num_slots
    return None, "", [], {}, {}, 0, 0


if __name__ == '__main__':
    nodes_dict, links_dict = readTopologyData(nodes_json, topology_json)
    if not testing:
        init_link_slots()
    g = initGraph()
    app.run(host='0.0.0.0', port=5000)
