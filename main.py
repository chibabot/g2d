import math
import sys
import json
import csv

from os import getcwd

from PySide6.QtCore import (QLineF,QPointF,QRectF, Qt, Signal, Slot)
from PySide6.QtGui import QBrush, QColor, QKeySequence, QPainter, QPen, QPolygonF, QShortcut, QMouseEvent
from PySide6.QtWidgets import (QApplication, QFileDialog, QHBoxLayout, QGraphicsItem, QGraphicsSceneMouseEvent,
                               QGraphicsObject, QGraphicsScene, QGraphicsView,QStatusBar,
                               QStyleOptionGraphicsItem, QPushButton, QTableWidget, QTableWidgetItem, QVBoxLayout, QWidget)


class Node(QGraphicsObject):
    """A QGraphicsItem representing node in a graph"""
    def __init__(self, name: str, textcolor="white", color="#5AD469", data={}, parent=None):
        """Node constructor

        Args:
            name (str): Node label
            textcolor (any): Text color
            color (any): Color for ellipse
            data (dict): Other stuff
        """
        super().__init__(parent)
        self._name = name
        self._data = data
        self._edges = []
        self._textcolor = textcolor
        self._color = color
        self._radius = 30
        self._rect = QRectF(0, 0, self._radius * 2, self._radius * 2)
        self.setFlag(QGraphicsItem.ItemIsMovable)
        self.setFlag(QGraphicsItem.ItemSendsGeometryChanges)
        self.setCacheMode(QGraphicsItem.DeviceCoordinateCache)

    def reload(self,data:dict):
        self._name=data["name"]
        self._color=data["color"]
        self._textcolor=data["textcolor"]
        self._data=data["data"] # data["data"] -> dict
        self.update()

    def get(self) -> dict:
        """Gets dictionary for class Node
        
        Returns:
            dict: {name,color,textcolor,pos,data}
        """
        return {
            "name":self._name,
            "edges":self.get_edges(),
            "color":self._color,
            "textcolor":self._textcolor,
            "pos":self.scenePos().toTuple(),
            "data":self._data}
    def get_edges(self):
        edges=[]
        for i in self._edges:
            if i not in edges:
                edges.append([i._source._name,i._dest._name])
        return edges

    def boundingRect(self) -> QRectF:
        """Override from QGraphicsItem

        Returns:
            QRect: Return node bounding rect
        """
        return self._rect

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget: QWidget = None):
        """Override from QGraphicsItem

        Draw node

        Args:
            painter (QPainter)
            option (QStyleOptionGraphicsItem)
        """
        painter.setRenderHints(QPainter.Antialiasing)
        painter.setPen(
            QPen(
                QColor(self._color).darker(),
                2,
                Qt.SolidLine,
                Qt.RoundCap,
                Qt.RoundJoin,
            )
        )
        painter.setBrush(QBrush(QColor(self._color)))
        painter.drawEllipse(self.boundingRect())
        painter.setPen(QPen(QColor(self._textcolor)))
        painter.drawText(self.boundingRect(), Qt.AlignCenter, str(self._name))

    def add_edge(self, edge):
        """Add an edge to this node

        Args:
            edge (Edge)
        """
        if len(self._edges)==0:
            self._edges.append(edge)
        target=[edge._source._name,edge._dest._name]
        if target not in self.get_edges() and target not in edge._dest.get_edges():
            self._edges.append(edge)

    def del_edge(self, edge):
        """Delete edge from this node

        Args:
            edge (Edge)
        """
        for e in self._edges:
            if edge._source==e._source and edge._dest==e._dest:
                self._edges.remove(e)

    def itemChange(self, change: QGraphicsItem.GraphicsItemChange, value):
        """Override from QGraphicsItem

        Args:
            change (QGraphicsItem.GraphicsItemChange)
            value (Any)

        Returns:
            Any
        """
        if change == QGraphicsItem.ItemPositionHasChanged:
            for edge in self._edges:
                edge.adjust()

        return super().itemChange(change, value)
    
    def setColor(self, color: QColor):
        """
        Sets color of Node (not text color)
        
        Args:
            color (QColor): New color for change node background color 
        """
        self._color=color
        self.update()

    def setPosition(self, pos):
        """
        Sets position from QPoint on scene

        Args:
            pos(
        """
        x=pos.x()-self._radius
        y=pos.y()-self._radius
        self.setPos(QPointF(x, y))

