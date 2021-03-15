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

    global list_node
    tmp_pid_in_src = False
    global process_count

    # To remove duplicates version nodes we created a variable to match the value with the previous stage
    pre_event = None
    pre_ip = None
    pre_pid = None

    
    second_row_pid = False
    second_row_ip = False

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
                # If TcpIp/Send, the edge should be Src_Addr to Dst_Addr
                    # src = src_pid
                    # dst = dst_addr
                    tmp_pid_in_src = True
                elif row.Event_Name == 'TcpIp/Recv':
                    # If Process_Stop, the edge should be Process_Id to Parent_Id
                    # src = dst_uaddr
                    # dst = src_upid
                    tmp_ip_in_src = True

                # There's a edge coming out of PID, we don't need to create version of PID
                if tmp_pid_in_src == True:
                    src_upid = str(src_pid) + "_" + str(process_count[src_pid]- 1)
                else:
                    # Create the Source Node (Process)
                    src_upid = str(src_pid) + "_" + str(process_count[src_pid]) 
                    second_row_pid = False  
                    
                    if not G.has_node(src_upid):
                        G.add_node(src_upid, shape='box')
                        process_count[src_pid] += 1                      

                if tmp_ip_in_src == True:
                    if process_count[dst_addr] == 0:
                        dst_uaddr = dst_addr +  "_" + str(process_count[dst_addr]) 
                        if not G.has_node(dst_uaddr):
                            G.add_node(dst_uaddr, shape='diamond')
                            process_count[dst_addr] += 1 
                    else:
                        dst_uaddr = dst_addr +  "_" + str(process_count[dst_addr] - 1) 
                else:
                    dst_uaddr = dst_addr +  "_" + str(process_count[dst_addr]) 
                    second_row_ip = False  
            
                    if not G.has_node(dst_uaddr):
                        G.add_node(dst_uaddr, shape='diamond')
                        process_count[dst_addr] += 1   

                if tmp_pid_in_src:
                    src = src_upid
                    dst = dst_uaddr
                else:
                    src = dst_uaddr
                    dst = src_upid                 
                
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

    tmp_pid_in_src = False
    tmp_file_in_src = False
    global process_count
    global list_node

    # To remove duplicates version nodes we created a variable to match the value with the previous stage
    pre_event = None
    dst_filepath = None
    pre_pid = None

    """Start with parsing fileio"""
    df = pd.read_csv(r'csv_files/FileIO2.csv',  header = 0)
    # Reversing the CSV
    df = df.iloc[::-1]  
    process_id = 0   

    # Creating counter for filepath
    u_filepath = list(df.File_Path.unique())    
    for row in u_filepath:
        process_count.update({row:0}) 

    u_pid = list(df.PID.unique())    
    for row in u_pid:
        if not row in process_count:
            process_count.update({row:0})
        #print(process_count)

    


    # Process other rows
    for row in df.itertuples(index=False):
        if row.PID in list_node or row.File_Path in list_node:
            src_pid = row.PID
            dst_filepath = row.File_Path
            evnt = row.Event_Name

            if pre_pid == src_pid and dst_filepath == dst_filepath and pre_event == evnt:
                pass
            else:
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
                    second_row_pid = False

                    if G.has_node(src_upid):
                        G.add_node(src_upid, shape='box')
                        process_count[src_pid] += 1   

                if tmp_file_in_src == True:
                    if process_count[dst_filepath] == 0:
                        dst_ufilepath = str(dst_filepath) +  "_" + str(process_count[dst_filepath]) 
                        if not G.has_node(dst_ufilepath):
                            G.add_node(dst_ufilepath)
                            process_count[dst_filepath] += 1 
                else:
                    dst_ufilepath = str(dst_filepath) +  "_" + str(process_count[dst_filepath] - 1) 
                    second_row_ip = False  
            
                    if not G.has_node(dst_ufilepath):
                        G.add_node(dst_ufilepath)
                        process_count[dst_filepath] += 1   

                if tmp_pid_in_src:
                    src = src_upid
                    dst = dst_ufilepath
                else:
                    src = dst_ufilepath
                    dst = src_upid 

                # Add the Edge
                if not (G.has_edge(src,dst) or G.has_edge(dst,src)):
                    G.add_edge(src, dst, key= row.Event_Name, time=row.Time, EventType=row.Event_Name, xlabel= row.Event_Name[7:]) 
                tmp_file_in_src = False
                tmp_pid_in_src = False 

    

            #update the current values to match the value with the prvious one
            dst_filepath = row.File_Path
            pre_pid = row.PID
            pre_event = row.Event_Name    

def dottedline():
    for key, value in process_count.items():
    
        if value > 1:
            for i in reversed(range(0,value)):
                node_x = str(key) + "_" + str(i)
                node_y = str(key) + "_" + str(i - 1)
  
                if G.has_node(node_x) and G.has_node(node_y):
                    G.add_edge(node_y, node_x, style='dotted')               


if __name__ == "__main__":
    task_process()
    task_network()
    task_fileio()
    dottedline()
    H = nx.relabel_nodes(G, mapping, copy=True)
    nx.nx_agraph.write_dot(H, "output/hello2.dot")
    nx.nx_agraph.pygraphviz_layout(H)