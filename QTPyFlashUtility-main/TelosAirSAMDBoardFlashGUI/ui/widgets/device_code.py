from tkinter import *
import tkinter.ttk as ttk

from TelosAirSAMDBoardFlashGUI.context import CONTEXT
from TelosAirSAMDBoardFlashGUI.util.files import DEVICE_FILE_NICKNAMES

class DeviceCodeWidget(LabelFrame):
    class DeviceCodeListBox(Listbox):
        def __init__(self, master):
            super().__init__(master=master, exportselection=0)
            for i, fn in enumerate(DEVICE_FILE_NICKNAMES):
                self.insert(i, fn)
            self.bind('<<ListboxSelect>>', self.cursor_select_cb)
        
        def cursor_select_cb(self, *args):
            if len(self.curselection()) == 0:
                return
            idx = self.curselection()[0]
            
            CONTEXT.file_selected = idx
            CONTEXT.root.event_generate(CONTEXT.EVENTS.BOARD_ACTION_BUTTON_ENABLE)

    def __init__(self, master):
        super().__init__(master=master, text="Device Program")

        self.listbox = DeviceCodeWidget.DeviceCodeListBox(self)
        self.listbox.pack(fill='both')
        

    


"""
class DeviceList(Listbox):
    def __init__(self, master):
        super().__init__(master=master, width=30, height=3, exportselection=0)
        self.board_list = []
        self.redraws = 0
        CONTEXT.bind_root(CONTEXT.EVENTS.REDRAW_LISTBOX, self.redraw)
        self.bind('<<ListboxSelect>>', self.cursor_select_cb)

    def cursor_select_cb(self, *args):
        if len(self.curselection()) == 0:
            return
        idx = self.curselection()[0]
        if idx >= len(self.board_list):
            return
        
        board = self.board_list[idx]
        CONTEXT.board_selected = board
        CONTEXT.root.event_generate(CONTEXT.EVENTS.BOARD_SELECTED_DRAW_INSPEC)
        CONTEXT.root.event_generate(CONTEXT.EVENTS.BOARD_ACTION_BUTTON_ENABLE)
"""