from TelosAirSAMDBoardFlashGUI.ui.app import TelosAirApp
from TelosAirSAMDBoardFlashGUI.context import CONTEXT
from TelosAirSAMDBoardFlashGUI.callbacks.refresh_button import refresh_button_callback

import logging
logger = logging.getLogger("TelosAir")
formatter = logging.Formatter('%(asctime)s %(name)s %(levelname)s: %(message)s', datefmt='%Y-%m-%d %H:%M:%S')

handler = logging.StreamHandler()
handler.setFormatter(formatter)

logger.addHandler(handler)
logger.setLevel(logging.DEBUG)

def main():
    logger.info("Starting.")
    app = TelosAirApp()
    #TODO: Use ini file or something
    refresh_button_callback()
    CONTEXT.init(app, client_name="TestClient", db_url="http://127.0.0.1:5001")
    

    app.mainloop()


if __name__ == "__main__":
    main()