from sig_graph_v6 import process_relevant_fileio
from bs4 import BeautifulSoup
import csv
import re
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
threshold_time_network = 10000
threshold_time_file = 10000
pid_mapping = {}
pname_mapping = {}
lst_df_data = []
df_data = pd.DataFrame()
dict_time = {}
df_csv_process = None
df_csv_network = None
df_csv_fileio  = None
df_csv_dll  = None




infile = open(r"Input/PerfViewData.etl.xml")
contents = infile.read()
soup = BeautifulSoup(contents,'xml')
titles = soup.find_all('Event')

def parse_xml_create_csv():
    global titles
    fileio = []
    network = []
    process = []
    dll = []

    for item in titles:
        event = item.get('EventName')
        
        
        if event == 'FileIO/Create' or event == 'FileIO/Read'   or event == 'FileIO/Write' or event == 'FileIO/Delete' or event == 'FileIO/Create':        
            time       = item.get('MSec')
            pid        = item.get('PID')
            pname      = item.get('PName')
            filename   = item.get('FileName')
            filename   = re.escape(filename)
            filekey    = item.get('FileKey')
            fileobject = item.get('FileObject')
            row        = (time, event, pid, pname, filekey, filename, fileobject)
            fileio.append(row)

        elif event == 'TcpIp/Send' or event == 'TcpIp/Recv':
            time       = item.get('MSec')
            pid        = item.get('PID')
            pname      = item.get('PName')
            saddr      = item.get('saddr')
            daddr      = item.get('daddr')
            sport      = item.get('sport')
            dport      = item.get('dport')
            row        = (time, event, pid, pname, saddr, sport, daddr, dport)
            network.append(row)

        elif event == 'Process/Start' or event == 'Process/Stop' or event == 'Process/DCStart' or event == 'Process/DCStop':
            time          = item.get('MSec')
            pid           = item.get('PID')
            pname         = item.get('PName')
            processid     = item.get('ProcessID')
            processid     = re.escape(processid)
            parentid      = item.get('ParentID')            
            cmdline       = item.get('CommandLine')
            cmdline       = re.escape(cmdline)
            imagefilename = item.get('ImageFileName')
            upk           = item.get('UniqueProcessKey')
            row           = (time, event, pid, pname, processid, parentid, cmdline, imagefilename, upk)
            process.append(row)

        elif event == "Image/DCStart" or event == "Image/DCStop":
            time      = item.get('MSec')
            pid       = item.get('PID')
            pname     = item.get('PName')
            filename  = item.get('FileName')
            filename  = re.escape(filename)
            imagebase = item.get('ImageBase')
            row       = (time, event, pid, pname, imagebase, filename)
            dll.append(row)
            

    with open("csv_files/FileIO.csv", 'w', newline="") as f:
        fields  = ['Time', 'EventName', 'PID', 'PName', 'FileKey', 'FileName', 'FileObject']
        write = csv.writer(f)
        write.writerow(fields) 
        write.writerows(fileio)
        

    with open("csv_files/Network.csv", 'w', newline="") as f:
        fields  = ['Time', 'EventName', 'PID', 'PName', 'saddr', 'sport', 'daddr', 'dport']
        write = csv.writer(f)   
        write.writerow(fields) 
        write.writerows(network)
        
    with open("csv_files/Process.csv", 'w', newline="") as f:        
        fields = ['Time', 'EventName', 'PID', 'PName', 'ProcessID', 'ParentID', 'CommandLine', 'ImageBase', 'UniqueProcessKey']
        write = csv.writer(f)   
        write.writerow(fields) 
        write.writerows(process)

    with open("csv_files/dll.csv", 'w', newline="") as f:        
        fields = ['Time', 'EventName', 'PID', 'PName', 'ImageBase', 'FileName']
        write = csv.writer(f)   
        write.writerow(fields) 
        write.writerows(dll)        
    

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
    
    pid_pid   = df_csv_process.at[row_idx, 'PID']
    pid_pname = df_csv_process.at[row_idx, 'PName']
    pid_ppid  = int(df_csv_process.at[row_idx, 'ParentID'].replace(",",""))
    pid_psk   = str(pid_pid) + "_" + str(pid_pname)
    
    #  We need to find the PName and ParentID where ParentID became pid. So first extracting the index of it.
    row_idx_ppid = (df_csv_process.loc[(df_csv_process['PID'] ==  pid_ppid)]).index

    # Extracting values using at; Using [0] as there can be multiple enteries
    ppid_pid   = pid_ppid
    ppid_pname = df_csv_process.at[row_idx_ppid[0],'PName']
    ppid_ppid  = df_csv_process.at[row_idx_ppid[0],'ParentID']
    ppid_psk   = str(ppid_pid) + "_" + str(ppid_pname)
    
    # Creating a dictionary with above extracted attributes with counter
    temp_dict = {  "UniqueKey": pid_psk, "ID": pid_pid, "Name": pid_pname, "Type": "Process", "Count": 0}
    if temp_dict not in lst_df_data:
        lst_df_data.append(temp_dict)
  
    temp_dict = { "UniqueKey": ppid_psk, "ID": ppid_pid, "Name": ppid_pname, "Type":"Process", "Count": 0}
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
        pid_pid   = row.PID
        pid_ppid  = int(row.ParentID.replace(",",""))
        pid_pname = row.PName
        pid_psk   = str(pid_pid) + "_" + str(pid_pname)

        row_idx_ppid = (df_csv_process.loc[(df_csv_process['PID'] ==  pid_ppid)]).index
        if row_idx_ppid.empty:
            # Do something
            ppid_pid = pid_ppid
            ppid_psk = "0xDEADBEEF"
        else:
        # Extracting values using at from df_csv; Using [0] as there can be multiple enteries
            ppid_pid   = pid_ppid
            ppid_pname = df_csv_process.at[row_idx_ppid[0],'PName']
            ppid_ppid  = df_csv_process.at[row_idx_ppid[0],'ParentID']
            ppid_psk   = str(ppid_pid) + "_" + str(ppid_pname)

 
    #   # Ensuring that current row is relevant
        if pid_psk in lst_node or ppid_psk in lst_node:

            temp_dict = {  "UniqueKey": pid_psk, "ID": pid_pid, "Name": pid_pname, "Type": "Process", "Count": 0}
            if temp_dict not in lst_df_data:
                lst_df_data.append(temp_dict)
        
            temp_dict = { "UniqueKey": ppid_psk, "ID": ppid_pid, "Name": ppid_pname, "Type":"Process", "Count": 0}
            if temp_dict not in lst_df_data:
                lst_df_data.append(temp_dict)

            if row.EventName == 'Process/Start' or row.EventName == 'Process/DCStart':
                # Adding the child process to our relevant nodes
                if pid_psk not in lst_node:
                    lst_node.append(pid_psk)

