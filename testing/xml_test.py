#!/usr/bin/python

import xml.etree.ElementTree as ET
import re
head_map = {}
def parse_head(file_name, head_name):
    w = ''
    f = open(file_name, 'r')
    p = re.compile('^\<'+head_name+'\s')
    p2 = re.compile('xmlns\:\w+\=\".+\"')
    for line in f.readlines():
        if p.search(line):
            w = p2.findall(line)
        f.close()
    s = w[0].split(" ")
    res = {}
    for e in s:
        v = e[6:].split("=")
        res[v[1]] = v[0]
    return res
    #r = w.group()[6:]
    #r = r.split("=")
    #return {r[1]: r[0]}

def rec(elem, obj):
    obj = {}
    for child in elem:
        nobj = {}
        nobj = rec(child, obj)
        if not child.text:
            for htag in head_map.keys():
                hntag = htag[1:-1]
                if child.tag.find(hntag) != -1:
                    s = child.tag.replace('{'+hntag+'}', head_map[htag]+':')
                    obj[s] = ''
                    break
                else:
                    obj[child.tag] = ''
        else:
            if child.text.strip() == "":
                rtag = ''
                for htag in head_map.keys():
                    hntag = htag[1:-1]
                    if child.tag.find(hntag) != -1:
                        s = child.tag.replace('{'+hntag+'}', head_map[htag]+':')
                        rtag = s
                        break
                    else:
                        rtag = child.tag
                try:
                    s = obj[rtag]
                    if isinstance(obj[rtag], dict):
                        new_arr = []
                        new_arr.append(obj[rtag])
                        new_arr.append(nobj)
                        obj[rtag] = new_arr
                    else:
                        old_arr = obj[rtag]
                        old_arr.append(nobj)
                        obj[rtag] = old_arr
                except:
                    obj[rtag] = nobj
            else:
                rtag = ''
                for htag in head_map.keys():
                    hntag = htag[1:-1]
                    if child.tag.find(hntag) != -1:
                        s = child.tag.replace('{'+hntag+'}', head_map[htag]+':')
                        rtag = s
                        break
                    else:
                        rtag = child.tag
                try:
                    s = obj[rtag]
                    if isinstance(obj[rtag], str):
                        new_arr = []
                        new_arr.append(obj[rtag])
                        new_arr.append(child.text)
                        obj[rtag] = new_arr
                    else:
                        old_arr = obj[rtag]
                        old_arr.append(child.text)
                        obj[rtag] = old_arr
                except:
                    #{sad}comment
                    for htag in head_map.keys():
                        hntag = htag[1:-1]
                        if child.tag.find(hntag) != -1:
                            s = child.tag.replace('{'+hntag+'}', head_map[htag]+':')
                            obj[s] = child.text
                            break
                        else:
                            obj[child.tag] = child.text
    return obj

def main(file_name):
    tree = ET.parse(file_name)
    root = tree.getroot()
    head = root.tag
    global head_map 
    head_map = parse_head(file_name, head)
    obj = {}
    obj = rec(root, obj)
    res = {}
    res[head] = obj
    print 'FINISH HIM'
    print res

if __name__ == "__main__":
    main('test.xml')
