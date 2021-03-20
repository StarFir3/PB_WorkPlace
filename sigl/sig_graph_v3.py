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
# Setting Threshold to 5 seconds
threshold_time = 10000
dict_time = {}


def task_process():
    """Start with parsing processes"""

    # list_node stores the relevant nodes to the graph
    global list_node
    pid_nv = False
    ppid_nv = False    

    df = pd.read_csv(r'csv_files/Process.csv',  header = 0)

    #creating a dictonary with key:Process_Name and value: Counter (initial value 0). Use it to create acyclic graph 
    u_pid = list(df.PID.unique())    
    for item in u_pid:
        process_count.update({item:0})

    # Process first row to get the objects
    row = df.iloc[0]

    # Start with the source
    pid = row["PID"]
    ppid = int(row["Parent_Id"].replace(",",""))
    process_count.update({ppid:0})

    if row['Event_Name'] == 'Process/Start':
        # If Process_Start, the edge should be Parent_Id to Process_Id
        pid_nv = True
        ppid_nv = False
    elif row['Event_Name'] == 'Process/Stop':
        # If Process_Stop, the edge should be Process_Id to Parent_Id
        pid_nv = False
        ppid_nv = True

    # 
    if pid_nv == True:
        u_pid = str(pid) + "_" + str(process_count[pid])
    else:
        if process_count[pid] == 0:
            u_pid = str(pid) + "_" + str(process_count[pid])
        else:    
            u_pid = str(pid) + "_" + str(process_count[pid] - 1)

    if ppid_nv == True:
        u_ppid = str(ppid) + "_" + str(process_count[ppid])
    else:
        if process_count[ppid] == 0:
            u_ppid = str(ppid) + "_" + str(process_count[ppid])
        else:
            u_ppid = str(ppid) + "_" + str(process_count[ppid] - 1)


    if row['Event_Name'] == 'Process/Start':
        # If Process_Start, the edge should be Parent_Id to Process_Id
        src = u_ppid
        dst = u_pid
        id_src = ppid
        id_dst = pid     
    elif row['Event_Name'] == 'Process/Stop':
        # If Process_Stop, the edge should be Process_Id to Parent_Id
        src = u_pid
        dst = u_ppid
        id_src = pid
        id_dst = ppid

    # Providing unique name  
    #u_dst = str(ppid) + "_" + str(process_count[ppid])
             
            
    if not G.has_node(src):
        G.add_node(src,shape='box', FilePath = row["File_Path"], Time = row["Time"]  )
        process_count[id_src] += 1
        list_node.append(id_src)

    if not G.has_node(dst):
        process_count[id_dst] += 1
        G.add_node(dst, shape='box')        
        list_node.append(id_dst)


    if not G.has_edge(src,dst):
        G.add_edge(src, dst, time=row["Time"], EventType=row["Event_Name"], xlabel= row["Event_Name"][8:])

    # Process other rows

    # Itertuples Refer https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.itertuples.html
    # Refer https://stackoverflow.com/questions/38596056/how-to-change-the-starting-index-of-iterrows/38596799
    # Skipping first row as already processed
    for row in islice(df.itertuples(index=False), 1, None):
        pid = row.PID
        ppid = int(row.Parent_Id.replace(",",""))

    #   # Ensuring that current row is relevant
        if pid in list_node or ppid in list_node:


            if row.Event_Name == 'Process/Start':
                # If Process_Start, the edge should be Parent_Id to Process_Id
                pid_nv = True
                ppid_nv = False
            elif row.Event_Name == 'Process/Stop':
                # If Process_Stop, the edge should be Process_Id to Parent_Id
                pid_nv = False
                ppid_nv = True

            if pid_nv == True:
                u_pid = str(pid) + "_" + str(process_count[pid])
            else:
                if process_count[pid] == 0:
                    u_pid = str(pid) + "_" + str(process_count[pid])
                else:
                    u_pid = str(pid) + "_" + str(process_count[pid] - 1)

            if ppid_nv == True:
                u_ppid = str(ppid) + "_" + str(process_count[ppid])
            else:
                if process_count[ppid] == 0:
                    u_ppid = str(ppid) + "_" + str(process_count[ppid])    
                else:
                    u_ppid = str(ppid) + "_" + str(process_count[ppid] - 1)


            if row.Event_Name == 'Process/Start':
                # If Process_Start, the edge should be Parent_Id to Process_Id
                src = u_ppid
                dst = u_pid
                id_src = ppid
                id_dst = pid
                # Adding the child process
                list_node.append(pid)
            elif row.Event_Name == 'Process/Stop':
                # If Process_Stop, the edge should be Process_Id to Parent_Id
                src = u_pid
                dst = u_ppid
                id_src = pid
                id_dst = ppid

                    
            if not G.has_node(src):
                G.add_node(src,shape='box', FilePath = row.File_Path, Time = row.Time)
                process_count[id_src] += 1

            if not G.has_node(dst):
                G.add_node(dst, shape='box')
                process_count[id_dst] += 1                

            if not G.has_edge(src,dst):
                G.add_edge(src, dst, time=row.Time, EventType=row.Event_Name, xlabel= row.Event_Name[8:])


            pid_nnv = False
            ppid_nnv = False


                      

