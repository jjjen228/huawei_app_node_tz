from PyQt5 import QtWidgets, QtGui, QtCore
import json
from math import atan2, degrees, cos, sin, radians


class NoteGraphApp(QtWidgets.QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Note Graph App")
        self.setGeometry(100, 100, 1000, 800)
        self.graph_widget = GraphWidget(self)
        self.initUI()

    def initUI(self):
        self.toolbar = self.addToolBar("Tools")
        self.toolbar.setMovable(False)
        self.toolbar.setStyleSheet("""
            QToolBar {
                background-color: #3F51B5;
                padding: 5px;
                border: none;
            }
            QToolButton {
                background-color: #5C6BC0;
                color: white;
                font: bold 14px;
                padding: 8px 12px;
                border-radius: 5px;
                margin: 3px;
            }
            QToolButton:hover {
                background-color: #7986CB;
            }
            QToolButton:pressed {
                background-color: #3949AB;
            }
        """)

        add_node_action = QtWidgets.QAction("Add Node", self)
        add_node_action.triggered.connect(self.graph_widget.add_node)
        self.toolbar.addAction(add_node_action)

        connect_nodes_action = QtWidgets.QAction("Connect Nodes", self)
        connect_nodes_action.triggered.connect(self.graph_widget.connect_nodes)
        self.toolbar.addAction(connect_nodes_action)

        delete_element_action = QtWidgets.QAction("Delete Element", self)
        delete_element_action.triggered.connect(self.graph_widget.delete_element)
        self.toolbar.addAction(delete_element_action)

        self.setCentralWidget(self.graph_widget)

        self.color_menu = ColorMenu(self.graph_widget)
        dock = QtWidgets.QDockWidget("Settings", self)
        dock.setWidget(self.color_menu)
        dock.setAllowedAreas(QtCore.Qt.RightDockWidgetArea)
        self.addDockWidget(QtCore.Qt.RightDockWidgetArea, dock)

        self.load_notes()

    def load_notes(self):
        try:
            with open("notes.json", "r") as f:
                data = json.load(f)
                self.graph_widget.load_graph(data)
        except FileNotFoundError:
            pass

    def closeEvent(self, event):
        self.save_notes()
        event.accept()

    def save_notes(self):
        data = self.graph_widget.get_graph_data()
        with open("notes.json", "w") as f:
            json.dump(data, f)


class ColorMenu(QtWidgets.QWidget):
    def __init__(self, graph_widget):
        super().__init__()
        self.graph_widget = graph_widget

        layout = QtWidgets.QVBoxLayout()

        layout.addWidget(QtWidgets.QLabel("Background Color:"))
        self.bg_color_btn = QtWidgets.QPushButton("Change Background")
        self.bg_color_btn.clicked.connect(self.change_background_color)
        layout.addWidget(self.bg_color_btn)

        layout.addWidget(QtWidgets.QLabel("Node Color:"))
        self.node_color_btn = QtWidgets.QPushButton("Change Node Color")
        self.node_color_btn.clicked.connect(self.change_node_color)
        layout.addWidget(self.node_color_btn)

        layout.addStretch()
        self.setLayout(layout)

    def change_background_color(self):
        color = QtWidgets.QColorDialog.getColor()
        if color.isValid():
            self.graph_widget.change_background_color(color)

    def change_node_color(self):
        color = QtWidgets.QColorDialog.getColor()
        if color.isValid():
            self.graph_widget.change_node_color(color)


class NodeItem(QtWidgets.QGraphicsEllipseItem):
    def __init__(self, text=""):
        super().__init__(-75, -75, 150, 150)
        self.default_color = QtGui.QColor("#FFCC80")
        self.setBrush(QtGui.QBrush(self.default_color))
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsMovable)
        self.setFlag(QtWidgets.QGraphicsItem.ItemIsSelectable)

        self.text_item = QtWidgets.QGraphicsTextItem(text, self)
        self.text_item.setTextInteractionFlags(QtCore.Qt.TextEditorInteraction)
        self.text_item.setDefaultTextColor(QtGui.QColor("#37474F"))
        font = QtGui.QFont("Arial", 10)
        self.text_item.setFont(font)
        self.text_item.setPos(-35, -15)

    def set_node_color(self, color):
        self.setBrush(QtGui.QBrush(color))


