import tarfile,glob,os
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
# make argparse arguments global
CONSOLE_ARGUMENTS = None


TAR_LOCATION = "/home/priyanka/PB_WorkPlace/prov_data_tar"
TAR_EXTRACTION_LOCATION = "/home/priyanka/PB_WorkPlace/prov_data_main"
CSV_FILES = "/home/priyanka/PB_WorkPlace/prov_data_csv"

class MyOwnDataset(Dataset):
    def __init__(self, root, transform=None, pre_transform=None):
        super(MyOwnDataset, self).__init__(root, transform, pre_transform)

    @property
    def raw_file_names(self):
        return ['some_file_1', 'some_file_2']

    @property
    def processed_file_names(self):
        return ['data_0.pt', 'data_1.pt']
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
                    # Check if folder exits in TAR_EXTRACTION_LOCATION, if not, extract
                    if not os.path.exists(TAR_EXTRACTION_LOCATION + "/" + tar_file_name):
                        tar = tarfile.open(file_name, 'r:gz')
                        tar.extractall(path=TAR_EXTRACTION_LOCATION)
                        tar.close()
                

                    trace_file = TAR_EXTRACTION_LOCATION + "/" + tar_file_name + "/camflow/output/trace.data" 
                    csv_folder = CSV_FILES + "/" + tar_file_name
                    if not os.path.exists(csv_folder):
                        os.mkdir(csv_folder)
                    # Process trace.data
                    prepare.process_file(trace_file, csv_folder, CONSOLE_ARGUMENTS) 

                    # Create Edge Index
                    filename_edge_index = csv_folder + "/" + 'edge_index.csv'
                    data_edge_index = genfromtxt(filename_edge_index, delimiter=',')
                    edge_index = torch.tensor(data_edge_index, dtype = torch.long)

                    # Create Node Feature
                    filename_node_feature = csv_folder + "/" + 'node_feature_x.csv'
                    data_node_feature = genfromtxt(filename_node_feature, delimiter=',')
                    node_feature = torch.tensor(data_node_feature, dtype = torch.float)

                    # Create Edge Feature
                    filename_edge_feature = csv_folder + "/" + 'edge_attr.csv'
                    data_edge_feature = genfromtxt(filename_edge_feature, delimiter=',')
                    edge_feature = torch.tensor(data_edge_feature, dtype = torch.long)

                    # Classify graph based on Malicious/ Not Malicious
                    if tar_file_name.startswith("attack_"):
                        y = torch.tensor([True], dtype= torch.long)
                    elif tar_file_name.startswith("normal_"):
                        y = torch.tensor([False], dtype= torch.long)


                    # Create Data instance a `torch_geometric.data.Data` object
                    data = Data(x=node_feature, edge_index=edge_index, edge_attr=edge_feature, y=y)

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
    dataset = DataLoader(graph_dataset)
    print(graph_dataset.len())
    data = graph_dataset.get(0)
    #print(data.num_features)
    #print(dataset.num_classes)



