import sys
import os
from pathlib import Path

# Add project root
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from PyQt6.QtWidgets import QApplication
from src.database import DatabaseManager, GameEntry
from src.core.tracker import TimeTrackerThread
from src.ui.main_window import MainWindow

def test_sections():
    app = QApplication.instance() or QApplication(sys.argv)
    
    # Use temporary test database file
    test_db_path = "scratch/test_db.json"
    if os.path.exists(test_db_path):
        os.remove(test_db_path)

    db = DatabaseManager(data_file=test_db_path)
    
    # Add 2 favorite games and 2 non-favorite games
    g1 = db.add_game("Favorite Game 1", "C:\\fav1.exe")
    db.toggle_favorite(g1.id)
    
    g2 = db.add_game("Favorite Game 2", "C:\\fav2.exe")
    db.toggle_favorite(g2.id)

    g3 = db.add_game("Other App 1", "C:\\app1.exe")
    g4 = db.add_game("Other App 2", "C:\\app2.exe")

    tracker = TimeTrackerThread(db)
    window = MainWindow(db, tracker)
    window.show()

    # Check sections
    assert "favorites" in window.sections, "Favorites section should exist"
    assert "other" in window.sections, "Other section should exist"

    assert len(window.sections["favorites"].cards) == 2
    assert len(window.sections["other"].cards) == 2

    print("Initial setup verified: 2 favorited, 2 other.")

    # Toggle favorite on g3
    window.toggle_favorite_game(g3.id)
    assert len(window.sections["favorites"].cards) == 3
    assert len(window.sections["other"].cards) == 1
    print("Toggle favorite verified: 3 favorited, 1 other.")

    # Test collapse toggling
    fav_section = window.sections["favorites"]
    assert not fav_section.is_collapsed
    assert not fav_section.content_widget.isHidden()

    fav_section.on_header_clicked(None)
    assert fav_section.is_collapsed
    assert fav_section.content_widget.isHidden()
    print("Collapse toggle verified.")

    # Test window resize rearrange
    window.rearrange_library_grid(4)
    print("Rearrange grid verified.")

    # Test theming support on sections
    for theme in ["dark", "white", "dracula", "gruvbox"]:
        window.apply_theme(theme)
        print(f"Theme '{theme}' applied successfully.")

    window.close()
    if os.path.exists(test_db_path):
        os.remove(test_db_path)
    print("ALL TESTS PASSED SUCCESSFULLY!")

if __name__ == "__main__":
    test_sections()