class Edge(QGraphicsItem):
    def __init__(self, source: Node, dest: Node, parent: QGraphicsItem = None):
        """Edge constructor

        Args:
            source (Node): source node
            dest (Node): destination node
        """
        super().__init__(parent)
        self._source = source
        self._dest = dest

        self._tickness = 2
        self._color = "#2BB53C"
        self._arrow_size = 10

        self._source.add_edge(self)
        self._dest.add_edge(self)

        self._line = QLineF()
        self.setZValue(-1)
        self.adjust()

    def delete(self):
        """Removing edge from nodes"""
        self._source.del_edge(self)
        self._dest.del_edge(self)

    def boundingRect(self) -> QRectF:
        """Override from QGraphicsItem

        Returns:
            QRect: Return node bounding rect
        """
        return (
            QRectF(self._line.p1(), self._line.p2())
            .normalized()
            .adjusted(
                -self._tickness - self._arrow_size,
                -self._tickness - self._arrow_size,
                self._tickness + self._arrow_size,
                self._tickness + self._arrow_size,
            )
        )

    def adjust(self):
        """
        Update edge position from source and destination node.
        This method is called from Node::itemChange
        """
        self.prepareGeometryChange()
        self._line = QLineF(
            self._source.pos() + self._source.boundingRect().center(),
            self._dest.pos() + self._dest.boundingRect().center(),
        )

    def _draw_arrow(self, painter: QPainter, start: QPointF, end: QPointF):
        """Draw arrow from start point to end point.

        Args:
            painter (QPainter)
            start (QPointF): start position
            end (QPointF): end position
        """
        painter.setBrush(QBrush(self._color))

        line = QLineF(end, start)

        angle = math.atan2(-line.dy(), line.dx())
        arrow_p1 = line.p1() + QPointF(
            math.sin(angle + math.pi / 3) * self._arrow_size,
            math.cos(angle + math.pi / 3) * self._arrow_size,
        )
        arrow_p2 = line.p1() + QPointF(
            math.sin(angle + math.pi - math.pi / 3) * self._arrow_size,
            math.cos(angle + math.pi - math.pi / 3) * self._arrow_size,
        )

        arrow_head = QPolygonF()
        arrow_head.clear()
        arrow_head.append(line.p1())
        arrow_head.append(arrow_p1)
        arrow_head.append(arrow_p2)
        painter.drawLine(line)
        painter.drawPolygon(arrow_head)

    def _arrow_target(self) -> QPointF:
        """Calculate the position of the arrow taking into account the size of the destination node

        Returns:
            QPointF
        """
        target = self._line.p1()
        center = self._line.p2()
        radius = self._dest._radius
        vector = target - center
        length = math.sqrt(vector.x() ** 2 + vector.y() ** 2)
        if length == 0:
            return target
        normal = vector / length
        target = QPointF(center.x() + (normal.x() * radius), center.y() + (normal.y() * radius))

        return target

    def paint(self, painter: QPainter, option: QStyleOptionGraphicsItem, widget=None):
        """Override from QGraphicsItem

        Draw Edge. This method is called from Edge.adjust()

        Args:
            painter (QPainter)
            option (QStyleOptionGraphicsItem)
        """

        if self._source and self._dest:
            painter.setRenderHints(QPainter.Antialiasing)

            painter.setPen(
                QPen(
                    QColor(self._color),
                    self._tickness,
                    Qt.SolidLine,
                    Qt.RoundCap,
                    Qt.RoundJoin,
                )
            )
            painter.drawLine(self._line)
            self._draw_arrow(painter, self._line.p1(), self._arrow_target())
            self._arrow_target()

