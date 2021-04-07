from bs4 import BeautifulSoup
import csv
import re


infile = open(r"PerfViewData.etl.xml")
contents = infile.read()
soup = BeautifulSoup(contents,'xml')
titles = soup.find_all('Event')


fileio = []
network = []
process = []
for item in titles:
    event = item.get('EventName')
    
    
    if event == 'FileIO/Create' or event == 'FileIO/Read'   or event == 'FileIO/Write' or event == 'FileIO/Delete' or event == 'FileIO/Create':        
        time = item.get('MSec')
        pname = item.get('PName')
        filename = item.get('FileName')
        pid= item.get('PID')
        filekey = item.get('FileKey')
        filename = re.escape(filename)
        fileobject = item.get('FileObject')
        row = (event, pname, filename, time, pid, filekey, fileobject)
        fileio.append(row)
        #fileio = sorted(set(fileio))
        
    elif event == 'TcpIp/Send' or event == 'TcpIp/Recv':
        saddr = item.get('saddr')
        daddr = item.get('daddr')
        sport = item.get('sport')
        dport = item.get('dport')
        pname = item.get('PName')
        time = item.get('MSec')
        pid= item.get('PID')
        row = (event,pname, saddr, sport, daddr, dport, time, pid )
        network.append(row)
        #network = sorted(set(network))
    
    #elif event == 'Process/Start':
    elif event == 'Process/Start' or event == 'Process/Stop' or event == 'Process/DCStart' or event == 'Process/DCStop':
        cmdline = item.get('CommandLine')
        cmdline = re.escape(cmdline)
        pname = item.get('PName')
        process_id = item.get('ProcessID')
        process_id = re.escape(process_id)
        parent_id = item.get('ParentID')
        time = item.get('MSec')
        exe = item.get('ImageFileName')
        pid= item.get('PID')
        uid = item.get('UniqueProcessKey')
        row = (event, pname, cmdline, time, process_id, parent_id, exe, pid, uid)
        process.append(row)
        #process = sorted(set(process))

with open("csv_files/FileIO.csv", 'w', newline="") as f:
    fields  = ['Event_Name', 'Process_Name', 'File_Path', 'Time','PID', 'FileKey', 'FileObject']
    write = csv.writer(f)
    write.writerow(fields) 
    write.writerows(fileio)
    

with open("csv_files/Network.csv", 'w', newline="") as f:
    fields  = ['Event_Name', 'Process_Name', 'Src_Addr', 'Src_Port', 'Dst_Addr', 'Dst_Port', 'Time', 'PID' ]
    write = csv.writer(f)   
    write.writerow(fields) 
    write.writerows(network)
    
with open("csv_files/Process.csv", 'w', newline="") as f:        
    fields = ['Event_Name',  'Process_Name', 'File_Path', 'Time', 'Process_Id', 'Parent_Id', 'exe', 'PID', 'UniqueProcessKey']
    #fields = ['Event_Name',  'Process_Name', 'File_Path', ]
    write = csv.writer(f)   
    write.writerow(fields) 
    write.writerows(process)
    


    

