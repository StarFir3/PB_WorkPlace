import csv
import numpy as np
from sklearn import preprocessing
import torch
from torch_geometric.data import Data

# Read csv file with delimiter , 
with open('attack_camflow-0-h.csv') as csvfile:
    readCSV = csv.reader(csvfile, delimiter=',')
    # list for storing sources, destination, attributes
    list_src = []
    list_dst = []
    list_attr = []
    list_node_feature = []
    list_edge_type = []
    # Reading line by line
    for row in readCSV:
        # Append src, dst and attr to respective lists
        list_src.append(row[0])
        list_dst.append(row[1])
        list_attr.append(row[2])
        # Split attr to get src_type, dst_type and edge_type
        attr = row[2].split(':')
        src_type=attr[0]
        dst_type=attr[1]
        edge_type=attr[2]
        list_edge_type.append(edge_type)
        # Combining src_id with src_type and
        #           dst_id with dst_type
        # We want to create data.x (Node Feature Matrix)
        srcid_srctype = [row[0],src_type]
        dstid_dsttype = [row[1],dst_type]
        if not srcid_srctype in list_node_feature:
            list_node_feature.append(srcid_srctype)
        if not dstid_dsttype in list_node_feature:
            list_node_feature.append(dstid_dsttype)

    # Storing all nodes by combining list_src, list_dst
    nodes = list_src + list_dst

    # Using LabelEncoder normalize labels between 0 and n_classes -1
    le = preprocessing.LabelEncoder()
    le.fit(nodes)
    source_node = le.transform(list_src)
    target_node = le.transform(list_dst)
    # Edge feature matrix with shape [num_edges, num_edge_features]
    mat_edge_attr = np.c_[list_edge_type]
    print("Edge Feature Matrix")
    print(mat_edge_attr)
    # Edge feature matrix with shape [num_edges, num_edge_features]
    mat_edge_index = [source_node, target_node]

    # Node feature matrix with shape [num_nodes, num_node_features]

    # Converting list_node_feature with node_id and node_type to np.array
    mat_node_feature = np.array(list_node_feature)
    # Extract node_id and node_type
    # Transform node_id 
    mat_node_feature[:,0] = le.transform(mat_node_feature[:,0])
    # Sort by first column, casting as integar
    mat_node_feature2 = mat_node_feature[mat_node_feature[:,0].astype('int').argsort()]
    # Extract node_feature from mat_node_feature
    mat_node_feature3 = mat_node_feature2[:,1]
    mat_node_feature4 = np.c_[mat_node_feature3]
    print("Node Feature Matrix")
    print(mat_node_feature4)
    print("Edge_Index")
    print(mat_edge_index)
    #edge_index = torch.tensor(mat_edge_index, dtype=torch.float)
    #edge_attr = torch.tensor(mat_edge_attr)
    #x = torch.tensor(mat_node_feature4,dtype=torch.float)
    #data = Data(x=x, edge_index=edge_index)


