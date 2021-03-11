from os import replace
import networkx as nx
from networkx.algorithms.traversal.depth_first_search import dfs_edges
from numpy.lib.utils import source
import pandas as pd
import matplotlib.pyplot as plt
import networkx
import pylab
from networkx.drawing.nx_agraph import graphviz_layout
import pygraphviz as pyg
from itertools import islice
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
process_count = {}
list_node = []


def task_process():
    """Start with parsing processes"""
    global list_node
    t_1234 = False
    t_1234_P_X = False
    df = pd.read_csv(r'csv_files/Process.csv',  header = 0)
    # Reversing the CSV as we start from the last log.
    df = df.iloc[::-1]

    #creating a dictonary with key:Process_Name and value: Counter (initial value 0). Use it to create acyclic graph 
    u_pid = list(df.PID.unique())    
    for row in u_pid:
        process_count.update({row:0})
        #print(process_count)

    # Process first row to get the objects
    row = df.iloc[0]

    # Start with the source
    src_pid = row["PID"]
    # Providing unique name  
    src_upid = str(src_pid) + "_" + str(process_count[src_pid])
    # If parent_id and process_id node doesn't exists create it
    if not G.has_node(src_upid):
        G.add_node(src_upid,shape='box', FilePath = row["File_Path"], Time = row["Time"]  )
        process_count[src_pid] += 1
        list_node.append(row["PID"])

    dst = int(row["Parent_Id"].replace(",",""))
    if not G.has_node(dst):
        list_node.append(dst)
        G.add_node(dst, shape='box')

    if G.has_node(src_upid) and G.has_node(dst):
        if row['Event_Name'] == 'Process/Start':
            # If Process_Start, the edge should be Parent_Id to Process_Id
            src = dst
            dst = src_upid
        elif row['Event_Name'] == 'Process/Stop':
            # If Process_Stop, the edge should be Process_Id to Parent_Id
            src = src_upid
            dst = dst

        if not G.has_edge(src,dst):
            G.add_edge(src, dst, time=row["Time"], EventType=row["Event_Name"], xlabel= row["Event_Name"][8:])

    # Process other rows

    # Itertuples Refer https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.itertuples.html
    # Refer https://stackoverflow.com/questions/38596056/how-to-change-the-starting-index-of-iterrows/38596799
    # Skipping first row as already processed
    for row in islice(df.itertuples(index=False), 1, None):

        # Ensuring that current row is relevant
        Parent_Id = int(row.Parent_Id.replace(",",""))
        if row.PID in list_node or Parent_Id in list_node:

        # If process_id node doesn't exists create it
            src_pid = row.PID 
            src_upid = str(src_pid) + "_" + str(process_count[src_pid])

            if not G.has_node(src_upid):
                G.add_node(src_upid,shape='box', FilePath = row.File_Path, Time = row.Time)
                process_count[src_pid] += 1
            # Now, the parent can exists either with 1234 or 1234_P_X
            if G.has_node(Parent_Id):
                t_1234 = True
                dst_upid = Parent_Id
            else:
            # Creating 1234_P_X
                temp = str(Parent_Id) + "_" + str(process_count[Parent_Id] - 1)
                if G.has_node(temp):
                    t_1234_P_X = True
                    dst_upid = temp
            
            # The node exists as either of them
            if t_1234 or t_1234_P_X:
                pass
            else:
                G.add_node(temp,shape='box', Time = row.Time )  
                   

            if row.Event_Name == 'Process/Start':
                # If Process_Start, the edge should be Parent_Id to Process_Id
                src = dst_upid
                dst = src_upid
            elif row.Event_Name == 'Process/Stop':
                # If Process_Stop, the edge should be Process_Id to Parent_Id
                src = src_upid
                dst = dst_upid

            if not G.has_edge(src,dst):
                G.add_edge(src, dst, time=row.Time, EventType=row.Event_Name, xlabel= row.Event_Name[8:]) 
                      
    #for items, rows in df.iterrows():
    a = dict(zip(list(df.PID), list(df.Process_Name)))
    mapping.update(a)
    #print(mapping)

def task_network():

    # Boolean variables to store process variant and network variant
    # p_1234 = False
    # p_1234_P_X = False
    # n_1234 = False
    # n_1234_N_X = False

    global list_node
    tmp_pid_in_src = False
    global process_count

    df = pd.read_csv(r'csv_files/Network.csv',  header = 0)
    # Reversing the CSV
    df = df.iloc[::-1]

    # Creating counter for dst addr
    u_daddr = list(df.Dst_Addr.unique())    
    for row in u_daddr:
        process_count.update({row:0}) 

    # Processing each row
    for row in df.itertuples(index=False):

        # The row is relevant is the row.PID is the list_node
        if row.PID in list_node or row.Dst_Addr in list_node:
            src_pid = row.PID
            dst_addr = row.Dst_Addr

            # Create the Source Node (Process)    
            src_upid = str(src_pid) + "_" + str(process_count[src_pid])
            if not G.has_node(src_upid):
                G.add_node(src_upid, shape='box')
                process_count[src_pid] += 1

            # Create the Destination Node (Socket)
            dst_uaddr = dst_addr +  "_" + str(process_count[dst_addr])
            if not G.has_node(dst_uaddr):
                G.add_node(dst_uaddr, shape='diamond')
                process_count[dst_addr] += 1

            # Check the direction
            if row.Event_Name == 'TcpIp/Send':
            # If TcpIp/Send, the edge should be Src_Addr to Dst_Addr
                src = src_upid
                dst = dst_uaddr
                tmp_pid_in_src = True
            elif row.Event_Name == 'TcpIp/Recv':
                # If Process_Stop, the edge should be Process_Id to Parent_Id
                src = dst_uaddr
                dst = src_upid
                tmp_pid_in_src = False         

            # Add the Edge
            if not (G.has_edge(src,dst) or G.has_edge(dst,src)):
                G.add_edge(src, dst, key= row.Event_Name, time=row.Time, EventType=row.Event_Name, xlabel= row.Event_Name[6:]) 

            # Probably the below is not required    
            else:
                tmp = str(row.PID) + "_" + str(process_count[row.PID])
                G.add_node(tmp,shape='box', Time = row.Time)
                process_count[row.PID] += 1
                if tmp_pid_in_src:
                    src = tmp
                else:
                    dst = tmp
                G.add_edge(src, dst, key= row.Event_Name, time=row.Time, EventType=row.Event_Name, xlabel= row.Event_Name[6:])

    #program to connect the version nodes with dotted line, by using dictionary
    for key, value in process_count.items():
        #print(key,value)
        if value > 1:
            for i in reversed(range(0,value)):
                node_x = str(key) + "_" + str(i)
                node_y = str(key) + "_" + str(i - 1)
                # print(node_x)
                # print(node_y)
        
                if G.has_node(node_x) and G.has_node(node_y):
                    G.add_edge(node_y, node_x, style='dotted')

def task_fileio():
    """Start with parsing fileio"""
    df = pd.read_csv(r'csv_files/FileIO.csv',  header = 0)
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
    nx.nx_agraph.write_dot(H, "output/hello2.dot")
    nx.nx_agraph.pygraphviz_layout(H)