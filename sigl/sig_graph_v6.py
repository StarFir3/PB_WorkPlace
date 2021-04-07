from os import replace
import networkx as nx
from networkx.algorithms.traversal.depth_first_search import dfs_edges
from numpy import row_stack
from numpy.lib.utils import source
import pandas as pd
import matplotlib.pyplot as plt
import networkx
from pandas.core.frame import DataFrame
import pylab
from networkx.drawing.nx_agraph import graphviz_layout
import pygraphviz as pyg
from itertools import count, islice
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
lst_node = []
list_dict_pc = []
# Setting Threshold to 5 seconds
threshold_time_network = 10
threshold_time_file = 10
pid_mapping = {}
pname_mapping = {}
lst_df_data = []
df_data = pd.DataFrame()
dict_time = {}
df_csv_process = pd.read_csv(r'csv_files/Process.csv',  header = 0)
df_csv_network = pd.read_csv(r'csv_files/Network.csv',  header = 0)
df_csv_fileio  = pd.read_csv(r'csv_files/FileIO.csv',  header = 0)


def get_relevant_process():
    """Start with parsing processes"""

    # list_node stores the relevant nodes to the graph
    global lst_node
    global df_data
    global df_csv_process
     
    
    # Get the last row index to retrieve the relevant object
    row_idx = df_csv_process.last_valid_index()

    # A row can have two objects (src/dst) which is equal to process and it's parent (which is also a process)
    # A process can have multiple attributes: 
    # Start with the getting attributes UniqueProcessKey, pid, parent id, process name
    pid_psk   = df_csv_process.at[row_idx, 'UniqueProcessKey']
    pid_pid   = df_csv_process.at[row_idx, 'PID']
    pid_pname = df_csv_process.at[row_idx, 'exe']
    pid_ppid  = int(df_csv_process.at[row_idx, 'Parent_Id'].replace(",",""))
    
    #  We need to find the UniqueProcessKey where parentid became pid. So first extracting the index of it.
    row_idx_ppid = (df_csv_process.loc[(df_csv_process['PID'] ==  pid_ppid)]).index

    # Extracting values using at; Using [0] as there can be multiple enteries
    ppid_psk   = df_csv_process.at[row_idx_ppid[0],'UniqueProcessKey']
    ppid_pid   = pid_ppid
    ppid_pname = df_csv_process.at[row_idx_ppid[0],'exe']
    ppid_ppid  = df_csv_process.at[row_idx_ppid[0],'Parent_Id']
    
    # Creating a dictionary with above extracted attributes with counter
    temp_dict = {  "UniqueKey": pid_psk, "ID": pid_pid, "Name": pid_pname, "Type": "Process", "Count": 0, "PrevTime": 0.0}
    if temp_dict not in lst_df_data:
        lst_df_data.append(temp_dict)
  
    temp_dict = { "UniqueKey": ppid_psk, "ID": ppid_pid, "Name": ppid_pname, "Type":"Process", "Count": 0, "PrevTime": 0.0}
    if temp_dict not in lst_df_data:
        lst_df_data.append(temp_dict)

    # Both nodes are relevant
    if pid_psk not in lst_node:
        lst_node.append(pid_psk)
    if ppid_psk not in lst_node:
        lst_node.append(ppid_psk)

    # Itertuples Refer https://pandas.pydata.org/pandas-docs/stable/reference/api/pandas.DataFrame.itertuples.html
    # Processing Rows
    for row in df_csv_process.itertuples(index=False):
        pid_psk   = row.UniqueProcessKey
        pid_pid   = row.PID
        pid_ppid  = int(row.Parent_Id.replace(",",""))
        pid_pname = row.exe

        row_idx_ppid = (df_csv_process.loc[(df_csv_process['PID'] ==  pid_ppid)]).index
        if row_idx_ppid.empty:
            # Do something
            ppid_pid = pid_ppid
            ppid_psk = "0xDEADBEEF"
        else:
        # Extracting values using at from df_csv; Using [0] as there can be multiple enteries
            ppid_psk   = df_csv_process.at[row_idx_ppid[0],'UniqueProcessKey']
            ppid_pid   = pid_ppid
            ppid_pname = df_csv_process.at[row_idx_ppid[0],'exe']
            ppid_ppid  = df_csv_process.at[row_idx_ppid[0],'Parent_Id']        

 
    #   # Ensuring that current row is relevant
        if pid_psk in lst_node or ppid_psk in lst_node:

            temp_dict = {  "UniqueKey": pid_psk, "ID": pid_pid, "Name": pid_pname, "Type": "Process", "Count": 0, "PrevTime": 0.0}
            if temp_dict not in lst_df_data:
                lst_df_data.append(temp_dict)
        
            temp_dict = { "UniqueKey": ppid_psk, "ID": ppid_pid, "Name": ppid_pname, "Type":"Process", "Count": 0, "PrevTime": 0.0}
            if temp_dict not in lst_df_data:
                lst_df_data.append(temp_dict)

            if row.Event_Name == 'Process/Start' or row.Event_Name == 'Process/DCStart':
                # Adding the child process to our relevant nodes
                if pid_psk not in lst_node:
                    lst_node.append(pid_psk)

