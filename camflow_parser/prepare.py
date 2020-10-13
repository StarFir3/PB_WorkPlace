import os
import sys
import argparse
import json
import logging
import xxhash
import time
import datetime
import tqdm
import csv
import numpy as np
from sklearn import preprocessing
#import torch
#from torch_geometric.data import Data

# make argparse arguments global
CONSOLE_ARGUMENTS = None
list_node = []
list_edge = []


def hashgen(l):
    """Generate a single hash value from a list. @l is a list of
    string values, which can be properties of a node/edge. This
    function returns a single hashed integer value."""
    hasher = xxhash.xxh64()
    for e in l:
        hasher.update(e)
    return hasher.intdigest()


def nodegen(node, node_type, uid):
    """Generate a single hash value for a CamFlow node.
    We hash type information, SELinux security context, mode, and name.
    @node is the CamFlow node data, parsed as a dictionary. This
    function returns a single hashed integer value for the node."""
    l = list()
    #list_node_feature = ['cf:id', 'prov:type', 'cf:pathname', 'prov:label', 'cf:machine_id', 'cf:version', 'cf:boot_id', 'cf:date', 'cf:epoch', 'cf:jiffies', 'cf:uid','cf:gid', 'cf:pid', 'cf:vpid', 'cf:XXXns', 'cf:secctx', 'cf:mode', 'cf:ino', 'cf:uuid', 'cf:length', 'cf:valid', 'cf:atime', 'cf:ctime', 'cf:mtime', 'cf:truncated',  'cf:content', 'cf:seq', 'cf:sender',  'cf:receiver', 'cf:address', 'cf:value' ]
    list_node_feature = ['cf:id', 'prov:type']
    assert(node["prov:type"])               # CamFlow node must contain "prov:type" field
    
    ##l.append(node["prov:type"])
    # CamFlow node may or may not have the
    # following fields. If not, we will
    # simply use N/A to represent absense.

    for feature in list_node_feature:
        if feature in node:
            l.append(node[feature])
        else:
            l.append('N/A')

    l.insert(1, node_type)
    base64_data = uid
    l.insert(0, base64_data)
    list_node.append(l)


def edgegen(edge, edge_type):
    """Generate a single hash value for a CamFlow edge. We
    hash type information and flags. @edge is the CamFlow
    edge data, parsed as a dictionary. This function returns
    a single hashed integer value of the edge."""
    l = list()
    #list_edge_feature = ['cf:id', 'prov:type', 'cf:boot_id', 'cf:machine_id', 'cf:date', 'cf:jiffies', 'prov:label', 'cf:allowed', 'prov:activity', 'prov:entity', 'cf:offset']
    list_edge_feature = ['cf:id', 'prov:type', 'prov:activity', 'prov:entity']
    assert(edge["prov:type"])               # CamFlow edge must contain "prov:type" field
    #l.append(edge["prov:type"])
    for feature in list_edge_feature:
        if feature in edge:
            l.append(edge[feature])
        else:
            l.append('N/A')
    
    l.insert(1, edge_type)

    list_edge.append(l)
    

def parse_nodes(json_string, node_map):
    """Parse a CamFlow JSON string that may contain nodes ("activity" or "entity").
    Parsed nodes populate @node_map, which is a dictionary that maps the node's UID,
    which is assigned by CamFlow to uniquely identify a node object, to a hashed
    value (in str) which represents the 'type' of the node. """
    try:
        # use "ignore" if non-decodeable exists in the @json_string
        json_object = json.loads(json_string.decode("utf-8","ignore"))
    except Exception as e:
        print("Exception ({}) occurred when parsing a node in JSON:".format(e))
        print(json_string)
        exit(1)
    if "activity" in json_object:
        activity = json_object["activity"]
        for uid in activity:
            if not uid in node_map:     # only parse unseen nodes
                if "prov:type" not in activity[uid]:
                    # a node must have a type.
                    # record this issue if logging is turned on
                    if CONSOLE_ARGUMENTS.verbose:
                        logging.debug("skipping a problematic activity node with no 'prov:type': {}".format(uid))
                else:
                    node_map[uid] = str(nodegen(activity[uid], "Activity", uid))

    if "entity" in json_object:
        entity = json_object["entity"]
        for uid in entity:
            if not uid in node_map:
                if "prov:type" not in entity[uid]:
                    if CONSOLE_ARGUMENTS.verbose:
                        logging.debug("skipping a problematic entity node with no 'prov:type': {}".format(uid))
                else:
                    node_map[uid] = str(nodegen(entity[uid], "Entity", uid))


