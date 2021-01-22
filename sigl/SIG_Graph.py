import networkx as nx
from numpy.lib.utils import source
import pandas as pd
import matplotlib.pyplot as plt
import networkx
import pylab
from networkx.drawing.nx_agraph import graphviz_layout
import pygraphviz as pyg
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
   

def task_fileio():    
    df = pd.read_csv(r'FileIO.csv')    

    # Finding Unique source nodes and destination nodes for adding the nodes.
    uniq_filepath = df['File_Path'].unique()
    uniq_process = df['Process_Name'].unique()
    print (uniq_process)
    # Adding  Unique source nodes and destination nodes into graph.
    G.add_nodes_from(uniq_filepath,node_type='file', shape='o')
    G.add_nodes_from(uniq_process, node_type='process', shape='s')

    # The format is ['Event_Name', 'Process_Name', 'File_Path', 'Time']
    for index, row in df.iterrows():
        # List for edges
        edges = [] 
        event_name = row[0]
        dst = row[1]
        src = row[2]
        time = row[3]

        # Edge Attributes
        edge_attrs = {"time":time, "EventType":event_name}
        # As we have directed graph, setting source and destination respectively
        if event_name == 'FileIO/Write':
            edge_tuple = (dst, src,edge_attrs)
        elif event_name == 'FileIO/Read':
            edge_tuple = (src, dst,edge_attrs)
        elif event_name == 'FileIO/Delete':
            edge_tuple = (dst, src,edge_attrs)
        else:
            edge_tuple = (dst, src,edge_attrs)
        edges.append(edge_tuple)    
   
        #if src and dest nodes present then build an edge
        if G.has_node(src) and G.has_node(dst):
            if not G.has_edge(src,dst):
                G.add_edges_from(edges)
        #nx.set_edge_attributes(G, attrs)
        edges.clear()
        del edges

    # Try to display it via NetworkX with Matplotlib
    # pos = nx.spring_layout(G)
    # nx.draw_networkx(G, pos)
    # plt.show()

    nx.nx_agraph.write_dot(G, "hello.dot")
    nx.nx_agraph.pygraphviz_layout(G)


if __name__ == "__main__":
    task_fileio()









