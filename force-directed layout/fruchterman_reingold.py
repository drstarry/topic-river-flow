#
# bioinformatics 3, wintersemester 89
# all code by Mathias Bader
# modified by Rui Dai
# add weight to each edge and fix the x of each node
#


import sys, os, string, random, time
from math import sqrt
# gives tk namespace for graphical output
import Tkinter as tk

center_distance = 10.0          # the distance from the middle of the screen to each border
scaling_factor = 1.0            # the zoom-factor (the smaller, the more surface is shown)
zooming = 0                     # is the application zooming right now?
zoom_in_border = 1.0            # limit between graph and screen-border for zooming in
zooming_out = 0
circle_diameter = 20            # the diameter of the node-circles
timestep = 0
thermal_energie = 0.0           # set this to 0.3 or 0.0 to (de)activate thermal_energie
all_energies = []               # list of all energies sorted by time
highest_energy = 0              # the highest energie occuring
energie_change_limit = 0.0000001    # if energie doesn't change more than this, process is stoped
velocity_maximum = 0.05
friction = 0.0005               # is subtracted from the velocity at each timestep for stop oscillations
show_energies_in_background = 1
status_message = ''
grabed_node = ''
grabed_component = ''
dont_finish_calculating = 1
show_energie_in_background = 1
show_textinformation_in_background = 1

#screen properties
c_width = 400
c_height = 200
border = 1


# Class for Nodes
class Node:
    def __init__(self, node_id, group):
        self.id = node_id       # id (as an integer for example)
        self.neighbour_ids = [] # list of the ids of the neighbours
        self.group = group # indicts the time,to fix x value
        self.degree = 0         # number of neighbours
        self.coordinate_x = 0
        self.coordinate_y = 0
        self.force_coulomb = 0
        self.force_harmonic = 0
        self.cc_number = 0      # the number of the connected component (0 if not assigned yet)
        self.cc_centers = []
        self.velocity = [0,0]   # instead of replacing the nodes, change its velocity to produce inertia
        self.movable = 1
    def getNeighbours(self):
        return self.neighbour_ids
    def getGroup(self):
        return self.group
    def getDegree(self):
        return self.degree
    def getId(self):
        return self.id
    def setNeighbour(self, node_id):
        self.neighbour_ids.append(node_id)
        self.degree += 1
    def deleteNeighbour(self, node_id):
        self.neighbour_ids.remove(node_id)
        self.degree -= 1

class Edge:
    def __init__(self,source,target,weight):
        self.source = source
        self.target = target
        self.weight = weight