class TableNode(QWidget):
    def __init__(self, node:Node, parent=None):
        """ TableNode constructor

        Widget that displays selected node data

        Args:
            node (Node): Selected node from GraphView scene  
        
        """
        super(TableNode, self).__init__(parent)
        
        self.node=node
        self.setWindowTitle(self.node._name)
        self.table = QTableWidget()
        self._nodeData={"data":{}}

        nodeData={"name":self.node._name,
                  "color":self.node._color,
                  "textcolor":self.node._textcolor}
        nodeData.update(self.node._data)
        
        if self.table.rowCount()==0:
            self.table.setRowCount(len(nodeData)+1)
            self.table.setColumnCount(2)
            self.table.setHorizontalHeaderLabels(["Ключ","Значение"])
            self.init_table(nodeData)
        
        self.table.itemChanged.connect(self.change_celldata)
        self.table.itemClicked.connect(self.append_row)
        
        layout = QVBoxLayout(self)
        layout.addWidget(self.table)
        
    def init_table(self,nodeData: dict):
        """
        Init table with default node data
        
        Args:
            nodeData (dict): Dictionary with nodes cooked data
        """
        for i,(k,v) in enumerate(nodeData.items()):
            if 0<=i<=2:
                item=QTableWidgetItem(k)
                item.setFlags(Qt.ItemFlag.ItemIsEnabled|Qt.ItemFlag.ItemIsSelectable)
                self.table.setItem(i,0,item)
            else:
                self.table.setItem(i,0,QTableWidgetItem(k))
                
            self.table.setItem(i,1,QTableWidgetItem(v))
            self.table.setItem(i+1,0,QTableWidgetItem(str("")))
            self.table.setItem(i+1,1,QTableWidgetItem(str("")))
            
    def append_row(self, item: QTableWidgetItem):
        """
        Appends last row in table with default QTableWidgetItem str
        
        Args:
            item (QTableWidgetItem): Current item that was clicked
        """
        rows=self.table.rowCount()
        
        if item.row()+1==rows:
            self.table.insertRow(rows)
            self.table.setItem(rows,0,QTableWidgetItem(""))
            self.table.setItem(rows,1,QTableWidgetItem(""))
            
    def change_celldata(self, item: QTableWidgetItem):
        """
        Disable name, color and text color cells editable (avoid crashes when apply node data)
        Realtime changing nodes data and reload it into node class
        
        Args:
            item (QTableWidgetItem): Changed item in table
        """
        rows=self.table.rowCount()
        
        for i in range(0,rows):
            if i==1:
                self.setWindowTitle(self.table.item(0,1).text())
                
            if i<=2 and self.table.item(i,0) != None and self.table.item(i,1) != None:
                self._nodeData[self.table.item(i,0).text()] = self.table.item(i,1).text()
                
            elif self.table.item(i,0) != None and self.table.item(i,1) != None:
                if self.table.item(i,0).text() != "":
                    self._nodeData["data"][self.table.item(i,0).text()] = self.table.item(i,1).text()
                    
        self.node.reload(self._nodeData)
        
class GraphView(QGraphicsView):
    def __init__(self, fileName:str=None, parent=None):
        """GraphView constructor

        This widget can display a directed graph

        Args:
            graph (nx.DiGraph): A networkx directed graph
            fileName (str): Filename for save/load scene
        """
        super().__init__()
        self._status=QStatusBar()
        self._file=fileName
        self._selectedNode = None
        self._scene = QGraphicsScene()
        self.setScene(self._scene)

        # Map node name to Node object {str=>Node}
        self._nodes_map = {}
        
    def mouseDoubleClickEvent(self, event: QMouseEvent) -> None:
        """
        Gestures for editing is in ReadMe.md 
        """
        
        button=event.button()
        
        match(button):
            case (button.LeftButton): #Adds Nodes and Edges on empty scene (if edge exists -> delete edge)
                
                p=event.position().toPoint()
                
                if self.itemAt(p):
                    
                    item=self.itemAt(p)
                    
                    if self._selectedNode == None and type(item) is Node: # But if on Node it will be selected
                        
                        #Selects the node
                        self._selectedNode=self.itemAt(p)
                        
                        self._status.showMessage("Selected Node: "+self._selectedNode._name)
                        
                    elif self._selectedNode!=item and type(item) is Node: # If node is already selected -> create edge
                        
                        #Finding selected->target in their edges by making compare list
                        edg=[i for i in self._selectedNode._edges if i in item._edges]
                        
                        if edg==[]:
                            
                            #If node isn't in compare list
                            edg=Edge(self._selectedNode,item)
                            self.scene().addItem(edg)
                            
                            self._selectedNode=None
                            
                            self._status.showMessage(str(edg._source._name)+"->"+str(edg._dest._name)+" added.")
                            
                        else:
                            
                            #Checks Node in selected node and target node to avoid the edge duplicates
                            if [self._selectedNode._name,item._name] not in [[x._source._name,x._dest._name] for x in edg]:
                                
                                edg=Edge(self._selectedNode,item)
                                self.scene().addItem(edg)

                                self._selectedNode=None

                                self._status.showMessage(str(edg._source._name)+"->"+str(edg._dest._name)+" added.")
                                
                            else:
                                
                                #Edge is about to delete
                                edg=edg[0]
                                edg.delete()

                                self.scene().removeItem(edg)

                                self._selectedNode=None

                                self._status.showMessage(str(edg._source._name)+"->"+str(edg._dest._name)+" deleted.")
                else:

                    #Add node on scene. Node name is counted nodes items on scene
                    self._selectedNode=None
                    nodes_count=sum([1 for x in self._scene.items() if isinstance(x, Node)])

                    n=Node(str(nodes_count+1))
                    n.setPosition(self.mapToScene(p))
                    
                    self._scene.addItem(n)
                    
                    self._status.showMessage("Added Node: "+n._name)
                    
            case (button.RightButton): #Gets data of Node
                
                p=event.position().toPoint()
                s=event.globalPosition().toPoint()
                
                if self.itemAt(p) and type(self.itemAt(p)) is Node:
                    
                    item=self.itemAt(p)
                    self.tableData=TableNode(item)
                    
                    self.tableData.adjustSize()
                    self.tableData.move(s.x()-320,s.y()-120)
                    
                    self.tableData.show()
                    
            case (button.MiddleButton): #Disable selected Node
                
                p=event.position().toPoint()
                
                if self.itemAt(p) and type(self.itemAt(p)) is Node and self._selectedNode==self.itemAt(p):
                    
                    self._selectedNode=None
                    self._status.showMessage("Selected Node: None")
                    
    def load_graph(self):
        """
        Load graph from self._file
        else nothing happen
        """
        if len(self._file)<=3:
            
            self._status.showMessage("File "+self._file+" is corrupted.")
            return None
        
        edge_map=[]
        self.scene().clear()
        self._nodes_map.clear()
        
        with open(self._file, "r", encoding='utf-8') as file:
            dumpdata = json.load(file)
            
        for node in dumpdata:
            for e in node['edges']:
                if e not in edge_map:
                    edge_map.append(e)
                    
            n=Node(node['name'],node['textcolor'],node['color'],node['data'])
            n.setPos(node['pos'][0],node['pos'][1])
            self._nodes_map[n._name]=n
            self.scene().addItem(n)
            
        for s,d in edge_map:
            
            source = self._nodes_map[s]
            dest = self._nodes_map[d]
            self.scene().addItem(Edge(source, dest))
            
        self._status.showMessage("File "+self._file+" opened.")
        
    def save_graph(self) -> list:
        
        savegraph=[]
        
        for item in self.scene().items():
            if type(item)==Node:
                savegraph.append(item.get())
                
        return (savegraph)
    
