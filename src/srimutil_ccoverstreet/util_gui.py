from PyQt6 import QtWidgets
from PyQt6.QtGui import QFont
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
