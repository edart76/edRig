# show the tesserae window
from PySide2 import QtWidgets

from . import window



def start():
    m = window.TilePileUI()
    m.show()
    return m

def main():
    app = QtWidgets.QApplication.instance()
    window = start()
    return window

if __name__ == "__main__":
    eyy = main()
