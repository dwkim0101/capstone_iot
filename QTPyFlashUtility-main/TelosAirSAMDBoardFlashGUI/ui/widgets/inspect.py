from tkinter import *
from TelosAirSAMDBoardFlashGUI.models.board import Board
from TelosAirSAMDBoardFlashGUI.context import CONTEXT

event_generate_func_generator = lambda event_str: lambda *args: CONTEXT.root.event_generate(event_str)

class BoardInfoEntry(Frame):
    def __init__(self, master, title_str: str):
        super().__init__(master=master)

        self.text_var = StringVar()
        title_label = Label(master=self, text=f"{title_str}: ", justify=LEFT)
        title_label.pack(side=LEFT, fill='x')

        entry_label = Label(master=self, textvariable=self.text_var, justify=RIGHT)
        entry_label.pack(fill='x')

    def update_text(self, text: str):
        self.text_var.set(text)

class BoardInfoFrame(Frame):
    def __init__(self, master):
        super().__init__(master=master)

        self.board_name = BoardInfoEntry(self, "Board Type")
        self.board_path = BoardInfoEntry(self, "USB Conn.")
        self.board_sn = BoardInfoEntry(self, "Serial")

        self.board_name.pack()
        self.board_path.pack()
        self.board_sn.pack()

    def update(self, board: Board):
        self.board_name.update_text(board.board_name)
        self.board_path.update_text(board.port_path)
        self.board_sn.update_text(board.serial_number)

    def clear(self):
        self.board_name.update_text("")
        self.board_path.update_text("")
        self.board_sn.update_text("")

class CheckBootloaderButton(Button):
    def __init__(self, master):
        super().__init__(master=master, text='Check Bootloader Version', command=event_generate_func_generator(CONTEXT.EVENTS.BOARD_BOOTLOADER_BUTTON))

class ActionButtonsFrame(Frame):
    def __init__(self, master):
        super().__init__(master=master)

        self.flash_button = Button(self, text='Flash', command=event_generate_func_generator(CONTEXT.EVENTS.FLASH_BUTTON))
        # self.check_bootloader_button = CheckBootloaderButton(self)

        self.flash_button.pack(fill=X)
        # self.check_bootloader_button.pack()

        CONTEXT.bind_root(CONTEXT.EVENTS.BOARD_ACTION_BUTTON_ENABLE, self.enable)
        # CONTEXT.bind_root(CONTEXT.EVENTS.BOARD_ACTION_BUTTON_DISABLE, self.disable)
        self.disable()

    def enable(self, *args):
        # print([CONTEXT.board_selected, CONTEXT.file_selected])
        if not (None in [CONTEXT.board_selected, CONTEXT.file_selected]):
            for btn in [self.flash_button]:
                btn: Button
                btn.config(state='normal')

    def disable(self, *args):
        for btn in [self.flash_button]:
            btn: Button
            btn.config(state='disabled')

class BoardInspectWidget(Frame):
    def __init__(self, master):
        super().__init__(master=master)

        self.board_info = BoardInfoFrame(self)
        self.board_info.pack(side=TOP, fill='both', padx=10, pady=10)

        self.action_buttons = ActionButtonsFrame(self)
        self.action_buttons.pack(side=BOTTOM, fill=X, padx=10)

        CONTEXT.bind_root(CONTEXT.EVENTS.BOARD_SELECTED_DRAW_INSPEC, self.update)
        CONTEXT.bind_root(CONTEXT.EVENTS.CLEAR_INSPECT, self.clear)

    def update(self, *args):
        board = CONTEXT.board_selected
        if not board: return
        self.board_info.update(board)

    def clear(self, *args):
        self.board_info.clear()
