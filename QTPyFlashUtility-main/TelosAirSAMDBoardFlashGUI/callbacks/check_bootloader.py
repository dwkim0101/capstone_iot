from TelosAirSAMDBoardFlashGUI.context import CONTEXT
from TelosAirSAMDBoardFlashGUI.util.tkinter_threads import JobThread
from tkinter import messagebox

def check_bootloader(*args):
    # if not CONTEXT.board_selected:
    #     return
    # diskp = search_for_qt_py()
    # while (not diskp and messagebox.askretrycancel("", "Device is not in bootloader update (?) mode. Please double-press the reset button and try again.")):
    #     diskp = search_for_qt_py()

    # if not diskp:
    #     return
    
    # res = check_bootloader_version(diskp.mountpoint)
    # if not res:
    #     messagebox.showerror("", "Something went wrong checking bootloader version.")
    #     return
    
    # version, needs_update = res
    # if not needs_update:
    #     messagebox.showinfo("", f"The selected board has bootloader version {version} and does not need an update.")
    # else:
    #     messagebox.askyesno("", f"The selected board has bootloader version {version} and the minimum required is {LATEST_BOOTLOADER_VER}.\nWould you like to update the bootloader?")
    
    # print(res)
    pass

    

    

CONTEXT.bind_root(CONTEXT.EVENTS.BOARD_BOOTLOADER_BUTTON, check_bootloader)