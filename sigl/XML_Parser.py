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
    
    
    if event == 'FileIO/Create' or event == 'FileIO/Read'   or event == 'FileIO/Write' or event == 'FileIO/Delete':        
        time = item.get('MSec')
        pname = item.get('PName')
        filename = item.get('FileName')
        filename = re.escape(filename)
        row = (event, pname, filename, time)
        fileio.append(row)
        #fileio = sorted(set(fileio))
        
    elif event == 'UdpIp/Send' or event == 'UdpIp/Recv' or event == 'TcpIp/Send' or event == 'TcpIp/Recv':
        saddr = item.get('saddr')
        daddr = item.get('daddr')
        sport = item.get('sport')
        dport = item.get('dport')
        pname = item.get('PName')
        time = item.get('MSec')
        row = (event, pname, saddr, sport, daddr, dport, time )
        network.append(row)
        #network = sorted(set(network))
    
    elif event == 'Process/Start' or event == 'Process/Stop':
        cmdline = item.get('CommandLine')
        cmdline = re.escape(cmdline)
        pname = item.get('PName')
        process_id = item.get('ProcessID')
        process_id = re.escape(process_id)
        parent_id = item.get('ParentID')
        time = item.get('MSec')
        exe = item.get('ImageFileName')
        row = (event, pname, cmdline, time, process_id, parent_id, exe)
        process.append(row)
        #process = sorted(set(process))

with open("FileIO.csv", 'w', newline="") as f:
    fields  = ['Event_Name', 'Process_Name', 'File_Path', 'Time']
    write = csv.writer(f)
    write.writerow(fields) 
    write.writerows(fileio)
    

with open("Network.csv", 'w', newline="") as f:
    fields  = ['Event_Name', 'Process_Name', 'Src_Addr', 'Src_Port', 'Dst_Addr', 'Dst_Port', 'Time' ]
    write = csv.writer(f)   
    write.writerow(fields) 
    write.writerows(network)
    
with open("Process.csv", 'w', newline="") as f:        
    fields = ['Event_Name',  'Process_Name', 'File_Path', 'Time', 'Process_Id', 'Parent_Id', 'exe']
    #fields = ['Event_Name',  'Process_Name', 'File_Path', ]
    write = csv.writer(f)   
    write.writerow(fields) 
    write.writerows(process)
    


    