def task_network():

    global process_count
    global list_node
    insert_row = False
    
    df = pd.read_csv(r'csv_files/Network.csv',  header = 0)

    # Creating counter for dst addr
    u_daddr = list(df.Dst_Addr.unique())    
    for row in u_daddr:
        process_count.update({row:0}) 

    # Processing each row
    for row in df.itertuples(index=False):
        pid = row.PID
        ip = row.Dst_Addr
        evnt = row.Event_Name
        time = row.Time        

        # The row is relevant is the row.PID is the list_node
        if pid in list_node or ip in list_node:

            ip_event = str(ip) + '_' + str(evnt)
            if ip_event in dict_time.keys():
                time_diff = time - dict_time[ip_event]
                if time_diff > threshold_time:
                    insert_row = True
                    dict_time.update({ip_event:time})
            else:
                insert_row = True
                dict_time.update({ip_event:time})
                

            # If previous row and current row are the same, ignore it
            if insert_row == True:

                # Check the direction we need if send (src = pid, dst = ip), if receive ( src = ip, dst - pid)
                if row.Event_Name == 'TcpIp/Send':
                # If TcpIp/Send, the edge should be PID to Dst_Addr
                    pid_nv = False
                    ip_nv = True
                elif row.Event_Name == 'TcpIp/Recv':
                # If TcpIp/Receive, the edge should be Dst_Addr to PID
                    pid_nv = True
                    ip_nv = False

                if pid_nv == True:
                    u_pid = str(pid) + "_" + str(process_count[pid])
                else:
                    if process_count[pid] == 0:
                        u_pid = str(pid) + "_" + str(process_count[pid])
                    else:
                        u_pid = str(pid) + "_" + str(process_count[pid] - 1)
                    

                if ip_nv == True:
                    u_ip = str(ip) + "_" + str(process_count[ip])
                else:
                    if process_count[ip] == 0:
                        u_ppid = str(ip) + "_" + str(process_count[ip])    
                    else:
                        u_ppid = str(ip) + "_" + str(process_count[ip] - 1)


                if row.Event_Name == 'TcpIp/Send':
                    # If Process_Start, the edge should be Parent_Id to Process_Id
                    src = u_pid
                    dst = u_ip
                    id_src = pid
                    id_dst = ip
                    shape_src = 'box'
                    shape_dst = 'diamond'

                elif row.Event_Name == 'TcpIp/Recv':
                    # If Process_Stop, the edge should be Process_Id to Parent_Id
                    src = u_ip
                    dst = u_pid
                    id_src = ip
                    id_dst = pid
                    shape_src = 'diamond'
                    shape_dst = 'box'


                if not G.has_node(src):
                    G.add_node(src, shape=shape_src)
                    process_count[id_src] += 1

                if not G.has_node(dst):
                    G.add_node(dst, shape=shape_dst)
                    process_count[id_dst] += 1 

            # Add the Edge
                if not (G.has_edge(src,dst) or G.has_edge(dst,src)):
                    G.add_edge(src, dst, key= row.Event_Name, time=row.Time, EventType=row.Event_Name, xlabel= row.Event_Name[6:]) 
                ip_nv = False
                pid_nv = False

            insert_row = False



