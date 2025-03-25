import sys
import os
import pathlib

"""

# Determine if running as a bundled application or in a normal Python environment
if getattr(sys, 'frozen', False):
    # If the application is run as a bundle, the PyInstaller bootloader
    # extends the sys module by a flag frozen=True and sets the app 
    # path into variable _MEIPASS.
    APP_PATH = sys._MEIPASS
else:
    APP_PATH = os.path.dirname(os.path.abspath(__file__))

BOSSAC_BIN_PATH_MAC_OS = f"{APP_PATH}/bossac_binaries/bossac"
BOSSAC_BIN_PATH_WINDOWS = f"{APP_PATH}/bossac_binaries/bossac.exe"

"""

# Determine if running as a bundled application or in a normal Python environment
if getattr(sys, 'frozen', False):
    # If the application is run as a bundle, the PyInstaller bootloader
    # extends the sys module by a flag frozen=True and sets the app 
    # path into variable _MEIPASS.
    APP_PATH = sys._MEIPASS
else:
    APP_PATH = os.path.dirname(os.path.abspath(__file__))

BIN_FOLDER_PATH = os.path.join(APP_PATH, 'device_binaries')

DEVICE_FILE_NICKNAMES = [
        "QT Py - Plantower PMS5003 Read",
        "QT Py - AlphaSense OPC-R2 Read",
        # "QT Py - Test Flashing"
]

DEVICE_FILE_PATHS = [
    os.path.join(BIN_FOLDER_PATH, "PlantowerTestSketch.ino.bin"),
    os.path.join(BIN_FOLDER_PATH, "AlphaSenseTestSketch.ino.bin"),
    # os.path.join(BIN_FOLDER_PATH, "DoNothingTestSketch.ino.bin")
    # os.path.join(BIN_FOLDER_PATH, "test.ino.bin")
]