def process_relevant_process():
    # Boolean variable provides information whether a new version is required or not
    pid_nv = False
    ppid_nv = False  

    df_csv = pd.read_csv(r'csv_files/Process.csv',  header = 0)
    # Processing Rows
    for row in df_csv.itertuples(index=False):
        pid_psk   = row.UniqueProcessKey
        pid_pid   = row.PID
        pid_ppid  = int(row.Parent_Id.replace(",",""))
        pid_pname = row.exe

        row_idx_ppid = (df_csv.loc[(df_csv['PID'] ==  pid_ppid)]).index
        if row_idx_ppid.empty:
            ppid_pid = pid_ppid
            ppid_psk = "0xDEADBEEF"
        else:
        # Extracting values using at from df_csv; Using [0] as there can be multiple enteries
            ppid_psk   = df_csv.at[row_idx_ppid[0],'UniqueProcessKey']
            ppid_pid   = pid_ppid
            ppid_pname = df_csv.at[row_idx_ppid[0],'exe']
            ppid_ppid  = df_csv.at[row_idx_ppid[0],'Parent_Id']        

        # Ensuring that current row is relevant
        if pid_psk in lst_node or ppid_psk in lst_node:

            if row.Event_Name == 'Process/Start' or row.Event_Name == 'Process/DCStart':
                # If Process_Start, the edge should be Parent_Id to Process_Id
                pid_nv = True
                ppid_nv = False
            elif row.Event_Name == 'Process/Stop' or row.Event_Name == 'Process/DCStop':
                # If Process_Stop, the edge should be Process_Id to Parent_Id
                pid_nv = False
                ppid_nv = True

            row_index_pid  = (df_data.loc[(df_data['UniqueKey'] == pid_psk ) & (df_data['ID'] == pid_pid )]).index
            row_index_ppid = (df_data.loc[(df_data['UniqueKey'] == ppid_psk) & (df_data['ID'] == ppid_pid)]).index
            
            pid_count  = df_data.at[row_index_pid[0] ,"Count"]
            ppid_count = df_data.at[row_index_ppid[0],"Count"]

            # Checking if new version is required
            if pid_nv == True:
                u_pid = str(pid_psk) + "_" + str(pid_count)
            else:
                if pid_count == 0:
                    u_pid = str(pid_psk) + "_" + str(pid_count)
                else:
                    u_pid = str(pid_psk) + "_" + str(pid_count - 1)

            if ppid_nv == True:
                u_ppid = str(ppid_psk) + "_" + str(ppid_count)
            else:
                if ppid_count == 0:
                    u_ppid = str(ppid_psk) + "_" + str(ppid_count)    
                else:
                    u_ppid = str(ppid_psk) + "_" + str(ppid_count - 1)


            if row.Event_Name == 'Process/Start' or row.Event_Name == 'Process/DCStart':
                # If Process_Start, the edge should be Parent_Id to Process_Id
                src = u_ppid
                dst = u_pid
                id_src = row_index_ppid
                id_dst = row_index_pid
            elif row.Event_Name == 'Process/Stop' or row.Event_Name == 'Process/DCStop':
                # If Process_Stop, the edge should be Process_Id to Parent_Id
                src = u_pid
                dst = u_ppid
                id_src = row_index_pid
                id_dst = row_index_ppid

            if not G.has_node(src):
                G.add_node(src,shape='box', FilePath = row.File_Path, Time = row.Time)
                df_data.at[id_src[0],'Count'] += 1

            if not G.has_node(dst):
                G.add_node(dst, shape='box')
                df_data.at[id_dst[0],'Count'] += 1                

            if not G.has_edge(src,dst):
                G.add_edge(src, dst, time=row.Time, EventType=row.Event_Name, xlabel= row.Event_Name[8:])

            pid_nv = False
            ppid_nv = False
                      