class EdgeItem(QtWidgets.QGraphicsPathItem):
    def __init__(self, start_item, end_item):
        super().__init__()
        self.start_item = start_item
        self.end_item = end_item
        self.setPen(QtGui.QPen(QtGui.QColor("#546E7A"), 2, QtCore.Qt.SolidLine, QtCore.Qt.RoundCap))
        self.setBrush(QtGui.QBrush(QtGui.QColor("#546E7A")))
        self.arrow_size = 10
        self.update_position()

    def update_position(self):
        start_point = self.start_item.scenePos()
        end_point = self.end_item.scenePos()

        node_radius = 75

        line_vector = end_point - start_point
        distance = (line_vector.x()**2 + line_vector.y()**2)**0.5

        if distance == 0:
            return

        unit_vector = line_vector / distance

        start_point_adjusted = start_point + unit_vector * node_radius
        end_point_adjusted = end_point - unit_vector * node_radius

        path = QtGui.QPainterPath()
        path.moveTo(start_point_adjusted)
        path.lineTo(end_point_adjusted)
        self.setPath(path)

        angle = atan2(-(end_point_adjusted.y() - start_point_adjusted.y()),
                      end_point_adjusted.x() - start_point_adjusted.x())

        arrow_p1 = end_point_adjusted + QtCore.QPointF(
            -self.arrow_size * cos(angle + radians(30)),
            self.arrow_size * sin(angle + radians(30)),
        )
        arrow_p2 = end_point_adjusted + QtCore.QPointF(
            -self.arrow_size * cos(angle - radians(30)),
            self.arrow_size * sin(angle - radians(30)),
        )

        path.moveTo(end_point_adjusted)
        path.lineTo(arrow_p1)
        path.moveTo(end_point_adjusted)
        path.lineTo(arrow_p2)

        self.setPath(path)



class GraphWidget(QtWidgets.QGraphicsView):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setScene(QtWidgets.QGraphicsScene(self))
        self.scene().setSceneRect(0, 0, 800, 600)
        self.setRenderHint(QtGui.QPainter.Antialiasing)
        self.nodes = []
        self.edges = []

        self.background_color = QtGui.QColor("#ECEFF1")
        self.setStyleSheet(f"background-color: {self.background_color.name()};")
        

    def change_background_color(self, color):
        self.background_color = color
        self.setStyleSheet(f"background-color: {self.background_color.name()};")

    def change_node_color(self, color):
        for node in self.nodes:
            node.set_node_color(color)

    def add_node(self):
        node = NodeItem("New Node")
        self.scene().addItem(node)
        node.setPos(150, 150)
        self.nodes.append(node)

    def connect_nodes(self):
        selected_nodes = [node for node in self.nodes if node.isSelected()]
        if len(selected_nodes) == 2:
            start, end = selected_nodes
            edge = EdgeItem(start, end)
            self.scene().addItem(edge)
            self.edges.append(edge)

    def delete_element(self):
        items_to_delete = self.scene().selectedItems()

        for item in items_to_delete:
            if isinstance(item, NodeItem):
                connected_edges = [edge for edge in self.edges if edge.start_item == item or edge.end_item == item]
                for edge in connected_edges:
                    self.edges.remove(edge)
                    self.scene().removeItem(edge)

        for item in items_to_delete:
            if isinstance(item, NodeItem):
                self.nodes.remove(item)
            elif isinstance(item, EdgeItem):
                self.edges.remove(item)
            self.scene().removeItem(item)

    def load_graph(self, data):
        for node_data in data.get("nodes", []):
            node = NodeItem(node_data["text"])
            node.setPos(node_data["x"], node_data["y"])
            self.scene().addItem(node)
            self.nodes.append(node)
        for edge_data in data.get("edges", []):
            start_node = self.nodes[edge_data["start"]]
            end_node = self.nodes[edge_data["end"]]
            edge = EdgeItem(start_node, end_node)
            self.scene().addItem(edge)
            self.edges.append(edge)

    def get_graph_data(self):
        data = {"nodes": [], "edges": []}
        for node in self.nodes:
            data["nodes"].append({
                "x": node.scenePos().x(),
                "y": node.scenePos().y(),
                "text": node.text_item.toPlainText()
            })
        for edge in self.edges:
            if edge.start_item in self.nodes and edge.end_item in self.nodes:
                data["edges"].append({
                    "start": self.nodes.index(edge.start_item),
                    "end": self.nodes.index(edge.end_item)
                })
        return data

    def mousePressEvent(self, event):
        super().mousePressEvent(event)
        for edge in self.edges:
            edge.update_position()

    def mouseMoveEvent(self, event):
        super().mouseMoveEvent(event)
        for edge in self.edges:
            edge.update_position()

    def wheelEvent(self, event):
        zoom_in_factor = 1.25
        zoom_out_factor = 1 / zoom_in_factor

        if event.angleDelta().y() > 0:
            scale_factor = zoom_in_factor
        else:
            scale_factor = zoom_out_factor

        cursor_pos = self.mapToScene(event.pos())

        self.scale(scale_factor, scale_factor)

        new_viewport_center = self.mapToScene(self.viewport().rect().center())
        delta = cursor_pos - new_viewport_center
        self.centerOn(self.mapToScene(self.viewport().rect().center()) + delta)


if __name__ == "__main__":
    import sys
    app = QtWidgets.QApplication(sys.argv)
    mainWin = NoteGraphApp()
    mainWin.show()
    sys.exit(app.exec_())
