from TelosAirSAMDBoardFlashGUI.context import CONTEXT
# from TelosAirBoardManager.util.arduino import get_connected_boards
from TelosAirSAMDBoardFlashGUI.util.bossa import get_connected_boards
from TelosAirSAMDBoardFlashGUI.util.tkinter_threads import JobThread

def refresh_button_callback(*args):
    def _get_connected_boards_and_update_list():
        boards = get_connected_boards()
        CONTEXT.board_list = boards

    th = JobThread([CONTEXT.EVENTS.DONE_REFRESH, CONTEXT.EVENTS.REDRAW_LISTBOX, CONTEXT.EVENTS.UNLOCK_REFRESH_BUTTON],
                    _get_connected_boards_and_update_list)
    th.start()

CONTEXT.bind_root(CONTEXT.EVENTS.REFRESH, refresh_button_callback)