# Class for graph
class Graph:
    def __init__(self):
        # build an empty graph
        self.nodes = [] # list of Node-objects
        self.edges = [] # list of tupels (node1-id, node2-id) where node1-id is always smaller than node2-id
        self.last_added_id = -1
        self.connected_components_count = 0
        self.overall_energie = 0
        self.overall_energie_difference = 1000
        self.calculation_finished = 0

    def addNode(self, node_id, group):
        # adds a node to the graph
        # use group to scale the x value
        if node_id == self.last_added_id:
            return    # speed up adding of same ids consecutively
        for x in self.nodes:
            if x.getId() == node_id:
                return
        self.nodes.append(Node(node_id, group))
        self.last_added_id = node_id

    def addEdge(self, node_id_1, node_id_2, weight):
        # adds an edge between two nodes
        # add weight of each edge
        if node_id_1 != node_id_2 and node_id_1 >= 0 and node_id_2 >= 0 and not self.isEdge(node_id_1, node_id_2):

            self.edges.append(Edge(node_id_1, node_id_2,weight))
            # search for the two node-objects with fitting ids
            node1 = self.getNode(node_id_1)
            node2 = self.getNode(node_id_2)
            node1.setNeighbour(node_id_2)
            node2.setNeighbour(node_id_1)

    def deleteEdge(self, (node_id_1, node_id_2)):
        # deletes the edge between node_id_1 and node_id_2
        if node_id_1 > node_id_2:
            # switch the two node-ids (edges are always saved with smaller id first)
            tmp = node_id_1
            node_id_1 = node_id_2
            node_id_2 = tmp
        self.edges.remove((node_id_1, node_id_2))
        node1 = self.getNode(node_id_1)
        node1.deleteNeighbour(node_id_2)
        node2 = self.getNode(node_id_2)
        node2.deleteNeighbour(node_id_1)

    def nodesList(self):
        # returns the list of ids of nodes
        list_of_ids = []
        for node in self.nodes:
            list_of_ids.append(node.id)
        return list_of_ids

    def edgesList(self):
        # returns the list of edges ([(id, id), (id, id), ...]
        return self.edges

    def degreeList(self):
        # returns a dictionary with the degree distribution of the graph
        degrees = {}
        for x in self.nodes:
            if degrees.has_key(x.degree):
                degrees[x.degree] += 1
            else:
                degrees[x.degree] = 1
        return degrees

    def countNodes(self):
        # prints the number of nodes
        return len(self.nodes)

    def countEdges(self):
        # prints the number of nodes
        return len(self.edges)

    def printNodes(self):
        # prints the list of nodes
        to_print = '['
        count = 0
        for x in self.nodes:
            to_print = to_print + str(x.getId()) + ','
            count += 1
            if count > 200:
                print to_print,
                to_print = ''
                count = 1
        if count > 0: to_print = to_print[:-1]
        to_print = to_print + ']'
        print to_print

    def printEdges(self):
        # prints the list of edges
        to_print = '['
        count = 0
        for (n1, n2) in self.edges:
            to_print = to_print + '(' + str(n1) + ',' + str(n2) + '), '
            count += 1
            if count > 200:
                print to_print,
                to_print = ''
                count = 1
        if count > 0: to_print = to_print[:-2]
        to_print = to_print + ']'
        print to_print

    def printData(self):
        # prints number of nodes and edges
        print 'graph with', len(self.nodes), 'nodes and', len(self.edges), 'edges'
        print
        for node in self.nodes:
            print node.id,'(',node.coordinate_x,',',node.coordinate_y,'),group:',node.group

    def saveJson(self):
        nodes = []
        links = []
        for node in self.nodes:
            nodes.append({"id":node.id,"group":node.group,"x":node.coordinate_x,"y":node.coordinate_y})
        for edge in self.edges:
            links.append({"source":edge.source,"target":edge.target,"weight":edge.weight})
        g = dict({"nodes":nodes,"links":links})
        f = open("gragh.dat",'w')


        print g

    def isEdge(self, node_id_1, node_id_2):
        if node_id_1 > node_id_2:
            # switch the two node-ids (edges are always saved with smaller id first)
            tmp = node_id_1
            node_id_1 = node_id_2
            node_id_2 = tmp
        # checks if there is an edge between two nodes
        for x in self.edges:
            if x == (node_id_1, node_id_2): return True
        return False

    def getNode(self, node_id):
        # returns the node for a given id
        for x in self.nodes:
            if x.getId() == node_id:
                return x

    def getNodes(self):
        return self.nodes

    def SetRandomNodePosition(self):
        # sets random positions for all nodes
        for node in self.nodes:
            #fix x (how to scale?)
            node.coordinate_x = (node.group * center_distance - (center_distance/2))/10
            node.coordinate_y = random.random() * center_distance - (center_distance/2)

    def paintGraph(self):
        # clear the screen
        # for c_item in c.find_all():
        #     c.delete(c_item)

        # # plot the energie vs time in the background of the window
        # if show_energie_in_background == 1:
        #     if show_energies_in_background == 1:
        #         global all_energies
        #         energies_count = len(all_energies)
        #         # only show the last 200 energies at maximum
        #         if energies_count > 200:
        #             start_point = energies_count - 200
        #         else:
        #             start_point = 0
        #         for i in range(start_point, energies_count):
        #             c.create_rectangle(border+(c_width)/(energies_count-start_point)*(i-start_point), border+c_height-(c_height/highest_energy*all_energies[i]), border + (c_width)/(energies_count-start_point)+(c_width)/(energies_count-start_point)*(i-start_point), c_height+border, fill="#eee", outline="#ddd")
        # # draw the coordinate system with the center
        # c.create_line (border, c_height/2+border, (c_width+border), c_height/2+border, fill="#EEEEEE")
        # c.create_line (c_width/2+border, border, c_width/2+border, c_height+border*2+border, fill="#EEEEEE")

        # DRAW AlL EDGES OF THE GRAPH
        for node in g.getNodes():
            # calculate position of this node
            x0 = ((node.coordinate_x*scaling_factor + (center_distance/2)) / center_distance * c_width) + border
            y0 = ((node.coordinate_y*scaling_factor + (center_distance/2)) / center_distance * c_height) + border
            # draw all the edges to neighbors of this node
            for neighbor_id in node.neighbour_ids:
                node2 = self.getNode(neighbor_id)
                if (node.id > node2.id):
                    x1 = ((node2.coordinate_x*scaling_factor + (center_distance/2)) / center_distance * c_width) + border
                    y1 = ((node2.coordinate_y*scaling_factor + (center_distance/2)) / center_distance * c_height) + border
                    # c.create_line(x0 + circle_diameter*scaling_factor / 2, y0 + circle_diameter*scaling_factor / 2, x1 + circle_diameter*scaling_factor / 2, y1 + circle_diameter*scaling_factor / 2)

        # DRAW AlL NODES OF THE GRAPH
        for node in g.getNodes():
            # calculate position of this node
            x0 = ((node.coordinate_x*scaling_factor + (center_distance/2)) / center_distance * c_width) + border
            y0 = ((node.coordinate_y*scaling_factor + (center_distance/2)) / center_distance * c_height) + border
            # draw this node
            fill_color = "AAA"
            if (node.cc_number <= 5):
                if (node.cc_number == 1):
                    fill_color = "0C0"	# green
                if (node.cc_number == 2):
                    fill_color = "00C"	# blue
                if (node.cc_number == 3):
                    fill_color = "C00"	# red
                if (node.cc_number == 4):
                    fill_color = "FF2"	# yellow
                if (node.cc_number == 5):
                    fill_color = "FFB63D"	# orange
                if node.movable == 1:
                    c.create_oval(x0, y0, x0 + circle_diameter*scaling_factor, y0 + circle_diameter*scaling_factor, fill="#" + fill_color)
                else:
                    c.create_oval(x0, y0, x0 + circle_diameter*scaling_factor, y0 + circle_diameter*scaling_factor, fill="#000")
            else:
                if (node.cc_number == 6):
                    fill_color = "FF2"	# yellow
                if (node.cc_number == 7):
                    fill_color = "00C"	# blue
                if (node.cc_number == 8):
                    fill_color = "C00"	# red
                if (node.cc_number == 9):
                    fill_color = "0C0"	# green
                if node.movable == 1:
                    c.create_rectangle(x0, y0, x0 + circle_diameter*scaling_factor, y0 + circle_diameter*scaling_factor, fill="#" + fill_color)
                else:
                    c.create_rectangle(x0, y0, x0 + circle_diameter*scaling_factor, y0 + circle_diameter*scaling_factor, fill="#000")
            # write the id under the node
            c.create_text(x0, y0 + circle_diameter*scaling_factor + 20, anchor=tk.SW, text=str(node.id))
            # c.create_text(x0, y0 + circle_diameter*scaling_factor + 40, anchor=tk.SW, text=str(node.cc_number), fill="#008800")
        c.protocol("WM_DELETE_WINDOW", c.destroy)
        c.update()

    def calculateStep(self):
        new_overall_energie = 0

        # calculate the repulsive force for each node
        for node in self.nodes:
            node.force_coulomb = [0,0]
            for node2 in self.nodes:
                if (node.id != node2.id) and (node.cc_number == node2.cc_number):
                    distance_x = node.coordinate_x - node2.coordinate_x
                    distance_y = node.coordinate_y - node2.coordinate_y
                    radius = sqrt(distance_x*distance_x + distance_y*distance_y)
                    if radius != 0:
                        vector = [distance_x/radius, distance_y/radius]
                        node.force_coulomb[0] += 0.01 * vector[0] / radius
                        node.force_coulomb[1] += 0.01 * vector[1] / radius
                        # add this force to the overall energie
                        new_overall_energie += 0.01 / radius
                    else:
                        # if the nodes lie on each other, randomly replace them a bit
                        node.force_coulomb[0] += random.random() - 0.5
                        node.force_coulomb[1] += random.random() - 0.5

        # calculate the attractive force for each node
        # which should also be scaled by the edge weight
        for node in self.nodes:
            node.force_harmonic = [0,0]
            for neighbor_id in node.neighbour_ids:
                node2 = self.getNode(neighbor_id)
                distance_x = node.coordinate_x - node2.coordinate_x
                distance_y = node.coordinate_y - node2.coordinate_y
                radius = sqrt(distance_x*distance_x + distance_y*distance_y)
                if radius != 0:
                    vector = [distance_x/radius* -1, distance_y/radius * -1]
                    force_harmonic_x = vector[0] *radius*radius/100
                    force_harmonic_y = vector[1] *radius*radius/100
                else:
                    # if the nodes lie on each other, randomly replace them a bit
                    force_harmonic_x = random.random() - 0.5
                    force_harmonic_y = random.random() - 0.5
                node.force_harmonic[0] += force_harmonic_x
                node.force_harmonic[1] += force_harmonic_y
                # add this force to the overall energie
                new_overall_energie += radius*radius/100

        # calculate the difference between the old and new overall energie
        self.overall_energie_difference = self.overall_energie - new_overall_energie
        self.overall_energie = new_overall_energie
        all_energies.append(self.overall_energie)
        global highest_energy
        if self.overall_energie > highest_energy:
            highest_energy = self.overall_energie
        if not dont_finish_calculating:
            if (self.overall_energie_difference < energie_change_limit and self.overall_energie_difference > -1*energie_change_limit):
                self.calculation_finished = 1

        # set the new position influenced by the force
        # global thermal_energie
        # if timestep == 50 and thermal_energie > 0:
        #     thermal_energie = 0.2
        # if timestep == 110 and thermal_energie > 0:
        #     thermal_energie = 0.1
        # if timestep == 150 and thermal_energie > 0:
        #     thermal_energie = 0.0
        # for node in self.nodes:
        #     (force_coulomb_x, force_coulomb_y) = node.force_coulomb
        #     (force_harmonic_x, force_harmonic_y) = node.force_harmonic
        #     # node.coordinate_x += force_coulomb_x + force_harmonic_x
        #     # node.coordinate_y += force_coulomb_y + force_harmonic_y
        #
        #     node.velocity[0] += (force_coulomb_x + force_harmonic_x)*0.1
        #     node.velocity[1] += (force_coulomb_y + force_harmonic_y)*0.1
        #     # ensure maximum velocity
        #     if (node.velocity[0] > velocity_maximum):
        #         node.velocity[0] = velocity_maximum
        #     if (node.velocity[1] > velocity_maximum):
        #         node.velocity[1] = velocity_maximum
        #     if (node.velocity[0] < -1*velocity_maximum):
        #         node.velocity[0] = -1*velocity_maximum
        #     if (node.velocity[1] < -1*velocity_maximum):
        #         node.velocity[1] = -1*velocity_maximum
        #     # get friction into play
        #     if node.velocity[0] > friction:
        #         node.velocity[0] -= friction
        #     if node.velocity[0] < -1*friction:
        #         node.velocity[0] += friction
        #     if node.velocity[1] > friction:
        #         node.velocity[1] -= friction
        #     if node.velocity[1] < -1*friction:
        #         node.velocity[1] += friction

            # FINALLY SET THE NEW POSITION
            if node.id != grabed_node or node.cc_number == grabed_component:
                if node.movable == 1:
                    # node.coordinate_x += node.velocity[0]
                    node.coordinate_y += node.velocity[1]

            if thermal_energie > 0:
                if node.movable == 1:
                    # node.coordinate_x += random.random()*thermal_energie*2-thermal_energie
                    node.coordinate_y += random.random()*thermal_energie*2-thermal_energie


