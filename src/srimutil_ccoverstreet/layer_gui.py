from PyQt6 import QtWidgets
from PyQt6.QtCore import pyqtSignal as Signal
from PyQt6.QtCore import Qt,QSize 
from PyQt6.QtGui import QFont
from dataclasses import dataclass
from . import util_gui
from . import chemicalparser
from . import srim

class LayerPage(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.master_layout = QtWidgets.QHBoxLayout()

        self.input_box = QtWidgets.QVBoxLayout()

        self.setup_form = LayerForm()
        self.ion_form = IonConfigForm()
        self.run_srim_layer_button = QtWidgets.QPushButton("Run SRIM")
        self.run_srim_layer_button.clicked.connect(self.run_srim_layer)

        self.input_box.addWidget(self.setup_form)
        self.input_box.addWidget(self.ion_form)
        self.input_box.addWidget(self.run_srim_layer_button)


        self.PLACEHOLDER = QtWidgets.QLabel("ASDASDASD")

        self.master_layout.addLayout(self.input_box)
        self.master_layout.addWidget(self.PLACEHOLDER)

        self.setLayout(self.master_layout)

    def run_srim_layer(self):

        srim_dirname_parts = QtWidgets.QFileDialog.getExistingDirectory(self, 'Save SRIM Output Table')

        if srim_dirname_parts == "":
            return


        ion = self.ion_form.getIonConfig()

        layers = self.setup_form.get_layers()
        print(ion, layers)

        srim.run_srim_layered(ion, layers, srim_dirname_parts)
        

class LayerForm(QtWidgets.QWidget):

    def __init__(self):
        super().__init__()

        column_layout = QtWidgets.QVBoxLayout()

        controls_layout = QtWidgets.QHBoxLayout()

        self.add_layer_button = QtWidgets.QPushButton("Add Layer")
        self.add_layer_button.clicked.connect(self.add_layer)

        self.delete_layer_button = QtWidgets.QPushButton("Delete Layer")
        self.delete_layer_button.clicked.connect(self.delete_layer)

        self.layer_list = QtWidgets.QListWidget()

        controls_layout.addWidget(self.add_layer_button)
        controls_layout.addWidget(self.delete_layer_button)

        column_layout.addLayout(controls_layout)
        column_layout.addWidget(self.layer_list)

        self.setLayout(column_layout)

    def add_layer(self):
        new_item = QtWidgets.QListWidgetItem()
        new_item.setSizeHint(QSize(30, 60))
        self.layer_list.addItem(new_item)
        self.layer_list.setItemWidget(new_item, LayerItem())

    def delete_layer(self):
        items = self.layer_list.selectedItems()
        for x in items:
            row = self.layer_list.indexFromItem(x)
            wid = self.layer_list.takeItem(row.row())
            del wid

    def get_layers(self):
        layers = []
        for i in range(0, self.layer_list.count()):
            item = self.layer_list.item(i)
            widget = self.layer_list.itemWidget(item)
            layers.append(widget.get_layer_data())

        return layers

class LayerItem(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()
        self.layout = QtWidgets.QHBoxLayout()

        self.formula_entry = QtWidgets.QLineEdit()
        self.formula_entry.setText("Al")

        self.density_entry = QtWidgets.QDoubleSpinBox()
        self.density_entry.setValue(2.70)
        self.density_entry.setDecimals(6)
        self.density_entry.setMinimum(0.000001)

        self.density_unit = QtWidgets.QLabel("g/cm<sup>3</sup>")

        self.thickness_entry = QtWidgets.QDoubleSpinBox()
        self.thickness_entry.setValue(1.0)
        self.thickness_entry.setDecimals(6)
        self.thickness_entry.setMinimum(0.000001)
        self.thickness_entry.setMaximum(1E6)

        self.thickness_unit = QtWidgets.QLabel("μm")

        self.layout.addWidget(self.formula_entry)
        self.layout.addWidget(self.density_entry)
        self.layout.addWidget(self.density_unit)
        self.layout.addWidget(self.thickness_entry)
        self.layout.addWidget(self.thickness_unit)

        self.setLayout(self.layout)

    def get_layer_data(self):
        parsed = chemicalparser.parse_formula(self.formula_entry.text())
        elems = list(map(lambda x: srim.ELEM_DICT[x[0]], parsed))
        stoichs = list(map(lambda x: x[1], parsed))

        return srim.SRIMLayer(
            srim.TargetType.SOLID,
            self.density_entry.value(),
            1,
            stoichs,
            elems,
            self.thickness_entry.value(),
            self.formula_entry.text()
        )




class IonConfigForm(QtWidgets.QWidget):
    def __init__(self):
        super().__init__()

        self.input_layout = QtWidgets.QVBoxLayout()

        self.setMaximumWidth(500)

        self.ion_row = QtWidgets.QHBoxLayout()
        self.combo_label = QtWidgets.QLabel("Ion:")
        self.ionbox = util_gui.ElementComboBox()

        self.ion_row.addWidget(self.combo_label)
        self.ion_row.addWidget(self.ionbox)

        self.max_energy_row = QtWidgets.QHBoxLayout()
        self.max_energy_label = QtWidgets.QLabel("Energy (keV)")
        self.max_energy_input = QtWidgets.QDoubleSpinBox()
        self.max_energy_input.setMinimum(10)
        self.max_energy_input.setMaximum(1E9)
        self.max_energy_input.setValue(1000)
        self.max_energy_row.addWidget(self.max_energy_label)
        self.max_energy_row.addWidget(self.max_energy_input)

        self.input_layout.addLayout(self.ion_row)
        self.input_layout.addLayout(self.max_energy_row)

        self.setLayout(self.input_layout)

    def getIonConfig(self):
        return srim.IonConfigLayer(srim.ELEM_DICT[self.ionbox.getSymbol()], self.max_energy_input.value())


