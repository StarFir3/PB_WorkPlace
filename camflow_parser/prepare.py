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
from numpy import asarray
from sklearn.preprocessing import OneHotEncoder
from sklearn.compose import ColumnTransformer 
from scipy.sparse import hstack
from scipy.sparse import csr_matrix

#import torch
#from torch_geometric.data import Data

# make argparse arguments global
CONSOLE_ARGUMENTS = None
OUTPUT_FOLDER = ""
list_node = []
list_edge = []
cnt_edges_wo_nodes_eg = 0
cnt_edges_wo_nodes_fn = 0

# labe encoder for base64
le_base64 = preprocessing.LabelEncoder()

def hashgen(l):
    """Generate a single hash value from a list. @l is a list of
    string values, which can be properties of a node/edge. This
    function returns a single hashed integer value."""
    hasher = xxhash.xxh64()
    for e in l:
        hasher.update(e)
    return hasher.intdigest()


def nodegen(node, node_type, base64_data):
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
    l.insert(0, base64_data)
    list_node.append(l)


def edgegen(edge, edge_type, node_map):
    """Generate a single hash value for a CamFlow edge. We
    hash type information and flags. @edge is the CamFlow
    edge data, parsed as a dictionary. This function returns
    a single hashed integer value of the edge."""
    global cnt_edges_wo_nodes_eg
    l = list()
    # Get the src_id and dst_id for edge_type
    src_id, dst_id = get_src_dst_id(edge_type)
    #list_edge_feature = ['cf:id', 'prov:type', 'cf:boot_id', 'cf:machine_id', 'cf:date', 'cf:jiffies', 'prov:label', 'cf:allowed', 'prov:activity', 'prov:entity', 'cf:offset']
    list_edge_feature = ['cf:id', 'prov:type', src_id, dst_id]
    assert(edge["prov:type"])               # CamFlow edge must contain "prov:type" field
    #l.append(edge["prov:type"])
    for feature in list_edge_feature:
        if feature in edge:
            l.append(edge[feature])
        else:
            l.append('N/A')
    
    l.insert(1, edge_type)

    if src_id in edge and dst_id in edge:
        srcUUID = edge[src_id]
        dstUUID = edge[dst_id]
        # both source and destination node must
        # exist in @node_map; if not, we will
        # have to skip the edge. Log this issue
        # if verbose is set.
        if srcUUID not in node_map or dstUUID not in node_map:
            cnt_edges_wo_nodes_eg = cnt_edges_wo_nodes_eg + 1
            pass
        else:
            list_edge.append(l)
    

def parse_nodes(json_string, node_map):
    """Parse a CamFlow JSON string that may contain nodes ("activity" or "entity").
    Parsed nodes populate @node_map, which is a dictionary that maps the node's UID,
    which is assigned by CamFlow to uniquely identify a node object, to a hashed
    value (in str) which represents the 'type' of the node. """
    try:
        # use "ignore" if non-decodeable exists in the @json_string
#        json_object = json.loads(json_string.decode("utf-8","ignore"))
        json_object = json.loads(json_string)
    except Exception as e:
        print("\nException ({}) occurred when parsing a node in JSON:".format(e))
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

def get_src_dst_id(var):
    #possible valuse for var ["used", "wasGeneratedBy", "wasInformedBy", "wasDerivedFrom", "wasAssociatedWith"}
    if var == "used":
        src = "prov:entity"
        dst = "prov:activity"
    elif var == "wasGeneratedBy":
        src = "prov:activity"
        dst = "prov:entity"
    elif var == "wasInformedBy":
        src = "prov:informant"
        dst = "prov:informed"
    elif var == "wasDerivedFrom":
        src = "prov:usedEntity"
        dst = "prov:generatedEntity"
    elif var == "wasAssociatedWith":
        src = "prov:agent"
        dst = "prov:activity"

    return src,dst



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
    global cnt_edges_wo_nodes_fn
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
#            json_object = json.loads(line.decode("utf-8","ignore"))
            json_object = json.loads(line)            
            # var takes the value of "used", "wasGeneratedBy", "wasInformedBy", "wasDerivedFrom", "wasAssociatedWith"
            for var in edge_possible_value:
                # Edge information can be stored in different variable as per the entity_type: used, wasGeneratedBy,wasDerviedFrom
                # For example; If entity_type is used, src_node and dst_node is stored in `prov_entity` and `prov_activity`
                #              If entity_type is wasDerivedFrom, it is stored in `prov:usedEntity` and `prov:generatedEntity`
                src_id, dst_id = get_src_dst_id(var)
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
                            edgetype = edgegen(var_json_object[uid], var, node_map)
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
                        if src_id not in var_json_object[uid]:
                            # an edge's source node must exist;
                            # if not, we will have to skip the
                            # edge. Log this issue if verbose is set.
                            if CONSOLE_ARGUMENTS.verbose:
                                logging.debug("edge (" + var + "/{}) record without source UUID: {}".format(var[uid]["prov:type"], uid))
                            continue
                        if dst_id not in var_json_object[uid]:
                            # an edge's destination node must exist;
                            # if not, we will have to skip the edge.
                            # Log this issue if verbose is set.
                            if CONSOLE_ARGUMENTS.verbose:
                                logging.debug("edge (" + var + "/{}) record without destination UUID: {}".format(var[uid]["prov:type"], uid))
                            continue
                        srcUUID = var_json_object[uid][src_id]
                        dstUUID = var_json_object[uid][dst_id]
                        # both source and destination node must
                        # exist in @node_map; if not, we will
                        # have to skip the edge. Log this issue
                        # if verbose is set.
                        if srcUUID not in node_map:
                            cnt_edges_wo_nodes_fn = cnt_edges_wo_nodes_fn + 1
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