def get_relevant_network():

    global lst_node
    global df_data
    global df_csv_process
    global df_csv_network
    
    # Processing each row
    for row in df_csv_network.itertuples(index=False):
        pid  = row.PID
        ip   = row.Dst_Addr
        evnt = row.Event_Name
        time = row.Time        

        #  We need to find the UniqueKey of pid. So first extracting the index of it.
        row_idx_pid = (df_csv_process.loc[(df_csv_process['PID'] ==  pid)]).index

    # Extracting values using at; Using [0] as there can be multiple enteries
        pid_psk   = df_csv_process.at[row_idx_pid[0],'UniqueProcessKey']

        # The row is relevant is the row.PID is the list_node
        if pid_psk in lst_node or ip in lst_node:

            temp_dict = {  "UniqueKey": ip, "ID": ip, "Name": ip, "Type": "Network", "Count": 0, "PrevTime": 0.0}
            if temp_dict not in lst_df_data:
                lst_df_data.append(temp_dict)

def process_relevant_network():

    global lst_node
    global df_data
    global dict_time
    global df_csv_process
    global df_csv_network
    
    # Processing each row
    for row in df_csv_network.itertuples(index=False):
        pid_pid  = row.PID
        ip   = row.Dst_Addr
        evnt = row.Event_Name
        time = row.Time        

        #  We need to find the UniqueKey of pid. So first extracting the index of it.
        row_idx_pid = (df_csv_process.loc[(df_csv_process['PID'] ==  pid_pid)]).index

    # Extracting values using at; Using [0] as there can be multiple enteries
        pid_psk   = df_csv_process.at[row_idx_pid[0],'UniqueProcessKey']

        # The row is relevant is the row.PID is the list_node
        if pid_psk in lst_node or ip in lst_node:

            ip_event = str(ip) + '_' + str(evnt)
            if ip_event in dict_time.keys():
                time_diff = time - dict_time[ip_event]
                if time_diff > threshold_time_network:
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

                row_idx_pid  = (df_data.loc[(df_data['UniqueKey'] == pid_psk ) & (df_data['ID'] == pid_pid )]).index
                row_idx_ip = (df_data.loc[(df_data['UniqueKey'] == ip) & (df_data['ID'] == ip)]).index
            
                pid_count  = df_data.at[row_idx_pid[0] ,"Count"]
                ip_count = df_data.at[row_idx_ip[0],"Count"]                    

                if pid_nv == True:
                    u_pid = str(pid_psk) + "_" + str(pid_count)
                else:
                    if pid_count == 0:
                        u_pid = str(pid_psk) + "_" + str(pid_count)
                    else:
                        u_pid = str(pid_psk) + "_" + str(pid_count - 1)
                    

                if ip_nv == True:
                    u_ip = str(ip) + "_" + str(ip_count)
                else:
                    if ip_count == 0:
                        u_ppid = str(ip) + "_" + str(ip_count)    
                    else:
                        u_ppid = str(ip) + "_" + str(ip_count - 1)


                if row.Event_Name == 'TcpIp/Send':
                    # If Process_Start, the edge should be Parent_Id to Process_Id
                    src = u_pid
                    dst = u_ip
                    id_src = row_idx_pid
                    id_dst = row_idx_ip
                    shape_src = 'box'
                    shape_dst = 'diamond'

                elif row.Event_Name == 'TcpIp/Recv':
                    # If Process_Stop, the edge should be Process_Id to Parent_Id
                    src = u_ip
                    dst = u_pid
                    id_src = row_idx_ip
                    id_dst = row_idx_pid
                    shape_src = 'diamond'
                    shape_dst = 'box'


                if not G.has_node(src):
                    G.add_node(src, shape=shape_src)
                    df_data.at[id_src[0],'Count'] += 1

                if not G.has_node(dst):
                    G.add_node(dst, shape=shape_dst)
                    df_data.at[id_dst[0],'Count'] += 1

            # Add the Edge
                if not (G.has_edge(src,dst) or G.has_edge(dst,src)):
                    G.add_edge(src, dst, key= row.Event_Name, time=row.Time, EventType=row.Event_Name, xlabel= row.Event_Name[6:]) 
                ip_nv = False
                pid_nv = False

            insert_row = False

