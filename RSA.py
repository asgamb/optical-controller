import dijsktra
from tools import *
from variables import *


class RSA():
    def __init__(self, nodes, links):
        self.nodes_dict = nodes
        self.links_dict = links
        self.g = None

        self.flow_id = 0
        self.opt_band_id = 0
        self.db_flows = {}
        self.initGraph()
        self.c_slot_number = 0
        self.l_slot_number = 0
        self.s_slot_number = 0
        self.optical_bands = {}

    def init_link_slots(self, testing):
        if not testing:
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
        for l1 in self.links_dict:
            for f1 in self.links_dict[l1]["fibers"]:
                fib1 = self.links_dict[l1]["fibers"][f1]
                self.c_slot_number = len(fib1["c_slots"])
                self.l_slot_number = len(fib1["l_slots"])
                self.s_slot_number = len(fib1["s_slots"])

                break
            break
        return "{},{},{}".format(self.c_slot_number, self.l_slot_number, self.s_slot_number)

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

    def get_slots(self, links, slots, optical_band_id = None):

        if isinstance(slots, int):
            val_c = slots
            val_s = slots
            val_l = slots
        else:
            val_c = self.c_slot_number
            val_l = self.l_slot_number
            val_s = self.s_slot_number

        c_sts = []
        l_sts = []
        s_sts = []
        c_slots = {}
        l_slots = {}
        s_slots = {}
        add = ""
        drop = ""
        src_1, dst_1 = links[0].split('-')
        src_2, dst_2 = links[-1].split('-')
        if self.nodes_dict[src_1]["type"] == "OC-TP":
            add = links[0]
        if self.nodes_dict[dst_2]["type"] == "OC-TP":
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
                            print("WARNING!!!: link {}, fiber {} is already in use".format(l, f))
                            continue
                if l == drop:
                    if 'used' in fib:
                        if fib["used"]:
                            #if debug:
                            print("WARNING!!!: link {}, fiber {} is already in use".format(l, f))
                            continue
                if len(fib["c_slots"])> 0:
                    c_slots[l] = combine(c_slots[l], consecutives(fib["c_slots"], val_c))
                if len(fib["l_slots"]) > 0:
                    l_slots[l] = combine(l_slots[l], consecutives(fib["l_slots"], val_l))
                if len(fib["s_slots"]) > 0:
                    s_slots[l] = combine(s_slots[l], consecutives(fib["s_slots"], val_s))
                if debug:
                    print(l, c_slots[l])
                found = 1
            if found == 0:
                return [], [], []

        keys = list(c_slots.keys())
        if debug:
            print(len(keys))
        if debug:
            print(keys[0])
        # intersection among the slots over all links
        if len(keys) == 1:
            c_sts = c_slots[keys[0]]
            l_sts = l_slots[keys[0]]
            s_sts = s_slots[keys[0]]
        else:
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
        if optical_band_id is not None:
            if "c_slots" in self.optical_bands[optical_band_id].keys():
                if len(self.optical_bands[optical_band_id]["c_slots"]) > 0:
                    a_c = c_sts
                    b_c = self.optical_bands[optical_band_id]["c_slots"]
                    c_sts = common_slots(a_c, b_c)
                else:
                    c_sts = []
            else:
                c_sts = []
            if "l_slots" in self.optical_bands[optical_band_id].keys():
                if len(self.optical_bands[optical_band_id]["l_slots"]) > 0:
                    a_l = l_sts
                    b_l = self.optical_bands[optical_band_id]["l_slots"]
                    l_sts = common_slots(a_l, b_l)
                else:
                    l_sts = []
            else:
                l_sts = []
            if "s_slots" in self.optical_bands[optical_band_id].keys():
                if len(self.optical_bands[optical_band_id]["s_slots"]) > 0:
                    a_s = s_sts
                    b_s = self.optical_bands[optical_band_id]["s_slots"]
                    s_sts = common_slots(a_s, b_s)
                else:
                    s_sts = []
            else:
                s_sts = []

        return c_sts, l_sts, s_sts

    def update_link(self, fib, slots, band):
        for i in slots:
            fib[band].remove(i)
        if 'used' in fib:
            fib['used'] = True

    def update_optical_band(self, optical_band_id, slots, band):
        for i in slots:
            self.optical_bands[optical_band_id][band].remove(i)

    def restore_link(self, fib, slots, band):
        for i in slots:
            fib[band].append(int(i))
        if 'used' in fib:
            fib['used'] = False
        fib[band].sort()

    def restore_optical_band(self, optical_band_id, slots, band):
        for i in slots:
            self.optical_bands[optical_band_id][band].append(int(i))
        self.optical_bands[optical_band_id][band].sort()

    def del_flow(self, flow, o_b_id = None):
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
        if o_b_id is not None:
            self.restore_optical_band(o_b_id, slots, band)
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
            if o_b_id is not None:
                rev_o_band_id = self.optical_bands[o_b_id]["reverse_optical_band_id"]
                self.restore_optical_band(rev_o_band_id, slots, band)
        return True

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
        band, slots = slot_selection(c, l, s, n_slots, self.c_slot_number, self.l_slot_number, self.s_slot_number)
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
        #if len(links) == 1:

        for lx in fibers_f:
            if lx == add:
                inport = "0"
                r_outport = "0"
            if lx == drop:
                outport = "0"
                r_inport = "0"
            f = fibers_f[lx]
            src, dst = lx.split("-")
            outport = self.links_dict[lx]['fibers'][f]["src_port"]
            t_flows[src] = {}
            t_flows[src]["f"] = {}
            t_flows[src]["b"] = {}
            t_flows[src]["f"] = {"in": inport, "out": outport}

            if bidir:
                r_inport = self.links_dict[lx]['fibers'][f]["local_peer_port"]
                t_flows[src]["b"] = {"in": r_inport, "out": r_outport}

            inport = self.links_dict[lx]['fibers'][f]["dst_port"]
            if bidir:
                r_outport = self.links_dict[lx]['fibers'][f]["remote_peer_port"]
            t_flows[dst] = {}
            t_flows[dst]["f"] = {}
            t_flows[dst]["b"] = {}
            t_flows[dst]["f"] = {"in": inport, "out": "0"}
            if bidir:
                t_flows[dst]["b"] = {"in": "0", "out": r_outport}

        if debug:
            print(self.links_dict)

        if debug:
            print(t_flows)
        print("INFO: Flow matrix computed")

        return t_flows, band, slots, fibers_f, fibers_b

    def select_slots_and_ports_fs(self, links, n_slots, c, l, s, bidir, o_band_id):
        if debug:
            print(self.links_dict)
        band, slots = slot_selection(c, l, s, n_slots, self.c_slot_number, self.l_slot_number, self.s_slot_number)
        if band is None:
            print("No slots available in the three bands")
            return None, None, None, None, None
        if debug:
            print(band, slots)
        fibers_f = self.get_fibers_forward(links, slots, band)
        self.update_optical_band(o_band_id, slots, band)
        fibers_b = []
        if bidir:
            fibers_b = self.get_fibers_backward(links, fibers_f, slots, band)

            rev_o_band_id = self.optical_bands[o_band_id]["reverse_optical_band_id"]
            self.update_optical_band(rev_o_band_id, slots, band)
        if debug:
            print("forward")
            print(fibers_f)
            if bidir:
                print("backward")
                print(fibers_b)
        add = links[0]
        drop = links[-1]
        port_0 = "0"

        t_flows = {}

        #flows_add_side
        f = fibers_f[add]
        src, dst = add.split("-")
        outport = self.links_dict[add]['fibers'][f]["src_port"]
        #T1 rules
        t_flows[src] = {}
        t_flows[src]["f"] = {}
        t_flows[src]["b"] = {}
        t_flows[src]["f"] = {"in": port_0, "out": outport}
        if bidir:
            r_inport = self.links_dict[add]['fibers'][f]["local_peer_port"]
            t_flows[src]["b"] = {"in": r_inport, "out": port_0}

        #R1 rules
        t_flows[dst] = {}
        t_flows[dst]["f"] = {}
        t_flows[dst]["b"] = {}
        inport = self.links_dict[add]['fibers'][f]["dst_port"]
        opt_band_src_port = self.optical_bands[o_band_id]["src_port"]
        t_flows[dst]["f"] = {"in": inport, "out": opt_band_src_port}
        if bidir:
            rev_opt_band_dst_port = self.optical_bands[rev_o_band_id]["dst_port"]
            r_outport = self.links_dict[add]['fibers'][f]["remote_peer_port"]
            t_flows[dst]["b"] = {"in": rev_opt_band_dst_port, "out": r_outport}

        #flows_drop_side
        # R2 rules
        f = fibers_f[drop]
        src, dst = drop.split("-")
        outport = self.links_dict[drop]['fibers'][f]["src_port"]
        t_flows[src] = {}
        t_flows[src]["f"] = {}
        t_flows[src]["b"] = {}
        opt_band_dst_port = self.optical_bands[o_band_id]["dst_port"]
        t_flows[src]["f"] = {"in": opt_band_dst_port, "out": outport}
        if bidir:
            rev_opt_band_src_port = self.optical_bands[rev_o_band_id]["src_port"]
            r_inport = self.links_dict[drop]['fibers'][f]["local_peer_port"]
            t_flows[src]["b"] = {"in": r_inport, "out": rev_opt_band_src_port}
        t_flows[dst] = {}
        t_flows[dst]["f"] = {}
        t_flows[dst]["b"] = {}
        inport = self.links_dict[drop]['fibers'][f]["dst_port"]
        t_flows[dst]["f"] = {"in": inport, "out": port_0}
        if bidir:
            r_inport = self.links_dict[drop]['fibers'][f]["remote_peer_port"]
            t_flows[dst]["b"] = {"in": port_0, "out": r_inport}

        if debug:
            print(self.links_dict)

        if debug:
            print(t_flows)
        print("INFO: Flow matrix computed for Flax Lightpath")

        return t_flows, band, slots, fibers_f, fibers_b

    def rsa_computation(self, src, dst, rate, bidir):
        self.flow_id += 1
        self.db_flows[self.flow_id] = {}
        self.db_flows[self.flow_id]["flow_id"] = self.flow_id
        self.db_flows[self.flow_id]["src"] = src
        self.db_flows[self.flow_id]["dst"] = dst
        self.db_flows[self.flow_id]["bitrate"] = rate
        self.db_flows[self.flow_id]["bidir"] = bidir

        links, path = self.compute_path(src, dst)
        op = 1
        if len(path) < 1:
            self.null_values(self.flow_id)
            return self.flow_id
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
            print("INFO: RSA completed for normal wavelenght connection")
            if flow_list is None:
                self.null_values(self.flow_id)
                return self.flow_id
            slots_i = []
            for i in slots:
                slots_i.append(int(i))
            # return links, path, flow_list, band_range, slots, fiber_f, fiber_b, op, num_slots, f0, band
            #        links, path, flows, bx, slots, fiber_f, fiber_b, op, n_slots, f0, band
            self.db_flows[self.flow_id]["flows"] = flow_list
            self.db_flows[self.flow_id]["band_type"] = band_range
            self.db_flows[self.flow_id]["slots"] = slots_i
            self.db_flows[self.flow_id]["fiber_forward"] = fiber_f
            self.db_flows[self.flow_id]["fiber_backward"] = fiber_b
            self.db_flows[self.flow_id]["op-mode"] = op
            self.db_flows[self.flow_id]["n_slots"] = num_slots
            self.db_flows[self.flow_id]["links"] = links
            self.db_flows[self.flow_id]["path"] = path
            self.db_flows[self.flow_id]["band"] = band
            self.db_flows[self.flow_id]["freq"] = f0
            self.db_flows[self.flow_id]["is_active"] = True
        return self.flow_id

    def null_values(self, flow_id):
        self.db_flows[flow_id]["flows"] = {}
        self.db_flows[flow_id]["band_type"] = ""
        self.db_flows[flow_id]["slots"] = []
        self.db_flows[flow_id]["fiber_forward"] = []
        self.db_flows[flow_id]["fiber_backward"] = []
        self.db_flows[flow_id]["op-mode"] = 0
        self.db_flows[flow_id]["n_slots"] = 0
        self.db_flows[flow_id]["links"] = {}
        self.db_flows[flow_id]["path"] = []
        self.db_flows[flow_id]["band"] = 0
        self.db_flows[flow_id]["freq"] = 0
        self.db_flows[flow_id]["is_active"] = False

    def null_values_ob(self, ob_id):
        self.optical_bands[ob_id]["flows"] = {}
        self.optical_bands[ob_id]["band_type"] = ""
        #self.optical_bands[ob_id]["slots"] = []
        self.optical_bands[ob_id]["fiber_forward"] = []
        self.optical_bands[ob_id]["n_slots"] = 0
        self.optical_bands[ob_id]["links"] = {}
        self.optical_bands[ob_id]["path"] = []
        self.optical_bands[ob_id]["band"] = 0
        self.optical_bands[ob_id]["freq"] = 0
        self.optical_bands[ob_id]["is_active"] = False
        self.optical_bands[ob_id]["c_slots"] = []
        self.optical_bands[ob_id]["l_slots"] = []
        self.optical_bands[ob_id]["s_slots"] = []
        self.optical_bands[ob_id]["served_lightpaths"] = []
        self.optical_bands[ob_id]["reverse_optical_band_id"] = 0

    def create_optical_band(self, links, path, src, dst, bidir):
        self.opt_band_id += 1
        forw_opt_band_id = self.opt_band_id
        self.optical_bands[forw_opt_band_id] = {}
        self.optical_bands[forw_opt_band_id]["optical_band_id"] = forw_opt_band_id
        self.optical_bands[forw_opt_band_id]["bidir"] = bidir
        back_opt_band_id = 0
        if bidir:
            self.opt_band_id += 1
            back_opt_band_id = self.opt_band_id
            self.optical_bands[back_opt_band_id] = {}
            self.optical_bands[back_opt_band_id]["optical_band_id"] = back_opt_band_id
            self.optical_bands[back_opt_band_id]["bidir"] = bidir
            self.optical_bands[back_opt_band_id]["reverse_optical_band_id"] = forw_opt_band_id
            self.optical_bands[forw_opt_band_id]["reverse_optical_band_id"] = back_opt_band_id
        else:
            self.optical_bands[forw_opt_band_id]["reverse_optical_band_id"] = 0
        op = 0
        temp_links = []
        num_slots = "all"
        if self.nodes_dict[path[0]]["type"] == "OC-TP":
            add_link = links[0]
            temp_links.append(add_link)
            links.remove(add_link)
            path.remove(path[0])
        self.optical_bands[forw_opt_band_id]["src"] = path[0]
        if bidir:
            self.optical_bands[back_opt_band_id]["dst"] = path[0]

        if self.nodes_dict[path[-1]]["type"] == "OC-TP":
            drop_link = links[-1]
            temp_links.append(drop_link)
            links.remove(drop_link)
            path.remove(path[-1])
        self.optical_bands[forw_opt_band_id]["dst"] = path[-1]
        if bidir:
            self.optical_bands[back_opt_band_id]["src"] = path[-1]

        c_slots, l_slots, s_slots = self.get_slots(links, num_slots)
        if debug:
            print(c_slots)
            print(l_slots)
            print(s_slots)
        if len(c_slots) > 0 or len(l_slots) > 0 or len(s_slots) > 0:
            flow_list, band_range, slots, fiber_f, fiber_b = self.select_slots_and_ports(links, num_slots, c_slots, l_slots, s_slots, bidir)
            f0, band = freqency_converter(band_range, slots)
            flow_list_b = {}
            rev_path = path.copy()
            rev_path.reverse()
            rev_links = reverse_links(links)
            if bidir:
                for dev_x in flow_list.keys():
                    flow_list_b[dev_x] = {}
                    flow_list_b[dev_x]["f"] = flow_list[dev_x]["b"]
                    del flow_list[dev_x]["b"]
                    rev_path = path.copy()
            if debug:
                print(f0, band)
            print("INFO: RSA completed for optical band")
            if flow_list is None:
                self.null_values(self.flow_id)
                return self.flow_id, []
            slots_i = []
            for i in slots:
                slots_i.append(int(i))
            # return links, path, flow_list, band_range, slots, fiber_f, fiber_b, op, num_slots, f0, band
            #        links, path, flows, bx, slots, fiber_f, fiber_b, op, n_slots, f0, band
            src_port = flow_list[path[0]]['f']['out']
            dst_port = flow_list[path[-1]]['f']['in']
            if len(fiber_f.keys()) == 1:
                link_x = list(fiber_f.keys())[0]
                fib_x = fiber_f[link_x]
                rev_dst_port = self.links_dict[link_x]['fibers'][fib_x]["local_peer_port"]
                rev_src_port = self.links_dict[link_x]['fibers'][fib_x]["remote_peer_port"]
            else:
                link_in = list(fiber_f.keys())[0]
                link_out = list(fiber_f.keys())[-1]

                fib_in = fiber_f[link_in]
                fib_out = fiber_f[link_out]
                rev_dst_port = self.links_dict[link_in]['fibers'][fib_in]["local_peer_port"]
                rev_src_port = self.links_dict[link_out]['fibers'][fib_out]["remote_peer_port"]

            self.optical_bands[forw_opt_band_id]["flows"] = flow_list
            self.optical_bands[forw_opt_band_id]["band_type"] = band_range
            self.optical_bands[forw_opt_band_id]["fiber_forward"] = fiber_f
            #self.optical_bands[forw_opt_band_id]["fiber_backward"] = fiber_b
            self.optical_bands[forw_opt_band_id]["op-mode"] = op
            self.optical_bands[forw_opt_band_id]["n_slots"] = num_slots
            self.optical_bands[forw_opt_band_id]["links"] = links
            self.optical_bands[forw_opt_band_id]["path"] = path
            self.optical_bands[forw_opt_band_id]["band"] = band
            self.optical_bands[forw_opt_band_id]["freq"] = f0
            self.optical_bands[forw_opt_band_id]["is_active"] = True
            self.optical_bands[forw_opt_band_id]["src_port"] = src_port
            self.optical_bands[forw_opt_band_id]["dst_port"] = dst_port
            self.optical_bands[forw_opt_band_id][band_range] = slots_i
            self.optical_bands[forw_opt_band_id]["served_lightpaths"] = []
            if bidir:
                self.optical_bands[back_opt_band_id]["flows"] = flow_list_b
                self.optical_bands[back_opt_band_id]["band_type"] = band_range
                self.optical_bands[back_opt_band_id]["fiber_forward"] = fiber_b
                # self.optical_bands[back_opt_band_id]["fiber_backward"] = fiber_b
                self.optical_bands[back_opt_band_id]["op-mode"] = op
                self.optical_bands[back_opt_band_id]["n_slots"] = num_slots
                self.optical_bands[back_opt_band_id]["links"] = rev_links
                self.optical_bands[back_opt_band_id]["path"] = rev_path
                self.optical_bands[back_opt_band_id]["band"] = band
                self.optical_bands[back_opt_band_id]["freq"] = f0
                self.optical_bands[back_opt_band_id]["is_active"] = True
                self.optical_bands[back_opt_band_id]["src_port"] = rev_src_port
                self.optical_bands[back_opt_band_id]["dst_port"] = rev_dst_port
                self.optical_bands[back_opt_band_id][band_range] = slots_i.copy()
                self.optical_bands[back_opt_band_id]["served_lightpaths"] = []

        return forw_opt_band_id, temp_links

    def get_optical_bands(self, r_src, r_dst):
        result = []
        for ob_id in self.optical_bands:
            ob = self.optical_bands[ob_id]
            if debug:
                print(r_src, ob["src"])
                print(r_dst, ob["dst"])
                print(ob)
            if ob["src"] == r_src and ob["dst"] == r_dst:
                result.append(ob_id)
        return result

    def rsa_fs_computation(self, src, dst, rate, bidir):
        if self.nodes_dict[src]["type"] == "OC-ROADM" and self.nodes_dict[dst]["type"] == "OC-ROADM":
            print("INFO: ROADM to ROADM connection")
            links, path = self.compute_path(src, dst)
            if len(path) < 1:
                self.null_values_ob(self.opt_band_id)
                return self.flow_id, []
            optical_band_id, temp_links = self.create_optical_band(links, path, src, dst, bidir)
            return None, optical_band_id
        print("INFO: TP to TP connection")

        #todo check with multiple links
        #in case T1 is connected to R1 and R2
        temp_links2 = []
        temp_path = []
        src_links = get_links_form_node(self.links_dict, src)
        dst_links = get_links_to_node(self.links_dict, dst)
        if len(src_links.keys()) >= 1:
            temp_links2.append(list(src_links.keys())[0])
        if len(src_links.keys()) >= 1:
            temp_links2.append(list(dst_links.keys())[0])
        if len(temp_links2) == 2:
            [t_src, roadm_src] = temp_links2[0].split('-')
            [roadm_dst, t_dst] = temp_links2[1].split('-')
            temp_path.append(t_src)
            temp_path.append(roadm_src)
            temp_path.append(roadm_dst)
            temp_path.append(t_dst)
            existing_ob = self.get_optical_bands(roadm_src, roadm_dst)
            self.flow_id += 1
            self.db_flows[self.flow_id] = {}
            self.db_flows[self.flow_id]["flow_id"] = self.flow_id
            self.db_flows[self.flow_id]["src"] = src
            self.db_flows[self.flow_id]["dst"] = dst
            self.db_flows[self.flow_id]["bitrate"] = rate
            self.db_flows[self.flow_id]["bidir"] = bidir
            if len(existing_ob) > 0:
                print("INFO: Evaluating existing OB  {}".format(existing_ob))
                #first checking in existing OB
                ob_found = 0
                for ob_id in existing_ob:
                    op, num_slots = map_rate_to_slot(rate)
                    if debug:
                        print(temp_links2)
                    c_slots, l_slots, s_slots = self.get_slots(temp_links2, num_slots, ob_id)
                    if debug:
                        print(c_slots)
                        print(l_slots)
                        print(s_slots)
                    if len(c_slots) >= num_slots or len(l_slots) >= num_slots or len(s_slots) >= num_slots:
                        flow_list, band_range, slots, fiber_f, fiber_b = self.select_slots_and_ports_fs(temp_links2, num_slots,
                                                                                                        c_slots,
                                                                                                        l_slots, s_slots, bidir,
                                                                                                        ob_id)
                        f0, band = freqency_converter(band_range, slots)
                        if debug:
                            print(f0, band)
                        print("INFO: RSA completed for Flex Lightpath with OB already in place")
                        if flow_list is None:
                            self.null_values(self.flow_id)
                            continue
                        slots_i = []
                        for i in slots:
                            slots_i.append(int(i))
                        # return links, path, flow_list, band_range, slots, fiber_f, fiber_b, op, num_slots, f0, band
                        #        links, path, flows, bx, slots, fiber_f, fiber_b, op, n_slots, f0, band
                        self.db_flows[self.flow_id]["flows"] = flow_list
                        self.db_flows[self.flow_id]["band_type"] = band_range
                        self.db_flows[self.flow_id]["slots"] = slots_i
                        self.db_flows[self.flow_id]["fiber_forward"] = fiber_f
                        self.db_flows[self.flow_id]["fiber_backward"] = fiber_b
                        self.db_flows[self.flow_id]["op-mode"] = op
                        self.db_flows[self.flow_id]["n_slots"] = num_slots
                        self.db_flows[self.flow_id]["links"] = temp_links2
                        self.db_flows[self.flow_id]["path"] = temp_path
                        self.db_flows[self.flow_id]["band"] = band
                        self.db_flows[self.flow_id]["freq"] = f0
                        self.db_flows[self.flow_id]["is_active"] = True
                        self.db_flows[self.flow_id]["parent_opt_band"] = ob_id
                        self.db_flows[self.flow_id]["new_optical_band"] = False
                        self.optical_bands[ob_id]["served_lightpaths"].append(self.flow_id)
                        if bidir:
                            rev_ob_id = self.optical_bands[ob_id]["reverse_optical_band_id"]
                            self.optical_bands[rev_ob_id]["served_lightpaths"].append(self.flow_id)
                        return self.flow_id, ob_id
                    else:
                        print("not enough slots")
        print("INFO: Not existing OB meeting requirements")
        #if no OB I create a new one
        links, path = self.compute_path(src, dst)
        optical_band_id, temp_links = self.create_optical_band(links, path, src, dst, bidir)
        op, num_slots = map_rate_to_slot(rate)
        if debug:
            print(temp_links)
        c_slots, l_slots, s_slots = self.get_slots(temp_links, num_slots, optical_band_id)
        if debug:
            print(c_slots)
            print(l_slots)
            print(s_slots)
        if len(c_slots) > 0 or len(l_slots) > 0 or len(s_slots) > 0:
            flow_list, band_range, slots, fiber_f, fiber_b = self.select_slots_and_ports_fs(temp_links, num_slots, c_slots,
                                                                                            l_slots, s_slots, bidir, optical_band_id)
            f0, band = freqency_converter(band_range, slots)
            if debug:
                print(f0, band)
            print("INFO: RSA completed for FLex Lightpath with new OB")
            if flow_list is None:
                self.null_values(self.flow_id)
                return self.flow_id, optical_band_id
            slots_i = []
            for i in slots:
                slots_i.append(int(i))

            self.db_flows[self.flow_id]["flows"] = flow_list
            self.db_flows[self.flow_id]["band_type"] = band_range
            self.db_flows[self.flow_id]["slots"] = slots_i
            self.db_flows[self.flow_id]["fiber_forward"] = fiber_f
            self.db_flows[self.flow_id]["fiber_backward"] = fiber_b
            self.db_flows[self.flow_id]["op-mode"] = op
            self.db_flows[self.flow_id]["n_slots"] = num_slots
            self.db_flows[self.flow_id]["links"] = temp_links
            self.db_flows[self.flow_id]["path"] = path
            self.db_flows[self.flow_id]["band"] = band
            self.db_flows[self.flow_id]["freq"] = f0
            self.db_flows[self.flow_id]["is_active"] = True
            self.db_flows[self.flow_id]["parent_opt_band"] = optical_band_id
            self.db_flows[self.flow_id]["new_optical_band"] = True
            self.optical_bands[optical_band_id]["served_lightpaths"].append(self.flow_id)
            if bidir:
                rev_ob_id = self.optical_bands[optical_band_id]["reverse_optical_band_id"]
                self.optical_bands[rev_ob_id]["served_lightpaths"].append(self.flow_id)
        return self.flow_id, optical_band_id
