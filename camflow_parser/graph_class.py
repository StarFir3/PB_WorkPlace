import tarfile,glob,os,shutil
import prepare
import argparse
import os.path as osp
import torch
from torch_geometric.data import Dataset
from torch_geometric.data import Data, DataLoader
import networkx as nx
from numpy import genfromtxt
#from graphlime import GraphLIME
from torch_geometric.nn import GCNConv
from torch.nn import Linear
import torch.nn.functional as F
import matplotlib.pyplot as plt
from torch_geometric.datasets import Planetoid
import torch_geometric.transforms as T
from torch_geometric.nn import GCNConv, GNNExplainer
from torch_geometric.utils.convert import to_networkx

from torch_geometric.nn import global_mean_pool


# make argparse arguments global
CONSOLE_ARGUMENTS = None


TAR_LOCATION = "/home/priyanka/PB_WorkPlace/prov_data_tar"
TAR_EXTRACTION_LOCATION = "/home/priyanka/PB_WorkPlace/prov_data_main"
CSV_FILES = "/home/priyanka/PB_WorkPlace/prov_data_csv"
train_dataset = None
test_dataset = None

class GCN(torch.nn.Module):
    def __init__(self, hidden_channels):
        super(GCN, self).__init__()
        torch.manual_seed(12345)
        self.conv1 = GCNConv(graph_dataset.num_node_features, hidden_channels)
        self.conv2 = GCNConv(hidden_channels, hidden_channels)
        self.conv3 = GCNConv(hidden_channels, hidden_channels)
        num_classes = 2
        self.lin = Linear(hidden_channels, num_classes)

    def forward(self, x, edge_index, batch):
        # 1. Obtain node embeddings
        print(edge_index)
        print(edge_index.shape)
        x = self.conv1(x, edge_index)
        x = x.relu()
        x = self.conv2(x, edge_index)
        x = x.relu()
        x = self.conv3(x, edge_index)

        # 2. Readout layer
        x = global_mean_pool(x, batch)  # [batch_size, hidden_channels]

        # 3. Apply a final classifier
        x = F.dropout(x, p=0.5, training=self.training)
        x = self.lin(x)

        return x


class MyOwnDataset(Dataset):
    def __init__(self, root, transform=None, pre_transform=None):
        super(MyOwnDataset, self).__init__(root, transform, pre_transform)

    @property
    def raw_file_names(self):
        return ['some_file_1', 'some_file_2']

    @property
    def processed_file_names(self):
        processed_file = os.listdir("Hello/processed/")
#        return ["Hello.pt"]
        return processed_file
#        return None

    def download(self):
        # Download to `self.raw_dir`.
        print("Helo")

    def process(self):
        i = 0
        # Read all the folders in the TAR_LOCATION
        for path, directories, files in os.walk(TAR_LOCATION):
            # Read all the files ending with .tar.gz in TAR_LOCATION
            for f in files:
                if f.endswith(".tar.gz"):
                    tar_file_name = f.rstrip(".tar.gz")

                    file_name = TAR_LOCATION + "/" + f
                    ext_path = TAR_EXTRACTION_LOCATION + "/" + tar_file_name
                    # Check if folder exits in TAR_EXTRACTION_LOCATION, if not, extract
                    if not os.path.exists(ext_path):
                        tar = tarfile.open(file_name, 'r:gz')
                        tar.extractall(path=TAR_EXTRACTION_LOCATION)
                        tar.close()
                

                    trace_file = TAR_EXTRACTION_LOCATION + "/" + tar_file_name + "/camflow/output/trace.data" 
                    csv_folder = CSV_FILES + "/" + tar_file_name
                    if not os.path.exists(csv_folder):
                        os.mkdir(csv_folder)
                    # Process trace.data by calling prepare module which process the trace.data and generates
                    # edge_index.csv, node_feature_x.csv and edge_attr.csv
                    prepare.process_file(trace_file, csv_folder, CONSOLE_ARGUMENTS) 

                    # Create Edge Index by reading edge_index.csv
                    filename_edge_index = csv_folder + "/" + 'edge_index.csv'
                    data_edge_index = genfromtxt(filename_edge_index, delimiter=',')
                    edge_index = torch.tensor(data_edge_index, dtype = torch.long)
                    print(edge_index.shape)

                    # Create Node Feature by reading node_feature_x.csv
                    filename_node_feature = csv_folder + "/" + 'node_feature_x.csv'
                    data_node_feature = genfromtxt(filename_node_feature, delimiter=',', skip_header = 1)
                    node_feature = torch.tensor(data_node_feature, dtype = torch.float)
                    print(node_feature.shape)

                    # Create Edge Feature by reading edge_attr.csv
                    filename_edge_feature = csv_folder + "/" + 'edge_attr.csv'
                    data_edge_feature = genfromtxt(filename_edge_feature, delimiter=',', skip_header = 1)
                    edge_feature = torch.tensor(data_edge_feature, dtype = torch.long)

                    # Classify graph based on Malicious/ Not Malicious
                    if tar_file_name.startswith("attack_"):
                        y = torch.tensor([True], dtype= torch.long)
                    elif tar_file_name.startswith("normal_"):
                        y = torch.tensor([False], dtype= torch.long)


                    # Create Data instance a `torch_geometric.data.Data` object
                    data = None
                    data = Data(x=node_feature, edge_index=edge_index, edge_attr=edge_feature, y=y)

                    #delete CSV files
                    if os.path.exists(ext_path):
                        shutil.rmtree(ext_path)

                    if os.path.exists(csv_folder):
                        shutil.rmtree(csv_folder)

                    print("Csv files and extracted folder deleted ")

                # for raw_path in self.raw_paths:
                #     # Read data from `raw_path`.
                #     data = Data(...)

                    if self.pre_filter is not None and not self.pre_filter(data):
                        continue

                    if self.pre_transform is not None:
                        data = self.pre_transform(data)

                    torch.save(data, osp.join(self.processed_dir, 'data_{}.pt'.format(i)))
                    i += 1

    def len(self):
        return len(self.processed_file_names)

    def get(self, idx):
        data = torch.load(osp.join(self.processed_dir, 'data_{}.pt'.format(idx)))
        return data