class MainWindow(QWidget):
    def __init__(self, parent=None):
        
        super().__init__()
        """Inits"""
        self.view = GraphView()

        self.status = QStatusBar(self)
        self.view._status=self.status
        
        """"Hotkeys"""
        self.fastload = QShortcut(QKeySequence("Ctrl+F"),self)
        self.fastload.activated.connect(self.currentLoad)

        self.fastsave = QShortcut(QKeySequence("Ctrl+S"),self)
        self.fastsave.activated.connect(self.quickSave)
        """Buttons"""
        self.button1 = QPushButton("Open")
        self.button1.clicked.connect(self.load)

        self.button2 = QPushButton("Save")
        self.button2.clicked.connect(self.save)
        """Layouts"""
        h_layout = QHBoxLayout()
        h_layout.addWidget(self.button1)
        h_layout.addWidget(self.button2)
        v_layout = QVBoxLayout(self)
        v_layout.addLayout(h_layout)
        v_layout.addWidget(self.view)
        v_layout.addWidget(self.status)
        
    def currentLoad(self):
        """
        Function for QuickLoad hotkey
        """
        
        #File must be not None
        self.view.load_graph()
        self.status.showMessage("File "+self.view._file+" quickloaded.")
        
    def quickSave(self):
        """
        Function for QuickSave hotkey
        """
        
        #File must be not None
        if len(self.view._file)>=3:
            with open(self.view._file, "w") as file:
                json.dump(self.view.save_graph(), file, indent=3)
                
            self.status.showMessage("File "+self.view._file+" quicksaved.")
            
    def load(self):
        """
        Loads the Json file from current directory
        """
        fileName = QFileDialog.getOpenFileName(self, "Open File", getcwd(), 'Json File (*.json)')[0].split("/")[-1]
        
        if fileName!="":
            self.view._file=fileName
            self.view.load_graph()
            
    def save(self):
        """
        Saves the Json file in current directory
        """
        fileName = QFileDialog.getSaveFileName(self, "Save File", getcwd(), 'Json File (*.json)')[0].split("/")[-1]
        
        if len(fileName)>=3:
            with open(fileName, "w") as file:
                json.dump(self.view.save_graph(), file, indent=3)
                
            self.status.showMessage("File "+fileName+" saved.")
            
    def export(self):
        """TODO"""
        #Export Nodes data
        #Export Edges map
        #Maybe make TableEdge idk
        #Make the graph type setting for adding data in edges
        pass

if __name__ == "__main__":

    app = QApplication(sys.argv)
    widget = MainWindow()
    widget.show()
    widget.resize(800, 600)
    sys.exit(app.exec())