def task_fileio():

    global process_count
    global list_node
    global threshold_time
    global dict_time

    insert_row = False

    """Start with parsing fileio"""
    df = pd.read_csv(r'csv_files/FileIO.csv',  header = 0)

    # Creating counter for filepath
    u_filepath = list(df.File_Path.unique())    
    for row in u_filepath:
        process_count.update({row:0}) 

    u_pid = list(df.PID.unique())    
    for row in u_pid:
        if not row in process_count:
            process_count.update({row:0})

    # Process other rows
    for row in df.itertuples(index=False):

        pid = row.PID
        file = row.File_Path
        evnt = row.Event_Name
        time = row.Time    
        # If relevant
        if pid in list_node or file in list_node:

            file_event = str(file) + '_' + str(evnt)
            if file_event in dict_time.keys():
                time_diff = time - dict_time[file_event]
                if time_diff > threshold_time:
                    insert_row = True
                    dict_time.update({file_event:time})
            else:
                insert_row = True
                dict_time.update({file_event:time})

            if insert_row:
            
                if row.Event_Name == 'FileIO/Write':
                    pid_nv = False
                    file_nv = True
                elif row.Event_Name == 'FileIO/Read':
                    pid_nv = True
                    file_nv = False
                elif row.Event_Name == 'FileIO/Delete':
                    pid_nv = False
                    file_nv = True
                elif row.Event_Name == 'FileIO/Create':
                    pid_nv = False
                    file_nv = True

                if pid_nv == True:
                    u_pid = str(pid) + "_" + str(process_count[pid])
                else:
                    if process_count[pid] == 0:
                        u_pid = str(pid) + "_" + str(process_count[pid])
                    else:
                        u_pid = str(pid) + "_" + str(process_count[pid] - 1)
                    

                if file_nv == True:
                    u_file = str(file) + "_" + str(process_count[file])
                else:
                    if process_count[file] == 0:
                        u_ppid = str(file) + "_" + str(process_count[file])    
                    else:
                        u_ppid = str(file) + "_" + str(process_count[file] - 1)
            
                if row.Event_Name == 'FileIO/Read':
                    # If Process_Start, the edge should be Parent_Id to Process_Id
                    src = u_file
                    dst = u_pid
                    id_src = file
                    id_dst = pid
                    shape_src = 'ellipse'
                    shape_dst = 'box'
                else:
                    # If Process_Stop, the edge should be Process_Id to Parent_Id
                    src = u_pid
                    dst = u_file
                    id_src = pid
                    id_dst = file
                    shape_src = 'box'
                    shape_dst = 'ellipse'                    

                if not G.has_node(src):
                    G.add_node(src, shape=shape_src)
                    process_count[id_src] += 1

                if not G.has_node(dst):
                    G.add_node(dst, shape=shape_dst)
                    process_count[id_dst] += 1 

            # Add the Edge
                if not (G.has_edge(src,dst) or G.has_edge(dst,src)):
                    G.add_edge(src, dst, key= row.Event_Name, time=row.Time, EventType=row.Event_Name, xlabel= row.Event_Name[7:]) 
                file_nv = False
                pid_nv = False

            insert_row = False

def dottedline():
    for key, value in process_count.items():
    
        if value > 1:
            for i in reversed(range(0,value)):
                node_x = str(key) + "_" + str(i)
                node_y = str(key) + "_" + str(i - 1)
  
                if G.has_node(node_x) and G.has_node(node_y):
                    G.add_edge(node_y, node_x, style='dotted')  
        else:
            node_x = str(key) + "_0" 
            node_y = str(key) + "_1"
            if G.has_node(node_x) and G.has_node(node_y):
                G.add_edge(node_y, node_x, style='dotted')             



if __name__ == "__main__":
    task_process()
    task_network()
    task_fileio()
    dottedline()
        #for items, rows in df.iterrows():
    # a = dict(zip(list(df.PID), list(df.Process_Name)))
    # mapping.update(a)
    #print(mapping)
    H = nx.relabel_nodes(G, mapping, copy=True)
    nx.nx_agraph.write_dot(H, "output/hello2.dot")
    nx.nx_agraph.pygraphviz_layout(H)