import networkx as nx
from networkx.algorithms.traversal.depth_first_search import dfs_edges
from numpy.lib.utils import source
import pandas as pd
import matplotlib.pyplot as plt
import networkx
import pylab
from networkx.drawing.nx_agraph import graphviz_layout
import pygraphviz as pyg
options = {
    "font_size": 8,
    "node_size": 2000,
    "node_color": "white",
    "edgecolors": "black",
    'edge_color':'black',
    "linewidths": 1,
    "width": 2,
}

G = nx.MultiDiGraph()
mapping = {}

def task_process():
    """Start with parsing processes"""
    df = pd.read_csv(r'csv_files/Process.csv',  header = 0)
    # Reversing the CSV
    df = df.iloc[::-1]    

    # Process first row to get the objects
    row = df.iloc[0]
    src = row["Process_Id"]
    dst = row["Parent_Id"]

    # If parent_id and process_id node doesn't exists create it
    if not G.has_node(src):
        G.add_node(src, FilePath = row["File_Path"], Time = row["Time"] )
    if not G.has_node(dst):
        G.add_node(dst)
    
    if G.has_node(src) and G.has_node(dst):
        if row['Event_Name'] == 'Process/Start':
            # If Process_Start, the edge should be Parent_Id to Process_Id
            src = row["Parent_Id"]
            dst = row["Process_Id"]
        elif row['Event_Name'] == 'Process/Stop':
            # If Process_Stop, the edge should be Process_Id to Parent_Id
            src = row["Process_Id"]
            dst = row["Parent_Id"]

        if not G.has_edge(src,dst):
            G.add_edge(src, dst, time=row["Time"], EventType=row["Event_Name"], xlabel= row["Event_Name"][8:])

    # Process other rows
    for row in df.itertuples(index=False):
        #uniq_process_name = row.Process_Id + row.exe
        # If process_id node doesn't exists create it
        if G.has_node(row.Process_Id) or G.has_node(row.Parent_Id):
            G.add_node(row.Process_Id, FilePath = row.File_Path, Time = row.Time)
            G.add_node(row.Parent_Id, Time = row.Time )

            if row.Event_Name == 'Process/Start':
                # If Process_Start, the edge should be Parent_Id to Process_Id
                src = row.Parent_Id
                dst = row.Process_Id
            elif row.Event_Name == 'Process/Stop':
                # If Process_Stop, the edge should be Process_Id to Parent_Id
                src = row.Process_Id
                dst = row.Parent_Id

            if not G.has_edge(src,dst):
                G.add_edge(src, dst, time=row.Time, EventType=row.Event_Name, xlabel= row.Event_Name[8:]) 
      
    #for items, rows in df.iterrows():
    a = dict(zip(list(df.Process_Id), list(df.Process_Name)))
    mapping.update(a)
    #print(mapping)
    

def task_network():
    df = pd.read_csv(r'csv_files/Network.csv',  header = 0)
    # Reversing the CSV
    df = df.iloc[::-1]
    process_id = 0
       

    # Process other rows
    for row in df.itertuples(index=False):

        #for key,value in mapping.items():
        for key, value in mapping.items():
            if value == row.Process_Name:
                process_id = key

        #uniq_process_name = row.Process_Id + row.exe
        # If process_id node doesn't exists create it
        if G.has_node(process_id) or G.has_node(row.Dst_Addr):
            G.add_node(process_id, Time = row.Time )
            G.add_node(row.Dst_Addr, shape='diamond')

            if row.Event_Name == 'TcpIp/Send':
            # If TcpIp/Send, the edge should be Src_Addr to Dst_Addr
                src = process_id
                dst = row.Dst_Addr
            elif row.Event_Name == 'TcpIp/Recv':
                # If Process_Stop, the edge should be Process_Id to Parent_Id
                src = row.Dst_Addr
                dst = process_id


            if not G.has_edge(src,dst):
                G.add_edge(src, dst, time=row.Time, EventType=row.Event_Name, xlabel= row.Event_Name[6:]) 
    


def task_fileio():
    """Start with parsing fileio"""
    df = pd.read_csv(r'csv_files/FileIO.csv')
    # Reversing the CSV
    df = df.iloc[::-1]  
    process_id = 0     

    # Process other rows
    for row in df.itertuples(index=False):
        #print(row.Process_Name)

        #for key,value in mapping.items():
        for key, value in mapping.items():
            #print(key,value)
            if value == row.Process_Name:
                process_id = key
            #print(process_id)

        if process_id != 0:           

            if G.has_node(process_id) or G.has_node(row.File_Path):
                G.add_node(process_id, Time = row.Time, shape='box')
                G.add_node(row.File_Path, shape='ellipse')

                if row.Event_Name == 'FileIO/Write':
                    # If Process_Start, the edge should be Parent_Id to Process_Id
                    src = process_id
                    dst = row.File_Path
                elif row.Event_Name == 'FileIO/Read':
                    # If Process_Stop, the edge should be Process_Id to Parent_Id
                    src = row.File_Path
                    dst = process_id
                elif row.Event_Name == 'FileIO/Delete':
                    # If Process_Stop, the edge should be Process_Id to Parent_Id
                    src = process_id
                    dst = row.File_Path
                elif row.Event_Name == 'FileIO/Create':
                    # If Process_Stop, the edge should be Process_Id to Parent_Id
                    src = process_id
                    dst = row.File_Path

                if not G.has_edge(src,dst):
                    G.add_edge(src, dst, time=row.Time, EventType=row.Event_Name, xlabel= row.Event_Name[7:]) 
        


if __name__ == "__main__":
    task_process()
    task_network()
    task_fileio()
    H = nx.relabel_nodes(G, mapping, copy=True)
    nx.nx_agraph.write_dot(H, "output/hello.dot")
    nx.nx_agraph.pygraphviz_layout(H)