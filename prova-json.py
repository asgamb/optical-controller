import json
from collections import Counter
from itertools import groupby

g = None
nodes_json = 'nodes.json'
topology_json = 'topology-optical.json'


def read_topology_data(nodex, topology):
    nodes_file = open(nodex, 'r')
    topo_file = open(topology, 'r')

    nodex = json.load(nodes_file)
    topox = json.load(topo_file)

    nodes_file.close()
    topo_file.close()

    return nodex, topox


def test(nodex, topox):
    for n in nodex:
        print(n)
        print(nodex[n])

    for l in topox:
        print(l)
        [s, d] = l.split('-')
        ps = topox[l]['source']
        pd = topox[l]['target']
        print(s, d, ps, pd)

def cons2(x, val):
   res = []
   temp = []
   x.sort()
   temp.append(x[0])
   y = 1
   print(len(x))
   for i in range(1, len(x)):
       if x[i] == x[i-1]+1:
           y += 1
           temp.append(x[i])
       else:
           if y >= val:
               res.extend(temp)
           temp = [x[i]]
           y = 1
       if i == len(x)-1 and y >= val:
           res.extend(temp)
   return res


def combine(ls1, ls2):
    temp = ls1
    for i in ls2:
        if i not in ls1:
            temp.append(i)
    temp.sort()
    return temp


if __name__ == '__main__':
    '''
    nodes, topo = read_topology_data(nodes_json, topology_json)
    test(nodes, topo)
    ar1 = [1, 5, 10, 40, 80]
    ar2 = [6, 7, 20, 80, 100]
    ar3 = [3, 4, 15, 20, 30, 70, 80, 120]
    ar = commonElement2(ar1, ar2)
    arx = commonElement2(ar, ar3)
    print(ar)
    '''


    data1 = [1, 2, 3, 4, 5, 6, 10, 15, 16, 17, 18, 22, 25, 26, 27, 28]

    data2 = [1, 2, 3, 4, 5, 6, 10, 11, 12, 13, 15, 16, 17, 18, 22, 25, 26, 27, 28]
    a = cons2(data1, 4)
    b = cons2(data2, 4)

    print(a)
    print(b)
    a = combine(a, b)
    print(a)
    print("a is {}".format(a))



