import torch
from torch_geometric.data import Data
from numpy import genfromtxt
from graphlime import GraphLIME

# Create Edge Index
data_edge_index = genfromtxt('edge_index.csv', delimiter=',')
edge_index = torch.tensor(data_edge_index, dtype = torch.long)

# Create Node Feature
data_node_feature = genfromtxt('node_feature_x.csv', delimiter=',')
node_feature = torch.tensor(data_node_feature, dtype = torch.long)

# Create Edge Feature
data_edge_feature = genfromtxt('edge_attr.csv', delimiter=',')
edge_feature = torch.tensor(data_edge_feature, dtype = torch.long)

# Create Data instance a `torch_geometric.data.Data` object
data = Data(x=node_feature, edge_index=edge_index, edge_attr=edge_feature)

model = ... # any GNN model
node_idx = 0  # the specific node to be explained

explainer = GraphLIME(model, hop=2, rho=0.1)
coefs = explainer.explain_node(node_idx, data.x, data.edge_index)