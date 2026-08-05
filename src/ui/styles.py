MAIN_STYLE = """
QMainWindow {
    background-color: #0F111A;
}

QWidget {
    font-family: 'Segoe UI', Arial, sans-serif;
    color: #FFFFFF;
}

/* Sidebar */
#Sidebar {
    background-color: #141724;
    border-right: 1px solid #2B304A;
}

#SidebarTitle {
    font-size: 20px;
    font-weight: bold;
    color: #6C5CE7;
    padding: 15px 10px;
}

#NavButton {
    background-color: transparent;
    border: none;
    border-radius: 10px;
    padding: 12px 18px;
    text-align: left;
    font-size: 14px;
    font-weight: 600;
    color: #8E9BB0;
}

#NavButton:hover {
    background-color: #1E2235;
    color: #FFFFFF;
}

#NavButton:checked {
    background-color: #6C5CE7;
    color: #FFFFFF;
}

/* Header & Search Bar */
#HeaderFrame {
    background-color: #141724;
    border-bottom: 1px solid #2B304A;
    padding: 10px;
}

QLineEdit {
    background-color: #1E2235;
    border: 1px solid #2B304A;
    border-radius: 8px;
    padding: 8px 14px;
    color: #FFFFFF;
    font-size: 13px;
}

QLineEdit:focus {
    border: 1px solid #6C5CE7;
}

QComboBox {
    background-color: #1E2235;
    border: 1px solid #2B304A;
    border-radius: 8px;
    padding: 6px 12px;
    color: #FFFFFF;
}

QComboBox::drop-down {
    border: none;
}

QComboBox QAbstractItemView {
    background-color: #181B28;
    border: 1px solid #2B304A;
    selection-background-color: #6C5CE7;
    color: #FFFFFF;
}

/* Action Buttons */
QPushButton#PrimaryButton {
    background-color: #6C5CE7;
    color: #FFFFFF;
    border: none;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: bold;
    font-size: 13px;
}

QPushButton#PrimaryButton:hover {
    background-color: #5B4BC4;
}

QPushButton#PrimaryButton:pressed {
    background-color: #4A3BB3;
}

QPushButton#SecondaryButton {
    background-color: #1E2235;
    color: #00CEC9;
    border: 1px solid #00CEC9;
    border-radius: 8px;
    padding: 8px 16px;
    font-weight: bold;
    font-size: 13px;
}

QPushButton#SecondaryButton:hover {
    background-color: #00CEC9;
    color: #0F111A;
}

QPushButton#DangerButton {
    background-color: #272C45;
    color: #FF7675;
    border: 1px solid #FF7675;
    border-radius: 8px;
    padding: 6px 12px;
}

QPushButton#DangerButton:hover {
    background-color: #FF7675;
    color: #FFFFFF;
}

/* Game Card */
QFrame#GameCard {
    background-color: #1E2235;
    border: 1px solid #2B304A;
    border-radius: 14px;
}

QFrame#GameCard:hover {
    background-color: #24293E;
    border: 1px solid #6C5CE7;
}

#GameTitle {
    font-size: 15px;
    font-weight: bold;
    color: #FFFFFF;
}

#PlaytimeBadge {
    background-color: #141724;
    color: #00CEC9;
    border-radius: 6px;
    padding: 4px 8px;
    font-size: 12px;
    font-weight: 600;
}

#StatusBadgeRunning {
    background-color: #00B894;
    color: #FFFFFF;
    border-radius: 6px;
    padding: 3px 8px;
    font-size: 11px;
    font-weight: bold;
}

#StatusBadgeIdle {
    background-color: #2B304A;
    color: #8E9BB0;
    border-radius: 6px;
    padding: 3px 8px;
    font-size: 11px;
}

/* Dialogs */
QDialog {
    background-color: #141724;
}

QListWidget {
    background-color: #1E2235;
    border: 1px solid #2B304A;
    border-radius: 10px;
    padding: 5px;
}

QListWidget::item {
    padding: 8px;
    border-radius: 6px;
}

QListWidget::item:hover {
    background-color: #272C45;
}

QListWidget::item:selected {
    background-color: #6C5CE7;
    color: #FFFFFF;
}

/* Scrollbars */
QScrollBar:vertical {
    border: none;
    background: #0F111A;
    width: 8px;
    margin: 0px;
    border-radius: 4px;
}

QScrollBar::handle:vertical {
    background: #2B304A;
    min-height: 20px;
    border-radius: 4px;
}

QScrollBar::handle:vertical:hover {
    background: #6C5CE7;
}

QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
    height: 0px;
}
"""
