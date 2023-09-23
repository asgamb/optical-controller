import numpy as np
from variables import  *

#tool
def common_slots(a, b):
    return list(np.intersect1d(a, b))


#tool
def map_modulation_to_op(mod):
    if mod == "DP-QPSK":
        return 1
    if mod == "DP-16QAM":
        return 7

#tool
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

#tool
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

#tool
def combine(ls1, ls2):
    temp = ls1
    for i in ls2:
        if i not in ls1:
            temp.append(i)
    temp.sort()
    return temp


#tool
def list_in_list(a, b):
    # convert list A to numpy array
    a_arr = np.array(a)
    # convert list B to numpy array
    b_arr = np.array(b)

    for i in range(len(b_arr)):
        if np.array_equal(a_arr, b_arr[i:i + len(a_arr)]):
            return True
    return False


#tool
def reverse_link(link):
    s, d = link.split('-')
    r_link = "{}-{}".format(d, s)
    return r_link


#tool
def get_slot_frequency(b, n):
    if debug:
        print(n)
    if b == "c_slots":
        return Fc + n * 12.5
    if b == "s_slots":
        return Fs + n * 12.5
    if b == "l_slots":
        return Fl + n * 12.5


#tool
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
        f0 = fx + 6.25
    else:
        f0 = get_slot_frequency(b, slots[int((l + 1) / 2) - 1])
    return f0, 12.5 * l
