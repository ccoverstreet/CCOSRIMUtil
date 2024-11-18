from .ccosrimutil_gui import MainWindow
from PyQt6 import QtWidgets
import sys

print("Launching CCO SRIM Utility GUI")
app = QtWidgets.QApplication(sys.argv)
w = MainWindow()
app.exec()