def parse_all_nodes(filename, node_map):
    """Parse all nodes in CamFlow data. @filename is the file path of
    the CamFlow data to parse. @node_map contains the mappings of all
    CamFlow nodes to their hashed attributes. """
    description = '\x1b[6;30;42m[STATUS]\x1b[0m Parsing nodes in CamFlow data from {}'.format(filename)
    pb = tqdm.tqdm(desc=description, mininterval=1.0, unit=" recs")
    with open(filename, 'r') as f:
        # each line in CamFlow data could contain multiple
        # provenance nodes, we call @parse_nodes routine.
        for line in f:
            pb.update()                 # for progress tracking
            parse_nodes(line, node_map)
    f.close()
    pb.close()


def parse_all_edges(inputfile, outputfile, node_map, noencode):
    """Parse all edges (including their timestamp) from CamFlow data file @inputfile
    to an @outputfile. Before this function is called, parse_all_nodes should be called
    to populate the @node_map for all nodes in the CamFlow file. If @noencode is set,
    we do not hash the nodes' original UUIDs generated by CamFlow to integers. This
    function returns the total number of valid edge parsed from CamFlow dataset.

    The output edgelist has the following format for each line, if -s is not set:
        <source_node_id> \t <destination_node_id> \t <hashed_source_type>:<hashed_destination_type>:<hashed_edge_type>:<edge_logical_timestamp>
    If -s is set, each line would look like:
        <source_node_id> \t <destination_node_id> \t <hashed_source_type>:<hashed_destination_type>:<hashed_edge_type>:<edge_logical_timestamp>:<timestamp_stats>"""
    total_edges = 0
    smallest_timestamp = None
    # scan through the entire file to find the smallest timestamp from all the edges.
    # this step is only needed if we need to add some statistical information.
    
    # we will go through the CamFlow data (again) and output edgelist to a file
    output = open(outputfile, "w+")
    description = '\x1b[6;30;42m[STATUS]\x1b[0m Parsing edges in CamFlow data from {}'.format(inputfile)
    pb = tqdm.tqdm(desc=description, mininterval=1.0, unit=" recs")
    edge_possible_value = ["used", "wasGeneratedBy", "wasInformedBy", "wasDerivedFrom", "wasAssociatedWith"]
    with open(inputfile, 'r') as f:
        for line in f:
            pb.update()
            json_object = json.loads(line.decode("utf-8","ignore"))
            # var takes the value of "used", "wasGeneratedBy", "wasInformedBy", "wasDerivedFrom", "wasAssociatedWith"
            for var in edge_possible_value:
                if var in json_object:
                    var_json_object = json_object[var]
                    for uid in var_json_object:
                        if "prov:type" not in var_json_object[uid]:
                            # an edge must have a type; if not,
                            # we will have to skip the edge. Log
                            # this issue if verbose is set.
                            if CONSOLE_ARGUMENTS.verbose:
                                logging.debug("edge " + var + " record without type: {}".format(uid))
                            continue
                        else:
                            edgetype = edgegen(var_json_object[uid], var)
                        # cf:id is used as logical timestamp to order edges
                        if "cf:id" not in var_json_object[uid]:
                            # an edge must have a logical timestamp;
                            # if not we will have to skip the edge.
                            # Log this issue if verbose is set.
                            if CONSOLE_ARGUMENTS.verbose:
                                logging.debug("edge " + var + " record without logical timestamp: {}".format(uid))
                            continue
                        else:
                            timestamp = var_json_object[uid]["cf:id"]
                        if "prov:entity" not in var_json_object[uid]:
                            # an edge's source node must exist;
                            # if not, we will have to skip the
                            # edge. Log this issue if verbose is set.
                            if CONSOLE_ARGUMENTS.verbose:
                                logging.debug("edge (" + var + "/{}) record without source UUID: {}".format(var[uid]["prov:type"], uid))
                            continue
                        if "prov:activity" not in var_json_object[uid]:
                            # an edge's destination node must exist;
                            # if not, we will have to skip the edge.
                            # Log this issue if verbose is set.
                            if CONSOLE_ARGUMENTS.verbose:
                                logging.debug("edge (" + var + "/{}) record without destination UUID: {}".format(var[uid]["prov:type"], uid))
                            continue
                        srcUUID = var_json_object[uid]["prov:entity"]
                        dstUUID = var_json_object[uid]["prov:activity"]
                        # both source and destination node must
                        # exist in @node_map; if not, we will
                        # have to skip the edge. Log this issue
                        # if verbose is set.
                        if srcUUID not in node_map:
                            if CONSOLE_ARGUMENTS.verbose:
                                logging.debug("edge (" + var + "/{}) record with an unseen srcUUID: {}".format(var[uid]["prov:type"], uid))
                            continue
                        else:
                            srcVal = node_map[srcUUID]
                        if dstUUID not in node_map:
                            if CONSOLE_ARGUMENTS.verbose:
                                logging.debug("edge (" + var + "/{}) record with an unseen dstUUID: {}".format(var[uid]["prov:type"], uid))
                            continue
                        else:
                            dstVal = node_map[dstUUID]
                        if "cf:date" not in var_json_object[uid]:
                            # an edge must have a timestamp; if
                            # not, we will have to skip the edge.
                            # Log this issue if verbose is set.
                            if CONSOLE_ARGUMENTS.verbose:
                                logging.debug("edge (" + var + ") record without timestamp: {}".format(uid))
                            continue
                        else:
                            # we only record @adjusted_ts if we need
                            # to record stats of CamFlow dataset.
                            if CONSOLE_ARGUMENTS.stats:
                                ts_str = var_json_object[uid]["cf:date"]
                                ts = time.mktime(datetime.datetime.strptime(ts_str, "%Y:%m:%dT%H:%M:%S").timetuple())
                                adjusted_ts = ts - smallest_timestamp
                        total_edges += 1
                        if noencode:
                            if CONSOLE_ARGUMENTS.stats:
                                output.write("{}\t{}\t{}:{}:{}:{}:{}\n".format(srcUUID, dstUUID, srcVal, dstVal, edgetype, timestamp, adjusted_ts))
                            else:
                                output.write("{}\t{}\t{}:{}:{}:{}\n".format(srcUUID, dstUUID, srcVal, dstVal, edgetype, timestamp))
                        else:
                            if CONSOLE_ARGUMENTS.stats:
                                output.write("{}\t{}\t{}:{}:{}:{}:{}\n".format(hashgen([srcUUID]), hashgen([dstUUID]), srcVal, dstVal, edgetype, timestamp, adjusted_ts))
                            else:
                                output.write("{}\t{}\t{}:{}:{}:{}\n".format(hashgen([srcUUID]), hashgen([dstUUID]), srcVal, dstVal, edgetype, timestamp))

                
    f.close()
    output.close()
    pb.close()
    return total_edges