def get_relevant_network():

    global lst_node
    global df_data
    global df_csv_process
    global df_csv_network
    
    # Processing each row
    for row in df_csv_network.itertuples(index=False):
        pid_pid  = row.PID
        pid_pname = row.PName
        pid_psk   = str(pid_pid) + "_" + str(pid_pname)
        ip   = row.daddr

        # The row is relevant is the row.PID is the list_node
        if pid_psk in lst_node or ip in lst_node:

            temp_dict = {  "UniqueKey": ip, "ID": ip, "Name": ip, "Type": "Network", "Count": 0}
            if temp_dict not in lst_df_data:
                lst_df_data.append(temp_dict)

def get_relevant_fileio():

    global lst_node
    global df_data
    global df_csv_process
    global df_csv_fileio

    
    # Processing each row
    for row in df_csv_fileio.itertuples(index=False):
        pid_pid    = row.PID
        pid_pname  = row.PName
        filekey    = row.FileKey
        fileobject = row.FileObject
        file_path  = row.FileName
        event      = row.EventName
        time       = row.Time        

        #  We need to find the UniqueKey of pid. So first extracting the index of it.
        row_idx_pid = (df_csv_process.loc[(df_csv_process['PID'] ==  pid_pid)]).index

    # Extracting values using at; Using [0] as there can be multiple enteries
        if row_idx_pid.empty:
            pid_psk = "0xDEADBEEF"
        else:
            #pid_psk   = df_csv_process.at[row_idx_pid[0],'UniqueProcessKey']
            pid_psk   = str(pid_pid) + "_" + str(pid_pname)

        # The row is relevant is the row.PID is the list_node
        if pid_psk in lst_node or filekey in lst_node:
            
            if event == 'FileIO/Write' or event == 'FileIO/Delete' or event == 'FileIO/Read':
                temp_dict = {  "UniqueKey": filekey, "ID": filekey, "Name": file_path, "Type": "FileIO", "Count": 0}
                if temp_dict not in lst_df_data:
                    lst_df_data.append(temp_dict)


