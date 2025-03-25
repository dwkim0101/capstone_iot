from tkinter import *
from TelosAirSAMDBoardFlashGUI.ui.widgets.window import MainWindow


# Need to call these to run the code in them
from TelosAirSAMDBoardFlashGUI.callbacks.refresh_button import *
from TelosAirSAMDBoardFlashGUI.callbacks.check_bootloader import *
from TelosAirSAMDBoardFlashGUI.callbacks.flash import *

class TelosAirApp(Tk):
    def __init__(self):
        super().__init__()
        self.title("TelosAir QT-Py Flash Utility")

        mw = MainWindow(self)
        mw.pack()