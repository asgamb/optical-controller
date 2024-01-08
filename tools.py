import numpy as np
from variables import  *
import json


def common_slots(a, b):
    return list(np.intersect1d(a, b))


def map_modulation_to_op(mod):
    if mod == "DP-QPSK":
        return 1
    if mod == "DP-16QAM":
        return 7
    if mod == "DP-64QAM":
        return 10


def map_band_to_slot(band):
    return int(band/12.5)


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
    if rate == 1000:
        mod = "DP-64QAM"
        slots = 18
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


def list_in_list(a, b):
    # convert list A to numpy array
    a_arr = np.array(a)
    # convert list B to numpy array
    b_arr = np.array(b)

    for i in range(len(b_arr)):
        if np.array_equal(a_arr, b_arr[i:i + len(a_arr)]):
            return True
    return False


def reverse_link(link):
    s, d = link.split('-')
    r_link = "{}-{}".format(d, s)
    return r_link


def get_slot_frequency(b, n):
    if debug:
        print(n)
    if b == "c_slots":
        return Fc + n * 12.5
    if b == "s_slots":
        return Fs + n * 12.5
    if b == "l_slots":
        return Fl + n * 12.5


def freqency_converter(b, slots):
    l = len(slots)
    if debug:
        print(slots)
    if l % 2 == 0:
        if debug:
            print("pari {}".format(l))
        fx = get_slot_frequency(b, slots[int(l / 2)-1])
        if debug:
            print(fx)
        #GHz
        # #f0 = fx + 6.25
        #MHz
        f0 = int((fx + 6.25) * 1000)
    else:
        f0 = get_slot_frequency(b, slots[int((l + 1) / 2) - 1])
    #GHz
    # #return f0, 12.5 * l
    # MHz
    return f0, int((12.5 * l) * 1000)


def readTopologyData(nodes, topology):
        nodes_file = open(nodes, 'r')
        topo_file = open(topology, 'r')
        nodes = json.load(nodes_file)
        topo = json.load(topo_file)
        nodes_file.close()
        topo_file.close()
        return nodes, topo


def reverse_links(links):
    temp_links = links.copy()
    temp_links.reverse()
    result = []
    for link in temp_links:
        [a, b] = link.split("-")
        result.append("{}-{}".format(b, a))
    return result

def get_links_form_node(topology, node):
    result = {}
    for link in topology.keys():
        if "{}-".format(node) in link:
            result[link] = topology[link]
    return result

def get_links_to_node(topology, node):
    result = {}
    for link in topology.keys():
        if "-{}".format(node) in link:
            result[link] = topology[link]
    return result


def slot_selection(c, l, s, n_slots, Nc, Nl, Ns):
    # First Fit
    if isinstance(n_slots, int):
        slot_c = n_slots
        slot_l = n_slots
        slot_s = n_slots
    else:
        slot_c = Nc
        slot_l = Nl
        slot_s = Ns
    if len(c) >= slot_c:
        return "c_slots", c[0: slot_c]
    elif len(l) >= slot_l:
        return "l_slots", l[0: slot_l]
    elif len(l) >= slot_s:
        return "s_slots", s[0: slot_s]
    else:
        return None, None