def get_relevant_dll():

    global lst_node
    global df_data
    global df_csv_process
    global df_csv_fileio
    global df_csv_dll

    
    # Processing each row
    for row in df_csv_dll.itertuples(index=False):
        pid_pid =  row.PID
        pid_pname = row.PName
        filename = row.FileName
        imagebase = row.ImageBase
        event = row.EventName
        time = row.Time        

        #  We need to find the UniqueKey of pid. So first extracting the index of it.
        row_idx_pid = (df_csv_process.loc[(df_csv_process['PID'] ==  pid_pid)]).index

    # Extracting values using at; Using [0] as there can be multiple enteries
        if row_idx_pid.empty:
            pid_psk = "0xDEADBEEF"
        else:
            #pid_psk   = df_csv_process.at[row_idx_pid[0],'UniqueProcessKey']
            pid_psk   = str(pid_pid) + "_" + str(pid_pname)

        # The row is relevant is the row.PID is the list_node
        if pid_psk in lst_node or imagebase in lst_node:
            
            if event == 'Image/DCStart' or event == 'Image/DCStop':
                temp_dict = {  "UniqueKey": imagebase, "ID": imagebase, "Name": filename, "Type": "DLL", "Count": 0}
                if temp_dict not in lst_df_data:
                    lst_df_data.append(temp_dict)


def process_relevant_process(item):
    # Boolean variable provides information whether a new version is required or not
    global df_data
    pid_nv = False
    ppid_nv = False

    pid_pid    = item.get('PID')
    pid_pname  = item.get('PName')
    pid_ppid   = int(item.get('ParentID').replace(",",""))
    pid_psk    = str(pid_pid) + "_" + str(pid_pname)
    event_name = item.get('EventName')
    time       = item.get('MSec')
    file_path  = item.get('CommandLine')

    row_idx_ppid = (df_csv_process.loc[(df_csv_process['PID'] ==  pid_ppid)]).index
    if row_idx_ppid.empty:
        ppid_pid = pid_ppid
        ppid_psk = "0xDEADBEEF"
    else:
    # Extracting values using at from df_csv; Using [0] as there can be multiple enteries
        ppid_pid   = pid_ppid
        ppid_pname = df_csv_process.at[row_idx_ppid[0],'PName']
        ppid_ppid  = df_csv_process.at[row_idx_ppid[0],'ParentID']        
        ppid_psk   = str(ppid_pid) + "_" + str(ppid_pname)

    # Ensuring that current row is relevant
    if pid_psk in lst_node or ppid_psk in lst_node:

        if event_name == 'Process/Start' or event_name == 'Process/DCStart':
            # If Process_Start, the edge should be Parent_Id to Process_Id
            pid_nv = True
            ppid_nv = False
        elif event_name == 'Process/Stop' or event_name == 'Process/DCStop':
            # If Process_Stop, the edge should be Process_Id to Parent_Id
            pid_nv = False
            ppid_nv = True

        row_index_pid  = (df_data.loc[(df_data['UniqueKey'] == pid_psk ) & (df_data['ID'] == int(pid_pid))]).index
        row_index_ppid = (df_data.loc[(df_data['UniqueKey'] == ppid_psk) & (df_data['ID'] == int(ppid_pid))]).index
        
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


        if event_name == 'Process/Start' or event_name == 'Process/DCStart':
            # If Process_Start, the edge should be Parent_Id to Process_Id
            src = u_ppid
            dst = u_pid
            id_src = row_index_ppid
            id_dst = row_index_pid
        elif event_name == 'Process/Stop' or event_name == 'Process/DCStop':
            # If Process_Stop, the edge should be Process_Id to Parent_Id
            src = u_pid
            dst = u_ppid
            id_src = row_index_pid
            id_dst = row_index_ppid

        if not G.has_node(src):
            G.add_node(src,shape='box', FilePath = file_path, Time = time)
            df_data.at[id_src[0],'Count'] += 1

        if not G.has_node(dst):
            G.add_node(dst, shape='box')
            df_data.at[id_dst[0],'Count'] += 1                

        if not G.has_edge(src,dst):
            G.add_edge(src, dst, time=time, EventType=event_name, xlabel= event_name[8:])

        pid_nv = False
        ppid_nv = False

