import dijsktra
from tools import *
from variables import *


class RSA():
    def __init__(self, nodes, links):
        self.nodes_dict = nodes
        self.links_dict = links
        self.flows = {}
        self.g = None

        self.flow_id = 0
        self.db_flows = {}
        self.initGraph()

    def initGraph(self):
        self.g = dijsktra.Graph()
        for n in self.nodes_dict:
            self.g.add_vertex(n)
        for l in self.links_dict:
            if debug:
                print(l)
            [s, d] = l.split('-')
            ps = self.links_dict[l]["source"]
            pd = self.links_dict[l]["target"]
            self.g.add_edge(s, d, ps, pd, 1)

        print("INFO: Graph initiated.")
        if debug:
            self.g.printGraph()

    def compute_path(self, src, dst):
        path = dijsktra.shortest_path(self.g, self.g.get_vertex(src), self.g.get_vertex(dst))
        print("INFO: Path from {} to {} with distance: {}".format(src, dst, self.g.get_vertex(dst).get_distance()))
        if debug:
            print(path)
        links = []
        for i in range(0, len(path) - 1):
            s = path[i]
            if debug:
                print(s)
            if i < len(path) - 1:
                d = path[i + 1]
                link_id = "{}-{}".format(s, d)
                if debug:
                    print(link_id, self.links_dict[link_id])
                links.append(link_id)
        self.g.reset_graph()
        return links, path

    def get_slots(self, links, val):
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
            for f in self.links_dict[l]['fibers'].keys():
                fib = self.links_dict[l]['fibers'][f]
                if l == add:
                    if 'used' in fib:
                        if fib["used"]:
                            #if debug:
                            print("ERROR: link {}, fiber {} is already in use".format(l, f))
                            continue
                if l == drop:
                    if 'used' in fib:
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
                if debug:
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

    def update_link(self, fib, slots, band):
        for i in slots:
            fib[band].remove(i)
        if 'used' in fib:
            fib['used'] = True

    def restore_link(self, fib, slots, band):
        for i in slots:
            fib[band].append(int(i))
        if 'used' in fib:
            fib['used'] = False
        fib[band].sort()

    def del_flow(self, flow):
        flows = flow["flows"]
        band = flow["band_type"]
        slots = flow["slots"]
        fiber_f = flow["fiber_forward"]
        fiber_b = flow["fiber_backward"]
        op = flow["op-mode"]
        n_slots = flow["n_slots"]
        path = flow["path"]
        links = flow["links"]
        bidir = flow["bidir"]

        for l in fiber_f.keys():
            if debug:
                print(l)
                print(fiber_f[l])
            # if debug:
            link = self.links_dict[l]
            f = fiber_f[l]
            #for f in link["fibers"].keys():
            fib = link['fibers'][f]
            if not list_in_list(slots, fib[band]):
                self.restore_link(fib, slots, band)
                if debug:
                    print(fib[band])
        if bidir:
            for rl in fiber_b.keys():
                if debug:
                    print(rl)
                    print(fiber_b[rl])
                rlink = self.links_dict[rl]
                rf = fiber_b[rl]
                rfib = rlink['fibers'][rf]
                if not list_in_list(slots, rfib[band]):
                    self.restore_link(rfib, slots, band)
                    if debug:
                        print(rfib[band])
        return True

    def init_link_slots(self):
        for l in self.links_dict:
            for f in self.links_dict[l]["fibers"]:
                fib = self.links_dict[l]["fibers"][f]
                if len(fib["c_slots"]) > 0:
                    fib["c_slots"] = list(range(0, Nc))
                if len(fib["l_slots"]) > 0:
                    fib["l_slots"] = list(range(0, Nl))
                if len(fib["s_slots"]) > 0:
                    fib["s_slots"] = list(range(0, Ns))
            if debug:
                print(fib)

    def get_fibers_forward(self, links, slots, band):
        fiber_list = {}
        add = links[0]
        drop = links[-1]
        for l in links:
            for f in self.links_dict[l]['fibers'].keys():
                fib = self.links_dict[l]['fibers'][f]
                if l == add:
                    if 'used' in fib:
                        if fib["used"]:
                            if debug:
                                print("link {}, fiber {} is already in use".format(l, f))
                            continue
                if l == drop:
                    if 'used' in fib:
                        if fib["used"]:
                            if debug:
                                print("link {}, fiber {} is already in use".format(l, f))
                            continue
                if list_in_list(slots, fib[band]):
                    fiber_list[l] = f
                    self.update_link(fib, slots, band)
                    break
        print("INFO: Path forward computation completed")
        return fiber_list


    def get_fibers_backward(self, links, fibers, slots, band):
        fiber_list = {}
        #r_drop = reverse_link(links[0])
        #r_add = reverse_link(links[-1])
        for l in fibers.keys():
            if debug:
                print(l)
                print(fibers[l])
            port = self.links_dict[l]["fibers"][fibers[l]]["src_port"]
            r_l = reverse_link(l)
            r_link = self.links_dict[r_l]
            for f in r_link["fibers"].keys():
                fib = self.links_dict[r_l]['fibers'][f]
                if r_link["fibers"][f]["remote_peer_port"] == port:
                    if list_in_list(slots, fib[band]):
                        fiber_list[r_l] = f
                        self.update_link(fib, slots, band)
        print("INFO: Path backward computation completed")
        return fiber_list

    def select_slots_and_ports(self, links, n_slots, c, l, s, bidir):
        if debug:
            print(self.links_dict)
        band, slots = slot_selection(c, l, s, n_slots)
        if band is None:
            print("No slots available in the three bands")
            return None, None, None
        if debug:
            print(band, slots)
        fibers_f = self.get_fibers_forward(links, slots, band)
        fibers_b = []
        if bidir:
            fibers_b = self.get_fibers_backward(links, fibers_f, slots, band)
        if debug:
            print("forward")
            print(fibers_f)
            print("backward")
            print(fibers_b)
        add = links[0]
        drop = links[-1]
        inport = "0"
        outport = "0"
        r_inport = "0"
        r_outport = "0"
        t_flows = {}

        for lx in fibers_f:
            if l == add:
                inport = "0"
                r_outport = "0"
            if l == drop:
                outport = "0"
                r_inport = "0"
            f = fibers_f[lx]
            src, dst = lx.split("-")
            outport = self.links_dict[lx]['fibers'][f]["src_port"]
            self.flows[src] = {}
            t_flows[src] = {}
            self.flows[src]["f"] = {}
            t_flows[src]["f"] = {}
            self.flows[src]["b"] = {}
            t_flows[src]["b"] = {}
            self.flows[src]["f"] = {"in": inport, "out": outport}
            t_flows[src]["f"] = {"in": inport, "out": outport}

            if bidir:
                r_inport = self.links_dict[lx]['fibers'][f]["local_peer_port"]
                self.flows[src]["b"] = {"in": r_inport, "out": r_outport}
                t_flows[src]["b"] = {"in": r_inport, "out": r_outport}

            inport = self.links_dict[lx]['fibers'][f]["dst_port"]
            if bidir:
                r_outport = self.links_dict[lx]['fibers'][f]["remote_peer_port"]
        self.flows[dst] = {}
        t_flows[dst] = {}
        self.flows[dst]["f"] = {}
        t_flows[dst]["f"] = {}
        self.flows[dst]["b"] = {}
        t_flows[dst]["b"] = {}
        self.flows[dst]["f"] = {"in": inport, "out": "0"}
        t_flows[dst]["f"] = {"in": inport, "out": "0"}
        if bidir:
            self.flows[dst]["b"] = {"in": "0", "out": r_outport}
            t_flows[dst]["b"] = {"in": "0", "out": r_outport}

        if debug:
            print(self.links_dict)

        if debug:
            print(self.flows)
        print("INFO: Flow matrix computed")

        return t_flows, band, slots, fibers_f, fibers_b

    def rsa_computation(self, links, rate, bidir):
        path_len = 0
        op, num_slots = map_rate_to_slot(rate)
        c_slots, l_slots, s_slots = self.get_slots(links, num_slots)
        if debug:
            print(c_slots)
            print(l_slots)
            print(s_slots)
        if len(c_slots) > 0 or len(l_slots) > 0 or len(s_slots) > 0:
            flow_list, band_range, slots, fiber_f, fiber_b = self.select_slots_and_ports(links, num_slots, c_slots, l_slots, s_slots, bidir)
            f0, band = freqency_converter(band_range, slots)
            if debug:
                print(f0, band)
            print("INFO: RSA completed")

            return flow_list, band_range, slots, fiber_f, fiber_b, op, num_slots, f0, band
        return None, "", [], {}, {}, 0, 0, 0, 0
