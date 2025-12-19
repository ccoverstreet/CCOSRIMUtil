from PyQt6 import QtWidgets
from PyQt6.QtGui import QFont
import matplotlib.pyplot as plt
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg, NavigationToolbar2QT
from matplotlib.figure import Figure
from . import srim

class ElementComboBox(QtWidgets.QWidget):
    def __init__(self, selected_element="H"):
        super().__init__()

        self.layout = QtWidgets.QVBoxLayout()

        self.combobox = QtWidgets.QComboBox()
        self.combobox.setFont(QFont("Monospace"))
        self.combobox.setMinimumHeight(30)
        for sym in srim.ELEM_DICT:
            elem = srim.ELEM_DICT[sym]
            self.combobox.addItem(f"{elem.atomic_number:2} {sym:2} {elem.name:20}", sym)

        ind = self.combobox.findData(selected_element)
        self.combobox.setCurrentIndex(ind)

        self.layout.addWidget(self.combobox)

        self.setLayout(self.layout)

    def getSymbol(self):
        return self.combobox.currentData()


class MplCanvas(FigureCanvasQTAgg):
    def __init__(self, parent=None, width=5, height=4, dpi=100):
        layout = QtWidgets.QVBoxLayout()
        fig = Figure(figsize=(width, height), dpi=dpi)
        self.axes = fig.add_subplot(111)
        self.fig = fig
        super(MplCanvas, self).__init__(fig)

    def update_plot(self):
        self.fig.canvas.draw()
        self.fig.canvas.flush_events()

class PlotTab(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.canvas = MplCanvas()
        self.fig = self.canvas.fig
        self.axes = self.canvas.axes
        self.toolbar = NavigationToolbar2QT(self.canvas)

        layout = QtWidgets.QVBoxLayout()

        layout.addWidget(self.toolbar)
        layout.addWidget(self.canvas)
        self.setLayout(layout)

    def update_plot(self):
        self.canvas.update_plot()
