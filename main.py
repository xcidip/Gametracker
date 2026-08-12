import sys
import os
import logging
from PyQt6.QtWidgets import QApplication
from PyQt6.QtCore import Qt
from PyQt6.QtNetwork import QLocalServer, QLocalSocket

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

SERVER_NAME = "GameTracker_SingleInstance_IPC_Server"

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

    # --- Single Instance Enforcement via QLocalSocket / QLocalServer ---
    socket = QLocalSocket()
    socket.connectToServer(SERVER_NAME)
    if socket.waitForConnected(500):
        # An instance is already running!
        if "--minimized" not in sys.argv:
            logger.info("An instance of GameTracker is already running. Requesting window restore...")
            socket.write(b"RESTORE")
            socket.waitForBytesWritten(1000)
        socket.disconnectFromServer()
        logger.info("Exiting secondary application process to prevent duplicate tray icons.")
        sys.exit(0)

    # Initialize single-instance IPC server
    local_server = QLocalServer()
    QLocalServer.removeServer(SERVER_NAME)  # Remove stale socket from previous abnormal exit
    local_server.listen(SERVER_NAME)

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

    # Handle incoming IPC messages from duplicate launched processes
    def handle_ipc_connection():
        client_socket = local_server.nextPendingConnection()
        if client_socket:
            def on_ready_read():
                try:
                    msg = client_socket.readAll().data().decode("utf-8", errors="ignore")
                    if "RESTORE" in msg:
                        window.restore_from_tray()
                except Exception as e:
                    logger.debug(f"IPC message read error: {e}")
                client_socket.disconnectFromServer()
            client_socket.readyRead.connect(on_ready_read)

    local_server.newConnection.connect(handle_ipc_connection)

    # Register tray icon and IPC server cleanup on application quit
    app.aboutToQuit.connect(window.cleanup_system_tray)
    app.aboutToQuit.connect(local_server.close)

    # If launched with --minimized (e.g. on Windows startup), keep in system tray
    if "--minimized" not in sys.argv:
        window.show()
    else:
        logger.info("Application started minimized in System Tray.")

    # Run Application Event Loop
    exit_code = app.exec()

    # Cleanup on close
    window.cleanup_system_tray()
    tracker_thread.stop()
    db_manager.save()
    local_server.close()
    QLocalServer.removeServer(SERVER_NAME)
    logger.info("Application exited cleanly.")
    sys.exit(exit_code)

if __name__ == "__main__":
    main()