def process_relevant_network(item):

    global lst_node
    global df_data
    global dict_time
    global df_csv_process
    global df_csv_network
    insert_row = False

    pid_pid    = item.get('PID')
    pid_pname  = item.get('PName')
    pid_psk    = str(pid_pid) + "_" + str(pid_pname)
    eventname = item.get('EventName')
    time       = float(item.get('MSec'))
    ip         = item.get('daddr')

    # The row is relevant is the row.PID is the list_node
    if pid_psk in lst_node or ip in lst_node:

        ip_event = str(ip) + '_' + str(eventname)
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
            if eventname == 'TcpIp/Send':
            # If TcpIp/Send, the edge should be PID to Dst_Addr
                pid_nv = False
                ip_nv = True
            elif eventname == 'TcpIp/Recv':
            # If TcpIp/Receive, the edge should be Dst_Addr to PID
                pid_nv = True
                ip_nv = False

            row_idx_pid  = (df_data.loc[(df_data['UniqueKey'] == pid_psk ) & (df_data['ID'] == int(pid_pid) )]).index
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
                    u_ip = str(ip) + "_" + str(ip_count)    
                else:
                    u_ip = str(ip) + "_" + str(ip_count - 1)


            if eventname == 'TcpIp/Send':
                # If Process_Start, the edge should be Parent_Id to Process_Id
                src = u_pid
                dst = u_ip
                id_src = row_idx_pid
                id_dst = row_idx_ip
                shape_src = 'box'
                shape_dst = 'diamond'

            elif eventname == 'TcpIp/Recv':
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
                G.add_edge(src, dst, key= eventname, time=time, EventType=eventname, xlabel= eventname[6:]) 
            ip_nv = False
            pid_nv = False

        insert_row = False


def process_relevant_fileio(item):

    global process_count
    global list_node
    global threshold_time
    global dict_time

    insert_row = False

    """Start with parsing fileio"""
    
   # Process other rows
    pid_pid    = item.get('PID')
    pid_pname  = item.get('PName')
    pid_psk    = str(pid_pid) + "_" + str(pid_pname)
    eventname = item.get('EventName')
    time       = float(item.get('MSec'))
    filekey    = item.get('FileKey')  

