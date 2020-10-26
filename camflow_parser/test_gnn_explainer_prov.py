import torch
from torch_geometric.data import Data, DataLoader
from torch_geometric.data import Data
from numpy import genfromtxt
from graphlime import GraphLIME
from torch_geometric.nn import GCNConv
from torch.nn import Linear
import torch.nn.functional as F
import matplotlib.pyplot as plt
from torch_geometric.datasets import Planetoid
import torch_geometric.transforms as T
from torch_geometric.nn import GCNConv, GNNExplainer

data_list = []

# Create Edge Index
data_edge_index = genfromtxt('edge_index.csv', delimiter=',')
edge_index = torch.tensor(data_edge_index, dtype = torch.long)

# Create Node Feature
data_node_feature = genfromtxt('node_feature_x.csv', delimiter=',')
node_feature = torch.tensor(data_node_feature, dtype = torch.float)

# Create Edge Feature
data_edge_feature = genfromtxt('edge_attr.csv', delimiter=',')
edge_feature = torch.tensor(data_edge_feature, dtype = torch.long)

# Create Data instance a `torch_geometric.data.Data` object
data = Data(x=node_feature, edge_index=edge_index, edge_attr=edge_feature)

#  Data objects holds a label for each node, and additional attributes: train_mask, val_mask and test_mask:
# train_mask denotes against which nodes to train
# val_mask denotes which nodes to use for validation, e.g., to perform early stopping
# test_mask denotes against which nodes to test
data.train_mask = torch.zeros(data.num_nodes, dtype=torch.bool)
data.train_mask[:data.num_nodes - 100] = 1
data.val_mask = None
data.test_mask = torch.zeros(data.num_nodes, dtype=torch.bool)
data.test_mask[data.num_nodes - 100:] = 1


class Net(torch.nn.Module):
    def __init__(self):
        super(Net, self).__init__()
        self.conv1 = GCNConv(data.num_features, 16)
        # data.num_classes = 2
        self.conv2 = GCNConv(16, 2)

    def forward(self, x, edge_index):
        x = F.relu(self.conv1(x, edge_index))
        x = F.dropout(x, training=self.training)
        x = self.conv2(x, edge_index)
        return F.log_softmax(x, dim=1)

print(data.num_features)
print(data.num_nodes)
print(len(data.train_mask))

device = torch.device('cuda' if torch.cuda.is_available() else 'cpu')
model = Net().to(device)
data = data.to(device)
optimizer = torch.optim.Adam(model.parameters(), lr=0.01, weight_decay=5e-4)
x, edge_index = data.x, data.edge_index

for epoch in range(1, 201):
    model.train()
    optimizer.zero_grad()
    log_logits = model(x, edge_index)
    loss = F.nll_loss(log_logits[data.train_mask], data.y[data.train_mask])
    loss.backward()
    optimizer.step()

explainer = GNNExplainer(model, epochs=200)
node_idx = 10
node_feat_mask, edge_mask = explainer.explain_node(node_idx, x, edge_index)
ax, G = explainer.visualize_subgraph(node_idx, edge_index, edge_mask, y=data.y)
plt.show()