from tkinter import *
from typing import Callable
from TelosAirSAMDBoardFlashGUI.models.board import Board
import logging

logger = logging.getLogger("TelosAir")
class Context(object):
    root: Tk = None

    client_name: str = None

    _to_bind: 'list[str, Callable]' = []

    board_list: 'list[Board]' = []
    board_selected: Board = None

    file_selected: int = None

    class EVENTS(object):
        REFRESH = "<<refresh-devices-button>>"
        DONE_REFRESH = "<<refresh-devices-done>>"
        REDRAW_LISTBOX = "<<redraw-listbox>>"
        UNLOCK_REFRESH_BUTTON = "<<unlock-refresh-button>>"

        BOARD_SELECTED_DRAW_INSPEC = "<<draw-inspect>>"

        BOARD_BOOTLOADER_BUTTON = "<<bootloader-button>>"
        BOARD_ACTION_BUTTON_ENABLE = "<<enable-actions>>"
        BOARD_ACTION_BUTTON_DISABLE = "<<disable-actions>>"

        FLASH_BUTTON = "<<flash>>"

        BOARD_SELECT = "<<board-selected>>"
        FILE_SELECT = "<<file-selected>>"

        CLEAR_INSPECT = "<<clear-inspect>>"
        CLEAR_DEVICES = "<<clear-devices>>"

    def bind_root(self, signal: str, func: Callable):
        if self.root:
            self.root.bind(signal, func)
        else:
            self._to_bind.append((signal, func))

    def init(self, root: Tk, client_name: str, db_url: str):
        self.root = root
        self.client_name = client_name
        self.database_url = db_url
        for item in self._to_bind:
            logger.debug(f"Binding Pre-Bound: {item}")
            self.root.bind(*item)

CONTEXT = Context()