if __name__ == '__main__':
    g = Graph()
    try:
        f1 = open("topic.dat", 'r')
        rows = f1.readlines()
        f1.close()
    except IOError:
        print "topic.dat", 'could not be opened'
        sys.exit(1)

    for line in rows:
        new_line = line.strip()
        line_array = new_line.split()
        if len(line_array) == 2:
            (node, group) = line_array
            g.addNode(node, float(group))
        if len(line_array) == 3:
            (node_1, node_2, weight) = line_array
            g.addEdge(node_1, node_2, weight)

    g.SetRandomNodePosition()

    # create the window object for painting the graph on
    c = tk.Tk()


    # make it cover the entire screen
    #w, h = root.winfo_screenwidth(), root.winfo_screenheight()
    # root.overrideredirect(1)
    # root.geometry("%dx%d+0+0" % (c_width,c_height))

    # c_width = w - border*2
    # c_height = h - border*2

    # root.title("Force directed layout of graphs ")
    # c = tk.Canvas(root, width=c_width+2*border, height=c_height+2*border, bg='white')

    # g.paintGraph()
    # while (not g.calculation_finished or dont_finish_calculating):
    for i in range(1,200):
        g.calculateStep()
        print timestep
        timestep += 1
        # g.paintGraph()
    g.paintGraph()
    c.mainloop()

    g.printData()

    g.saveJson()