def label_encode():
    # Tranform Node List
    # Sampel list_node one entry
    #[[u'cf:AAAIAAAAACA68gAAA...AAAAAAAAA=', u'62010', 'Entity', u'path']

    # Creating two np arrays for reference purpose; one for transforming and one for original
    mat_list_node = np.array(list_node)
    trans_mat_list_node = np.array(list_node)
    # Transforming base64_id "cf:AAAIAAAAACA68gAAA...AAAAAAAAA=" to 0 to n-1
    le_base64 = preprocessing.LabelEncoder()
    base64_id = mat_list_node[:,0]
    le_base64.fit(base64_id)
    # Directly changing the trans_mat_list_node 
    trans_mat_list_node[:,0] = le_base64.transform(trans_mat_list_node[:,0])

    # Tranforming node_type "Entity and Activity" to 0 to 1
    le_node_type = preprocessing.LabelEncoder()
    node_type = mat_list_node[:,2]
    le_node_type.fit(node_type)
    trans_mat_list_node[:,2] = le_node_type.transform(trans_mat_list_node[:,2])
    
    # Tranforming prov_type from "path, address etc." to 0 to n -1
    le_prov_type = preprocessing.LabelEncoder()
    prov_type = mat_list_node[:,3]
    le_prov_type.fit(prov_type)
    trans_mat_list_node[:,3] = le_prov_type.transform(trans_mat_list_node[:,3])
    

    # Transform Edge List
    # Removing entries with N/A for prov:activity and prov:entity
    list_edge_wo_na = []
    for item in list_edge:
        src = item[3]
        if src not in ['N/A']:
            list_edge_wo_na.append(item)
    mat_list_edge_wo_na = np.array(list_edge_wo_na)
    trans_mat_list_edge_wo_na = np.array(list_edge_wo_na)
    # Tranforming cf:AAAIAAAAACA68gAAA...AAAAAAAAA= in "prov:activity/ Source" and "prov:entity/ Dest"
    trans_mat_list_edge_wo_na[:,3] = le_base64.transform(trans_mat_list_edge_wo_na[:,3])
    trans_mat_list_edge_wo_na[:,4] = le_base64.transform(trans_mat_list_edge_wo_na[:,4])

    # Tranforming edge_type from "used, WasGeneratedBy" etc to 0 to n - 1
    le_edge_type = preprocessing.LabelEncoder()
    edge_type = trans_mat_list_edge_wo_na[:,1]
    le_edge_type.fit(edge_type)
    trans_mat_list_edge_wo_na[:,1] = le_edge_type.transform(trans_mat_list_edge_wo_na[:,1])

    # Tranforming prov_type_edge (such as memory_read, memory_write, open) to 0 to n - 1
    le_prov_type_edge = preprocessing.LabelEncoder()
    prov_type_edge = trans_mat_list_edge_wo_na[:,2]
    le_prov_type_edge.fit(prov_type_edge)
    trans_mat_list_edge_wo_na[:,2] = le_prov_type_edge.transform(trans_mat_list_edge_wo_na[:,2])

    # Create Edge Matrix by extracting 3rd and 4th coloumn (Src and Destination)
    src_array = trans_mat_list_edge_wo_na[:,3]
    dst_array = trans_mat_list_edge_wo_na[:,4]
    # Create a np array with size of src_array
    mat_edge_list = np.zeros((src_array.size,2))
    mat_edge_list[:,0] = src_array
    mat_edge_list[:,1] = dst_array
    # Create egde_index in COO format
    edge_index = np.transpose(mat_edge_list)
    np.savetxt("edge_index.csv", edge_index, delimiter=",")
    #sorted_trans_mat_list_node = np.sort(trans_mat_list_node, axis = 0)
    sorted_trans_mat_list_node = trans_mat_list_node[trans_mat_list_node[:,0].astype('int').argsort()]
    node_feature = sorted_trans_mat_list_node.astype(np.int)
    np.savetxt("node_feature_x.csv", node_feature, delimiter=",")
    temp_edge_feature = trans_mat_list_edge_wo_na[:0-2]
    edge_feature = temp_edge_feature.astype(np.int)
    np.savetxt("edge_feature_x.csv", edge_feature, delimiter=",")


    ## Put into CSV edge_index, trans_mat_list_edge_wo_na and trans_mat_list_node

    print("Hello")