def get_relevant_fileio():

    global lst_node
    global df_data
    global df_csv_process
    global df_csv_fileio

    
    # Processing each row
    for row in df_csv_fileio.itertuples(index=False):
        pid =  row.PID
        filekey = row.FileKey
        fileobject = row.FileObject
        file_path = row.File_Path
        evnt = row.Event_Name
        time = row.Time        

        #  We need to find the UniqueKey of pid. So first extracting the index of it.
        row_idx_pid = (df_csv_process.loc[(df_csv_process['PID'] ==  pid)]).index

    # Extracting values using at; Using [0] as there can be multiple enteries
        if row_idx_pid.empty:
            pid_psk = "0xDEADBEEF"
        else:
            pid_psk   = df_csv_process.at[row_idx_pid[0],'UniqueProcessKey']

        # The row is relevant is the row.PID is the list_node
        if pid_psk in lst_node or filekey in lst_node:

            temp_dict = {  "UniqueKey": filekey, "ID": filekey, "Name": file_path, "Type": "FileIO", "Count": 0, "PrevTime": 0.0}
            if temp_dict not in lst_df_data:
                lst_df_data.append(temp_dict)


def task_fileio():

    global process_count
    global list_node
    global threshold_time
    global dict_time

    insert_row = False

    """Start with parsing fileio"""
    

    # Creating counter for filepath
    u_filepath = list(df.File_Path.unique())    
    for row in u_filepath:
        process_count.update({row:0}) 

    u_pid = list(df.FileKey.unique())    
    for row in u_pid:
        if not row in process_count:
            process_count.update({row:0})

    # Process other rows
    for row in df.itertuples(index=False):

        pid = row.FileKey
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

    global df_data
    for row in df_data.itertuples(index=False):
        key = row.UniqueKey
        count = row.Count
        if count > 1:
            for i in reversed(range(0,count)):
                node_x = str(key) + "_" + str(i)
                node_y = str(key) + "_" + str(i - 1)
  
                if G.has_node(node_x) and G.has_node(node_y):
                    G.add_edge(node_y, node_x, style='dotted')  
        else:
            node_x = str(key) + "_0" 
            node_y = str(key) + "_1"
            if G.has_node(node_x) and G.has_node(node_y):
                G.add_edge(node_y, node_x, style='dotted')             

def mapping_proc():

    global df_data
    global mapping
    dict_map = {}

    for index, row in df_data.iterrows():
        upk = row['UniqueKey']
        pname = row['Name']
        count = row['Count']

        for x in range(0,count):
            upk_key = upk + '_' + str(x)
            dict_map[upk_key] = pname + "_" + str(x)

    mapping.update(dict_map)

if __name__ == "__main__":
    get_relevant_process()
    get_relevant_network()
    get_relevant_fileio()
    df_data = pd.DataFrame(lst_df_data)
    df_data.to_csv("horrible.csv")
    process_relevant_process()
    process_relevant_network()
    #task_network()
    #task_fileio()
    dottedline()
    mapping_proc()

  

    H = nx.relabel_nodes(G, mapping, copy=True)
    nx.nx_agraph.write_dot(H, "output/hello3.dot")
    nx.nx_agraph.pygraphviz_layout(H)