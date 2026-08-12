import sys
import os
import logging
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt

from pathlib import Path

# Add src package directory to sys.path
SRC_DIR = Path(__file__).parent / "src"
if str(SRC_DIR) not in sys.path:
    sys.path.insert(0, str(SRC_DIR))

from src.config import APP_NAME
from src.database import DatabaseManager
from src.core.tracker import TimeTrackerThread
from src.ui.main_window import MainWindow
from src.ui.icon_factory import create_app_icon

def setup_logging():
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
        handlers=[
            logging.StreamHandler(sys.stdout)
        ]
    )

def main():
    setup_logging()
    logger = logging.getLogger("Main")
    logger.info(f"Starting {APP_NAME}...")

    # Enable High DPI Scaling for crisp UI on high-res displays
    os.environ["QT_AUTO_SCREEN_SCALE_FACTOR"] = "1"

    app = QApplication(sys.argv)
    app.setApplicationName(APP_NAME)
    app.setOrganizationName(APP_NAME)
    app.setStyle("Fusion")

    # Set modern gaming application icon globally
    app_icon = create_app_icon()
    app.setWindowIcon(app_icon)

    # Initialize Persistence Manager
    db_manager = DatabaseManager()

    # Start Background Time Tracker Worker
    tracker_thread = TimeTrackerThread(db_manager=db_manager, poll_interval=1.0)
    tracker_thread.start()

    # Create Main UI Window
    window = MainWindow(db_manager=db_manager, tracker_thread=tracker_thread)

    # If launched with --minimized (e.g. on Windows startup), keep in system tray
    if "--minimized" not in sys.argv:
        window.show()
    else:
        logger.info("Application started minimized in System Tray.")

    # Run Application Event Loop
    exit_code = app.exec()

    # Cleanup on close
    tracker_thread.stop()
    db_manager.save()
    logger.info("Application exited cleanly.")
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
