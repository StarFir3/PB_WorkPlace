import networkx
import pylab
import pandas as pd
options = {
    "font_size": 12,
    "node_size": 3000,
    "node_color": "white",
    "edgecolors": "black",
    "linewidths": 5,
    "width": 5,
}

#Build a graph (Node attribute 's' determines the node shape here)
#G = networkx.Graph()
G = networkx.DiGraph()
# Read the CSV File
df = pd.read_csv(r'/home/priyanka/PB_WorkPlace/sigl/CCLEAN_DETAILS.csv')

# Let's start with the rows with PROCESS types
filter = df["SRC_TYPE"]=="PROCESS"
df.where(filter, inplace = True)
process = df.dropna()

# List for edges
edges = []

for index, row in process.iterrows():
    print(row)
    edge_tuple = (row['SRC'],row['DST'],{"label":row['EDGE_LABEL']})
    edges.append(edge_tuple)

# Finding Unique source nodes and destination nodes.
uni_src_process = process['SRC'].unique()
uni_dst_process = process['DST'].unique()

G.add_nodes_from(uni_src_process, s='s')
G.add_nodes_from(uni_dst_process, s='^')
G.add_edges_from(edges)



#Drawing the graph
#First obtain the node positions using one of the layouts
nodePos = networkx.layout.spring_layout(G)

#The rest of the code here attempts to automate the whole process by
#first determining how many different node classes (according to
#attribute 's') exist in the node set and then repeatedly calling 
#draw_networkx_node for each. Perhaps this part can be optimised further.

#Get all distinct node classes according to the node shape attribute
nodeShapes = set((aShape[1]["s"] for aShape in G.nodes(data = True)))

#For each node class...
node_list = []
for aShape in nodeShapes:
    #...filter and draw the subset of nodes with the same symbol in the positions that are now known through the use of the layout.
    for node in G.nodes(data=True):
        if node[1]["s"] == aShape:
            node_list.append(node[0])
    networkx.draw_networkx(G, nodePos, node_shape = aShape, nodelist = node_list, **options,with_labels = True)
    node_list.clear()

#Finally, draw the edges between the nodes
networkx.draw_networkx_edges(G,nodePos)

#And show the final result
pylab.show()