if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Convert CamFlow JSON to Unicorn edgelist')
    parser.add_argument('-i', '--input', help='input CamFlow data file path', required=True)
    parser.add_argument('-o', '--output', help='output edgelist file path', required=True)
    parser.add_argument('-n', '--noencode', help='do not encode UUID in output (default is to encode)', action='store_true')
    parser.add_argument('-v', '--verbose', help='verbose logging (default is false)', action='store_true')
    parser.add_argument('-l', '--log', help='log file path (only valid is -v is set; default is debug.log)', default='debug.log')
    parser.add_argument('-s', '--stats', help='record some statistics of the CamFlow graph data and runtime graph generation speed (default is false)', action='store_true')
    parser.add_argument('-f', '--stats-file', help='file path to record the statistics (only valid if -s is set; default is stats.csv)', default='stats.csv')
    args = parser.parse_args()

    CONSOLE_ARGUMENTS = args

    if args.verbose:
        logging.basicConfig(filename=args.log, level=logging.DEBUG)

    node_map = dict()
    parse_all_nodes(args.input, node_map)
    print("Finished Parsing Nodes")
    #print(list_node)
    total_edges = parse_all_edges(args.input, args.output, node_map, args.noencode)
    #print(list_edge)
    print("Finished Parsing Edges")
    # mat_list_node = []
    # mat_list_edge = []
    # for item in list_node:
    #     mat_list_node.append(list(list_node))
    # print("Finished Appending list of nodes")        
    # for item in list_edge:
    #     mat_list_edge.append(list(list_edge))
    # print("Finished Appending list of edges")        

    with open("node_matrix.csv", 'wb') as myfile:
        #writer = csv.DictWriter(myfile, fieldnames = ['uid', 'cf:id','node_type', 'prov:type', 'cf:pathname', 'prov:label', 'cf:machine_id', 'cf:version', 'cf:boot_id', 'cf:date', 'cf:epoch', 'cf:jiffies', 'cf:uid','cf:gid', 'cf:pid', 'cf:vpid', 'cf:XXXns', 'cf:secctx', 'cf:mode', 'cf:ino', 'cf:uuid', 'cf:length', 'cf:valid', 'cf:atime', 'cf:ctime', 'cf:mtime', 'cf:truncated',  'cf:content', 'cf:seq', 'cf:sender',  'cf:receiver', 'cf:address', 'cf:value' ])
        writer = csv.DictWriter(myfile, fieldnames = ['base64_data', 'cf:id','node_type', 'prov:type'])
        writer.writeheader()
        #wr = csv.writer(myfile, quoting=csv.QUOTE_ALL)
        wr = csv.writer(myfile, delimiter=',')
        for item in list_node:
            wr.writerow(item)
    print("Finished Writing list of nodes")

    with open("edge_matrix.csv", 'wb') as myfile:
        #writer = csv.DictWriter(myfile, fieldnames = ['uid','cf:id', 'prov:type', 'cf:boot_id', 'cf:machine_id', 'cf:date', 'cf:jiffies', 'prov:label', 'cf:allowed', 'prov:activity', 'prov:entity', 'cf:offset'])
        writer = csv.DictWriter(myfile, fieldnames = ['cf:id', 'edge_type', 'prov:type', 'prov:activity', 'prov:entity'])
        writer.writeheader()        
        #wr = csv.writer(myfile, quoting=csv.QUOTE_ALL)
        wr = csv.writer(myfile, delimiter=',')
        for item in list_edge:
            wr.writerow(item)            
    print("Finished Writing list of edges")

    label_encode()

    if args.stats:
        total_nodes = len(node_map)
        stats = open(args.stats_file, "a+")
        stats.write("{},{},{}\n".format(args.input, total_nodes, total_edges))