def label_encode_node():
    # Tranform Node List
    # Sampel list_node one entry
    # Base64_id, node_id, node_type, prov_type
    #[[u'cf:AAAIAAAAACA68gAAA...AAAAAAAAA=', u'62010', 'Entity', u'path']

    # Creating two np arrays for reference purpose; one for transforming and one for original
    mat_list_node = np.array(list_node)
    trans_mat_list_node = np.array(list_node)

    ### Creating Node Feature Matrix ###

    # Transforming base64_id "cf:AAAIAAAAACA68gAAA...AAAAAAAAA=" to 0 to n-1
    
    base64_id = mat_list_node[:,0]
    le_base64.fit(base64_id)
    # Directly changing the trans_mat_list_node 
    trans_mat_list_node[:,0] = le_base64.transform(trans_mat_list_node[:,0])

    # Tranforming node_type "Entity and Activity" to 0 to 1
    le_node_type = preprocessing.LabelEncoder()
    node_type = mat_list_node[:,2]
    le_node_type.fit(node_type)
    trans_mat_list_node[:,2] = le_node_type.transform(trans_mat_list_node[:,2])
    
    # Tranforming Node prov_type from "path, address etc." to 0, 1 
    # Performing Hot Encoding # Refer Hot Encoding
    data_prov_type_node = asarray([['unknown'], ['string'], ['task'],['inode_unknown'], ['link'], ['file'],['directory'], ['char'], ['block'],['pipe'], ['socket'], ['msg'],['shm'], ['address'], ['sb'], ['path'],['disc_entity'], ['disc_activity'], ['disc_agent'],['machine'], ['packet'], ['iattr'], ['xattr'], ['packet_content'], ['argv'],['envp'], ['process_memory'], ['mmaped_file']])
    # Creating a instance of One Hot Encoder
    enc_node = OneHotEncoder(sparse=False)
    enc_node.fit(data_prov_type_node)
    # Copying the prov:type column from the transformed_mat_list_node -- node matrix
    prov_type = trans_mat_list_node[:,3]
    # delete column (prov_type) before combining onehot code
    del_prov_type = np.delete(trans_mat_list_node,3,1)


    # Converting it into list of list (array)! Should be better way
    temp_list_2 = []
    for item in prov_type:
        temp_list = [item]
        temp_list_2.append(temp_list)
    a_prov_type = np.array(temp_list_2)
    # Transformed the prov_type
    temp = enc_node.transform(a_prov_type)
    # Horizontally stack the matrix. A | B = AB (We are just adding more columns as we have same number of rows)
    temp2 = np.hstack((del_prov_type, temp.astype(np.int)))
    # Delete column 3 with axis 1; Axis 1 is for column
    #temp3 = np.delete(temp2, 3, 1)
    prov_type_labels = enc_node.get_feature_names()
    # Sorting the Node Matrix with base64_id
    trans_mat_list_node = temp2.astype(np.int)
    sorted_trans_mat_list_node = trans_mat_list_node[trans_mat_list_node[:,0].astype('int').argsort()]
    node_feature = sorted_trans_mat_list_node.astype(np.int)
    # Writing Node Feature Matrix
    node_header = ["base64_data", "cf:id","node_type"]
    for item in prov_type_labels:
        node_header.append(str(item))
    node_header_str = str(node_header).strip('[]')
    fmt = ",".join(["%s"] + ["%10.6e"] * (node_feature.shape[1]-1))
    node_file = OUTPUT_FOLDER + "/" +  "node_feature_x.csv"
    #print(node_header_str)
    np.savetxt(node_file, node_feature, fmt = fmt, header= node_header_str, comments='' )
    del node_feature
    print("Finish Label Encoding Nodes")