# Start of python script

def train():
    global train_dataset
    # Defining the batch size to 1? As graphs are quite big and batching is not required?
    model.train()

    for data in train_dataset:  # Iterate in batches over the training dataset.
        out = model(data.x, data.edge_index, data.batch)  # Perform a single forward pass.
        loss = criterion(out, data.y)  # Compute the loss.
        loss.backward()  # Derive gradients.
        optimizer.step()  # Update parameters based on gradients.
        optimizer.zero_grad()  # Clear gradients.

def test(loader):
     model.eval()

     correct = 0
     for data in loader:  # Iterate in batches over the training/test dataset.
        out = model(data.x, data.edge_index, data.batch)  
        pred = out.argmax(dim=1)  # Use the class with highest probability.
        correct += int((pred == data.y).sum())  # Check against ground-truth labels.
     return correct / len(loader.dataset)  # Derive ratio of correct predictions.

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Convert CamFlow JSON to Unicorn edgelist')
    parser.add_argument('-v', '--verbose', help='verbose logging (default is false)', action='store_true')
    parser.add_argument('-l', '--log', help='log file path (only valid is -v is set; default is debug.log)', default='debug.log')
    parser.add_argument('-s', '--stats', help='record some statistics of the CamFlow graph data and runtime graph generation speed (default is false)', action='store_true')
    parser.add_argument('-f', '--stats-file', help='file path to record the statistics (only valid if -s is set; default is stats.csv)', default='stats.csv')
    parser.add_argument('-n', '--noencode', help='do not encode UUID in output (default is to encode)', action='store_true')

    args = parser.parse_args()
    
    CONSOLE_ARGUMENTS = args
    
    graph_dataset = MyOwnDataset("Hello", transform=None, pre_transform=None)
    print("Length of the dataset is " + str(graph_dataset.len()))
    graph_dataset = graph_dataset.shuffle()
    train_dataset = graph_dataset[:100]
    test_dataset = graph_dataset[100:]
    
    torch.manual_seed(12345)
    
    train_loader = DataLoader(train_dataset, batch_size=1, shuffle=True)
    test_loader = DataLoader(test_dataset, batch_size=1, shuffle=False)

    #print(f'Number of training graphs: {len(train_dataset)}')
    #print(f'Number of test graphs: {len(test_dataset)}')


    model = GCN(hidden_channels=64)
    print(model)
    optimizer = torch.optim.Adam(model.parameters(), lr=0.01)
    criterion = torch.nn.CrossEntropyLoss()

    for epoch in range(1, 201):
        train()
        train_acc = test(train_loader)
        test_acc = test(test_loader)
        print(f'Epoch: {epoch:03d}, Train Acc: {train_acc:.4f}, Test Acc: {test_acc:.4f}')




