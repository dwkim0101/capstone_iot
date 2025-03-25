from tkinter import *
from tkinter.ttk import Progressbar
import tkinter.messagebox
from queue import Queue
from TelosAirSAMDBoardFlashGUI.context import CONTEXT

class ActionPopup(Toplevel):
    def __init__(self, root: Tk, starting_text: str, msg_queue: Queue, window_title: str = ''):
        super().__init__(master=root)
        if window_title: self.title(window_title)
        self.window_title = window_title

        self.geometry("300x150")

        # Using a queue here for thread-safety
        # TODO: enforce msg format with actual code: tuple(msg, ok(bool), done(bool))
        self.msg_queue = msg_queue
        
        self.layout = Frame(master=self)
        self.progress_text_var = StringVar(value = starting_text)
        progress_text_label = Label(self.layout, textvariable=self.progress_text_var)
        progress_bar = Progressbar(master=self.layout, mode='indeterminate', orient='horizontal')
        
        progress_text_label.pack(fill='x', side=TOP)
        progress_bar.pack(fill='x')

        self.layout.grid(sticky='nsew', padx=50, pady=50)
        progress_bar.start()

        self.update()

    def update(self, *args):
        if not self.msg_queue.empty():
            msg = self.msg_queue.get()
            if len(msg) == 3:
                msg_text, is_ok, is_done = msg

                if not is_ok:
                    self.destroy()
                    tkinter.messagebox.showerror(self.window_title, msg_text)
                    return
                
                if is_done:
                    self.destroy()
                    tkinter.messagebox.showinfo(self.window_title, msg_text)
                    return
                else:
                    self.progress_text_var.set(msg_text)

        CONTEXT.root.after(100, self.update)

        