def label_encode_edge():

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


# Create Edge Matrix by extracting 3rd and 4th coloumn (Src and Destination)
    src_array = trans_mat_list_edge_wo_na[:,3]
    dst_array = trans_mat_list_edge_wo_na[:,4]
    # Create a np array with size of src_array
    mat_edge_list = np.zeros((src_array.size,2))
    mat_edge_list[:,0] = src_array
    mat_edge_list[:,1] = dst_array
    
    # Create egde_index in COO format
    edge_index = np.transpose(mat_edge_list)
    edge_file = OUTPUT_FOLDER + "/" + "edge_index.csv"
    np.savetxt(edge_file, edge_index, delimiter=",")
    del edge_index

    # edge_type, prov_type
    # -> Transform both
    # -> 2 sparse matrix
    # -> Horizontally stack (concatenate) two sparse matrix
    # -> save the final matrix in csv (save sparse matrix into csv)
    # Tranforming edge_type from "used, WasGeneratedBy" etc to 0 to n - 1

    # Deleting Stuff cf:id, prov:activity and prov:entity
    trans_mat_list_edge_wo_na = np.delete(trans_mat_list_edge_wo_na, [0,3,4], 1)

    
    # One Hot code for edge_type (used, wasgeneratedby)
    data_edge_type = trans_mat_list_edge_wo_na[:,0]
    data_prov_type = trans_mat_list_edge_wo_na[:,1]

    poss_value_edge_type = asarray([['used'], ['wasGeneratedBy'], ['wasInformedBy'], ['wasDerivedFrom'], ['wasAssociatedWith']] )
    poss_value_prov_type = asarray([['unknown'], ['read'], ['read_ioctl'], ['write'], ['write_ioctl'], ['clone_mem'], ['msg_create'], ['socket_create'], ['socket_pair_create'], ['inode_create'], ['setuid'], ['setpgid'], ['getpgid'], ['sh_write'], ['memory_write'], ['bind'], ['connect'], ['connect_unix_stream'], ['listen'], ['accept'], ['open'], ['file_rcv'], ['file_lock'], ['file_sigio'], ['version_entity'], ['munmap'], ['shmdt'], ['link'], ['rename'], ['unlink'], ['symlink'], ['splice_in'], ['splice_out'], ['setattr'], ['setattr_inode'], ['accept_socket'], ['setxattr'], ['setxattr_inode'], ['removexattr'], ['removexattr_inode'], ['named'], ['addressed'], ['exec'], ['exec_task'], ['packet_content'], ['clone'], ['version_activity'], ['search'], ['getattr'], ['getxattr'], ['getxattr_inode'], ['listxattr'], ['read_link'], ['mmap_read'], ['mmap_exec'], ['mmap_write'], ['mmap_read_private'], ['mmap_exec_private'], ['mmap_write_private'], ['sh_read'], ['memory_read'], ['send'], ['send_packet'], ['send_unix'], ['send_msg'], ['send_msg_queue'], ['receive'], ['receive_packet'], ['receive_unix'], ['receive_msg'], ['receive_msg_queue'], ['perm_read'], ['perm_write'], ['perm_exec'], ['perm_append'], ['terminate_task'], ['terminate_proc'], ['free'], ['arg'], ['env'], ['log'], ['sh_attach_read'], ['sh_attach_write'], ['sh_create_read'], ['sh_create_write'], ['load_file'], ['ran_on'], ['load_unknown'], ['load_firmware'], ['load_firmware_prealloc_buffer'], ['load_module'], ['load_kexec_image'], ['load_kexec_initramfs'], ['load_policy'], ['load_certificate'], ['load_undefined'], ['ptrace_attach'], ['ptrace_read'], ['ptrace_attach_task'], ['ptrace_read_task'], ['ptrace_traceme'], ['derived_disc'], ['generated_disc'], ['used_disc'], ['informed_disc'], ['influenced_disc'], ['associated_disc']])
    
    #creating a instace of One Hot Encoder
    enc_edge_type = OneHotEncoder(sparse=True)
    enc_prov_type = OneHotEncoder(sparse=True)

    # Fit the possible values of edge_type and prov_type into the One-Hot Encoder
    enc_edge_type.fit(poss_value_edge_type)
    enc_prov_type.fit(poss_value_prov_type)

    # Converting it into list of list (array)!
    # For edge_type
    edge_type_list = []
    for item in data_edge_type:
        edge = [item]
        edge_type_list.append(edge)
    a_edge_type = np.array(edge_type_list)

    # For prov_type
    prov_type_list = []
    for item in data_prov_type:
        prov = [item]
        prov_type_list.append(prov)
    a_prov_type = np.array(prov_type_list)

    #Transform edge and prov type 

    # Below are sparse matrix
    temp_edge = enc_edge_type.transform(a_edge_type)
    temp_prov = enc_prov_type.transform(a_prov_type)

    # adding more columns as we have same number of rows
    # Horizontal stacking both edge_type and prov_type
    temp_edge_2 = hstack((temp_edge, temp_prov))
    temp_edge_3 = temp_edge_2.toarray()
  
    # Get the labels for edge_type and prov_type
    edge_type_labels = enc_edge_type.get_feature_names()    
    prov_type_labels = enc_prov_type.get_feature_names()


    # Writing Edge Feature Matrix
    edge_header = []
    for item in edge_type_labels:
        edge_header.append(str(item))
    for item in prov_type_labels:
        edge_header.append(str(item))
    edge_header_str = str(edge_header).strip('[]')
    fmt = ",".join(["%s"] + ["%10.6e"] * (temp_edge_3.shape[1]-1))
    edge_attr_file = OUTPUT_FOLDER + "/" + "edge_attr.csv"
    np.savetxt(edge_attr_file, temp_edge_3, fmt = fmt, header= edge_header_str, comments='' )
    del temp_edge, temp_prov, temp_edge_2, temp_edge_3 

    print("Finished Edge Hot Encoding")

