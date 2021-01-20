import pandas as pd
import networkx as nx
from pandasql import sqldf
import csv


def convert_FileIO_to_AdjacencyList():
    df = pd.read_csv(r'C:\Users\u_priyanka.badva\Desktop\Perfview\FileIO.csv')
    dst = df['File_Path']
    uniq_dst = dst.unique()
    lst_al_file =[]

    for item in uniq_dst:
        lst_temp = []
        
        query = "SELECT DISTINCT Process_Name from df where File_Path=\"" + item + '\"'
        result = sqldf(query)
        

        lst_temp.append(item)
        for index, row in result.iterrows():
            lst_temp.append(row['Process_Name'])
        row_csv = tuple(lst_temp)
        
        lst_al_file.append(row_csv)
        lst_temp.clear()

    with open("AL_FileIO.csv", 'w', newline="") as f:
    #    fields  = ['Source', 'Dest']
        write = csv.writer(f)
    #    write.writerow(fields) 
        write.writerows(lst_al_file)
        
        
def convert_Process_To_AdjacencyList():
    df = pd.read_csv(r'C:\Users\u_priyanka.badva\Desktop\Perfview\Process.csv')
    dst = df['File_Path']
    uniq_dst = dst.unique()
    lst_al_file =[]
    
    for item in uniq_dst:
        print(item)
        lst_tmp = []
        
        item = item.replace('"', '')
        print(item)
        
        
        query = "SELECT DISTINCT Process_Name from df where File_Path=\"" + item + '\"'
        print(query)
        result = sqldf(query)
        print (result)
        break
                
        lst_tmp.append(item)
        for index, row in result.iterrows():
            lst_tmp.append(row['Process_Name'])
        row_csv = tuple(lst_temp)
        #print(row_csv)
        lst_al_file.append(row_csv)
        lst_temp.clear()
        
    with open("AL_Process.csv",'w', newline="") as f:
        write = csv.writer(f)
        write.writerows(lst_al_file)
    

if __name__ == "__main__":
    convert_Process_To_AdjacencyList()
    convert_FileIO_to_AdjacencyList()
    
