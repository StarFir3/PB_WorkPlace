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
threshold_time = 20


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

            if not G.has_edge(src,dst):
                G.add_edge(src, dst, time=row.Time, EventType=row.Event_Name, xlabel= row.Event_Name[8:])


            pid_nnv = False
            ppid_nnv = False


                      

def task_network():

    global process_count
    global list_node
    tmp_pid_in_src = False


    # To remove duplicates version nodes we created a variable to match the value with the previous stage
    pre_event = None
    pre_ip = None
    pre_pid = None
    
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
            evnt = row.Event_Name

            # If previous row and current row are the same, ignore it
            if pre_pid == src_pid and pre_ip == dst_addr and pre_event == evnt:
                pass
            else:

                # Check the direction we need if send (src = pid, dst = ip), if receive ( src = ip, dst - pid)
                if row.Event_Name == 'TcpIp/Send':
                # If TcpIp/Send, the edge should be PID to Dst_Addr
                    tmp_pid_in_src = True
                elif row.Event_Name == 'TcpIp/Recv':
                # If TcpIp/Receive, the edge should be Dst_Addr to PID
                    tmp_ip_in_src = True

                # There's a edge coming out of PID, we don't need to create version of PID
                if tmp_pid_in_src == True:
                    src_upid = str(src_pid) + "_" + str(process_count[src_pid]- 1)
                else:
                    # Create the Source Node (Process)
                    src_upid = str(src_pid) + "_" + str(process_count[src_pid]) 
                    

                if tmp_ip_in_src == True:
                    # Creating the IP node, if this IP is the first IP node in the graph
                    if process_count[dst_addr] == 0:
                        dst_uaddr = dst_addr +  "_" + str(process_count[dst_addr]) 
                    else:
                        dst_uaddr = dst_addr +  "_" + str(process_count[dst_addr] - 1) 
                else:
                    dst_uaddr = dst_addr +  "_" + str(process_count[dst_addr]) 

            
                # Set the direction right
                if tmp_pid_in_src:
                    src = src_upid
                    dst = dst_uaddr
                else:
                    src = dst_uaddr
                    dst = src_upid                 

                if not G.has_node(src_upid):
                    G.add_node(src_upid, shape='box')
                    process_count[src_pid] += 1

                if not G.has_node(dst_uaddr):
                    G.add_node(dst_uaddr, shape='diamond')
                    process_count[dst_addr] += 1 

            # Add the Edge
                if not (G.has_edge(src,dst) or G.has_edge(dst,src)):
                    G.add_edge(src, dst, key= row.Event_Name, time=row.Time, EventType=row.Event_Name, xlabel= row.Event_Name[6:]) 
                tmp_ip_in_src = False
                tmp_pid_in_src = False

            #update the current values to match the value with the prvious one
            pre_ip = row.Dst_Addr
            pre_pid = row.PID
            pre_event = row.Event_Name

def task_fileio():

    global process_count
    global list_node
    global threshold_time
    tmp_pid_in_src = False
    tmp_file_in_src = False

    dic_time = {}

    insert_row = False

    """Start with parsing fileio"""
    df = pd.read_csv(r'csv_files/FileIO.csv',  header = 0)
    # Reversing the CSV
    df = df.iloc[::-1]  

    # Creating counter for filepath
    u_filepath = list(df.File_Path.unique())    
    for row in u_filepath:
        process_count.update({row:1}) 

    u_pid = list(df.PID.unique())    
    for row in u_pid:
        if not row in process_count:
            process_count.update({row:1})

    # Process other rows
    for row in df.itertuples(index=False):
        # If relevant
        if row.PID in list_node or row.File_Path in list_node:
            src_pid = row.PID
            dst_filepath = row.File_Path
            evnt = row.Event_Name
            time = row.Time       

            file_event = str(dst_filepath) + '_' + str(evnt)
            if not file_event in dic_time.keys():
                dic_time.update({file_event:time})
                insert_row = True
            else:
                threshhold = time - dic_time[file_event]
                if threshhold > threshold_time:
                    insert_row = True
            
            if insert_row:
            
                if row.Event_Name == 'FileIO/Write':
                    tmp_pid_in_src = True
                elif row.Event_Name == 'FileIO/Read':
                    tmp_file_in_src = True
                elif row.Event_Name == 'FileIO/Delete':
                    tmp_pid_in_src = True
                elif row.Event_Name == 'FileIO/Create':
                    tmp_pid_in_src = True

                # There's a edge coming out of PID, we don't need to create version of PID
                if tmp_pid_in_src == True:
                    if process_count[src_pid] == 0:
                        src_upid = str(src_pid)
                    else:    
                        src_upid = str(src_pid) + "_" + str(process_count[src_pid] - 1)
                else:
                    # Create the Source Node (Process)
                    src_upid = str(src_pid) + "_" + str(process_count[src_pid]) 


                if tmp_file_in_src == True:
                    if process_count[dst_filepath] == 0:
                        dst_ufilepath = str(dst_filepath) +  "_" + str(process_count[dst_filepath])
                    else:
                        dst_ufilepath = str(dst_filepath) +  "_" + str(process_count[dst_filepath] - 1)
                else:
                    dst_ufilepath = str(dst_filepath) +  "_" + str(process_count[dst_filepath]) 
            
                if tmp_pid_in_src:
                    src = src_upid
                    dst = dst_ufilepath
                else:
                    src = dst_ufilepath
                    dst = src_upid 

                if not G.has_node(dst_ufilepath):
                    G.add_node(dst_ufilepath)
                    process_count[dst_filepath] += 1 

                if G.has_node(src_upid):
                    G.add_node(src_upid, shape='box')
                    process_count[src_pid] += 1   

                # Add the Edge
                if not (G.has_edge(src,dst) or G.has_edge(dst,src)):
                    G.add_edge(src, dst, key= row.Event_Name, time=row.Time, EventType=row.Event_Name, xlabel= row.Event_Name[7:]) 
                tmp_file_in_src = False
                tmp_pid_in_src = False 

    

            #update the current values to match the value with the prvious one
            dst_filepath = row.File_Path
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
#    task_network()
#    task_fileio()
    dottedline()
        #for items, rows in df.iterrows():
    # a = dict(zip(list(df.PID), list(df.Process_Name)))
    # mapping.update(a)
    #print(mapping)
    H = nx.relabel_nodes(G, mapping, copy=True)
    nx.nx_agraph.write_dot(H, "output/hello2.dot")
    nx.nx_agraph.pygraphviz_layout(H)