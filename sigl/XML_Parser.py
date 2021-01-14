from bs4 import BeautifulSoup
import csv


infile = open(r"C:\Users\u_priyanka.badva\Desktop\Perfview\PerfViewData.etl.xml","r")
contents = infile.read()
soup = BeautifulSoup(contents,'xml')
titles = soup.find_all('Event')


fileio = []
network = []
process = []
for item in titles:
    event = item.get('EventName')
    
    
    if event == 'FileIO/Create' or event == 'FileIO/Read'   or event == 'FileIO/Write' or event == 'FileIO/Delete':
        pname = item.get('PName')
        filename = item.get('FileName')
        row = (event, pname, filename)
        fileio.append(row)
        
    elif event == 'UdpIp/Send' or event == 'UdpIp/Recv' or event == 'TcpIp/Send' or event == 'TcpIp/Recv':
        saddr = item.get('saddr')
        daddr = item.get('daddr')
        sport = item.get('sport')
        dport = item.get('dport')
        pname = item.get('PName')
        row = (event, pname, saddr, sport, daddr, dport )
        network.append(row)
    
    elif event == 'Process/Start' or event == 'Process/Stop':
        cmdline = item.get('CommandLine')
        pname = item.get('PName')
        row = (event, pname, cmdline )
        process.append(row)
        

header_network = ['Event_Name', 'Process_Name', 'Src_Addr', 'Src_Port', 'Dst_Addr', 'Dst_Port' ]
 

with open("FileIO.csv", 'w', newline="") as f:
    fields  = ['Event_Name', 'Process_Name', 'File_Path']
    write = csv.writer(f)
    write.writerow(fields) 
    write.writerows(fileio)
    

with open("Network.csv", 'w', newline="") as f:
    fields  = ['Event_Name', 'Process_Name', 'Src_Addr', 'Src_Port', 'Dst_Addr', 'Dst_Port' ]
    write = csv.writer(f)   
    write.writerow(fields) 
    write.writerows(network)
    
with open("Process.csv", 'w', newline="") as f:        
    fields = ['Event_Name', 'Process_Name', 'File_Path'] 
    write = csv.writer(f)   
    write.writerow(fields) 
    write.writerows(process)