def process_file(input_file, output_folder, args):
    # A hack to run prepare.py from another module
    global CONSOLE_ARGUMENTS
    global OUTPUT_FOLDER
    global list_edge
    global list_node
    global cnt_edges_wo_nodes_eg
    global cnt_edges_wo_nodes_fn
    CONSOLE_ARGUMENTS = args
    OUTPUT_FOLDER = output_folder
    output_file = OUTPUT_FOLDER + "/" + "temp"

    # Intitialise the list_node and list_edge as they were staying persistant during function calls
    list_edge.clear()
    list_node.clear()
    node_map = dict()
    parse_all_nodes(input_file, node_map)
    print("Finished Parsing Nodes")
    total_edges = parse_all_edges(input_file, output_file, node_map, CONSOLE_ARGUMENTS.noencode)
    print("Finished Parsing Edges")
    print("Number of edges wo src/dst noticed in eg:" + str(cnt_edges_wo_nodes_eg))
    print("Number of edges wo src/dst noticed in fn:" + str(cnt_edges_wo_nodes_fn))
    label_encode_node()
    label_encode_edge()




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
    total_edges = parse_all_edges(args.input, args.output, node_map, args.noencode)
    print("Finished Parsing Edges")
       

    with open("node_matrix.csv", 'wb') as myfile:
        #writer = csv.DictWriter(myfile, fieldnames = ['uid', 'cf:id','node_type', 'prov:type', 'cf:pathname', 'prov:label', 'cf:machine_id', 'cf:version', 'cf:boot_id', 'cf:date', 'cf:epoch', 'cf:jiffies', 'cf:uid','cf:gid', 'cf:pid', 'cf:vpid', 'cf:XXXns', 'cf:secctx', 'cf:mode', 'cf:ino', 'cf:uuid', 'cf:length', 'cf:valid', 'cf:atime', 'cf:ctime', 'cf:mtime', 'cf:truncated',  'cf:content', 'cf:seq', 'cf:sender',  'cf:receiver', 'cf:address', 'cf:value' ])
        fieldnames = ['base64_data', 'cf:id','node_type', 'prov:type']
        writer = csv.DictWriter(myfile, fieldnames = fieldnames)
        writer.writeheader()
        #wr = csv.writer(myfile, quoting=csv.QUOTE_ALL)
        wr = csv.writer(myfile, delimiter=',')
        for item in list_node:
            wr.writerow(item)
    print("Finished Writing list of nodes")

    with open("edge_matrix.csv", 'wb') as myfile:
        #writer = csv.DictWriter(myfile, fieldnames = ['uid','cf:id', 'prov:type', 'cf:boot_id', 'cf:machine_id', 'cf:date', 'cf:jiffies', 'prov:label', 'cf:allowed', 'prov:activity', 'prov:entity', 'cf:offset'])
        fieldnames = ['cf:id', 'edge_type', 'prov:type', 'prov:activity', 'prov:entity']
        writer = csv.DictWriter(myfile, fieldnames = fieldnames)
        writer.writeheader()        
        #wr = csv.writer(myfile, quoting=csv.QUOTE_ALL)
        wr = csv.writer(myfile, delimiter=',')
        for item in list_edge:
            wr.writerow(item)            
    print("Finished Writing list of edges")

    label_encode_node()
    label_encode_edge()

    if args.stats:
        total_nodes = len(node_map)
        stats = open(args.stats_file, "a+")
        stats.write("{},{},{}\n".format(args.input, total_nodes, total_edges))