# Extracting values using at; Using [0] as there can be multiple enteries
    if eventname != 'FileIO/Create':

        # If relevant
        if pid_psk in lst_node or filekey in lst_node:

            file_event = str(filekey) + '_' + str(eventname)
            if file_event in dict_time.keys():
                time_diff = time - dict_time[file_event]
                if time_diff > threshold_time_file:
                    insert_row = True
                    dict_time.update({file_event:time})
            else:
                insert_row = True
                dict_time.update({file_event:time})

            if insert_row:
            
                if eventname == 'FileIO/Write':
                    pid_nv = False
                    file_nv = True
                elif eventname == 'FileIO/Read':
                    pid_nv = True
                    file_nv = False
                elif eventname == 'FileIO/Delete':
                    pid_nv = False
                    file_nv = True
                elif eventname == 'FileIO/Create':
                    pid_nv = False
                    file_nv = True

                
                row_idx_pid  = (df_data.loc[(df_data['UniqueKey'] == pid_psk ) & (df_data['ID'] == int(pid_pid) )]).index
                row_idx_file = (df_data.loc[(df_data['UniqueKey'] == filekey) & (df_data['ID'] == filekey)]).index
            
                pid_count  = df_data.at[row_idx_pid[0] ,"Count"]
                file_count = df_data.at[row_idx_file[0],"Count"]    

                if pid_nv == True:
                    u_pid = str(pid_psk) + "_" + str(pid_count)
                else:
                    if pid_count == 0:
                        u_pid = str(pid_psk) + "_" + str(pid_count)
                    else:
                        u_pid = str(pid_psk) + "_" + str(pid_count - 1)
                    

                if file_nv == True:
                    u_file = str(filekey) + "_" + str(file_count)
                else:
                    if file_count == 0:
                        u_file = str(filekey) + "_" + str(file_count)    
                    else:
                        u_file = str(filekey) + "_" + str(file_count - 1)
            
                if eventname == 'FileIO/Read':
                    # If Process_Start, the edge should be Parent_Id to Process_Id
                    src = u_file
                    dst = u_pid
                    id_src = row_idx_file
                    id_dst = row_idx_pid
                    shape_src = 'ellipse'
                    shape_dst = 'box'
                else:
                    # If Process_Stop, the edge should be Process_Id to Parent_Id
                    src = u_pid
                    dst = u_file
                    id_src = row_idx_pid
                    id_dst = row_idx_file
                    shape_src = 'box'
                    shape_dst = 'ellipse'                    

                if not G.has_node(src):
                    G.add_node(src, shape=shape_src)
                    df_data.at[id_src[0],'Count'] += 1

                if not G.has_node(dst):
                    G.add_node(dst, shape=shape_dst)
                    df_data.at[id_dst[0],'Count'] += 1

            # Add the Edge
                if not (G.has_edge(src,dst) or G.has_edge(dst,src)):
                    G.add_edge(src, dst, key= eventname, time=time, EventType=eventname, xlabel= eventname[7:]) 
                file_nv = False
                pid_nv = False

            insert_row = False

def process_xml():
    for item in titles:
        event = item.get('EventName')
        
        if event == 'FileIO/Create' or event == 'FileIO/Read'   or event == 'FileIO/Write' or event == 'FileIO/Delete' or event == 'FileIO/Create':
            process_relevant_fileio(item)
            
        elif event == 'TcpIp/Send' or event == 'TcpIp/Recv':
            process_relevant_network(item)
        
        elif event == 'Process/Start' or event == 'Process/Stop' or event == 'Process/DCStart' or event == 'Process/DCStop':
            process_relevant_process(item)
        elif event == "Image/DCStart" or event == "Image/DCStop":
            pass

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

    #parse_xml_create_csv()
    df_csv_process = pd.read_csv(r'csv_files/Process.csv',  header = 0)
    df_csv_network = pd.read_csv(r'csv_files/Network.csv',  header = 0)
    df_csv_fileio  = pd.read_csv(r'csv_files/FileIO.csv',  header = 0)
    df_csv_dll     = pd.read_csv(r'csv_files/dll.csv',  header = 0)    
    get_relevant_process()
    get_relevant_network()
    get_relevant_fileio()
    get_relevant_dll()
    df_data = pd.DataFrame(lst_df_data)
    df_data.to_csv("horrible.csv")

    process_xml()
    dottedline()
    mapping_proc()

  

    H = nx.relabel_nodes(G, mapping, copy=True)
    nx.nx_agraph.write_dot(H, "output/hello3.dot")
    nx.nx_agraph.pygraphviz_layout(H)     
