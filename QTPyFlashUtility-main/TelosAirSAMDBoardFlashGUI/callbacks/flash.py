from TelosAirSAMDBoardFlashGUI.context import CONTEXT
from TelosAirSAMDBoardFlashGUI.ui.widgets.action_popup import ActionPopup
from TelosAirSAMDBoardFlashGUI.util.bossa import *
from TelosAirSAMDBoardFlashGUI.util.files import DEVICE_FILE_PATHS
import os

def flash_button_callback(*args):
    fileidx = CONTEXT.file_selected
    if fileidx is None:
        logger.error(f"Failed due to Nonetype fileidx.")
        return
    
    if fileidx < 0 or fileidx > len(DEVICE_FILE_PATHS)-1:
        logger.error(f"Failed due to invalid fileidx: {fileidx}. Needs to be a valid idx <= {len(DEVICE_FILE_PATHS)-1} ")
        return
    
    filepath = DEVICE_FILE_PATHS[fileidx]
    if filepath is None:
        logger.error(f"Failed due to Nonetype filepath.")
        return

    logger.info(f"Selected file is {filepath}.")

    class FlashProcessThread(Thread):
        def __init__(self, board: Board):
            self.board = board
            self.updates_queue = Queue()
            super().__init__(daemon=True)

        def run(self):
            CONTEXT.root.event_generate(CONTEXT.EVENTS.BOARD_ACTION_BUTTON_DISABLE)
            th = FlashThread(board=CONTEXT.board_selected, filepath=filepath, updates_queue=self.updates_queue)
            th.start()
            popup = ActionPopup(root=CONTEXT.root, starting_text="Beginning flashing process.", 
                                msg_queue=self.updates_queue, window_title="TelosAirBoardManager - Board Flashing")
            
            th.join()
            
            CONTEXT.board_list = []
            CONTEXT.root.event_generate(CONTEXT.EVENTS.CLEAR_INSPECT)
            CONTEXT.root.event_generate(CONTEXT.EVENTS.CLEAR_DEVICES)
            CONTEXT.root.update()
            sleep(2)
            CONTEXT.root.event_generate(CONTEXT.EVENTS.REFRESH)
            CONTEXT.root.event_generate(CONTEXT.EVENTS.CLEAR_INSPECT)
            CONTEXT.root.event_generate(CONTEXT.EVENTS.BOARD_ACTION_BUTTON_ENABLE)

    th = FlashProcessThread(CONTEXT.board_selected)
    th.start()

CONTEXT.bind_root(CONTEXT.EVENTS.FLASH_BUTTON, flash_button_callback)