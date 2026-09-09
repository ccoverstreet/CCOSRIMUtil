from .ccosrimutil_gui import MainWindow
from PyQt6 import QtWidgets
import sys

def main():

    print("Launching CCO SRIM Utility GUI")
    app = QtWidgets.QApplication(sys.argv)
    w = MainWindow()
    app.exec()


if __name__ == "__main__":
    main()



