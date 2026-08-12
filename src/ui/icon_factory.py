import os
from pathlib import Path
from PyQt6.QtGui import QIcon, QPixmap, QPainter, QColor, QBrush, QPen, QLinearGradient
from PyQt6.QtCore import Qt, QRectF

def create_app_icon(size: int = 128) -> QIcon:
    """
    Generates a sleek, high-resolution gaming controller application icon
    using QPixmap and QPainter. Works on all DPI scaling settings without
    external file dependencies.
    """
    pixmap = QPixmap(size, size)
    pixmap.fill(Qt.GlobalColor.transparent)

    painter = QPainter(pixmap)
    painter.setRenderHint(QPainter.RenderHint.Antialiasing)

    # 1. Background: Rounded rect with vibrant linear gradient (Purple -> Cyan)
    margin = size * 0.05
    rect = QRectF(margin, margin, size - 2 * margin, size - 2 * margin)
    radius = size * 0.24

    gradient = QLinearGradient(0, 0, size, size)
    gradient.setColorAt(0.0, QColor("#6C5CE7"))  # Neon Purple Accent
    gradient.setColorAt(1.0, QColor("#00CEC9"))  # Cyan Glow

    painter.setBrush(QBrush(gradient))
    painter.setPen(QPen(QColor("#181B28"), size * 0.02))
    painter.drawRoundedRect(rect, radius, radius)

    # 2. Gamepad Controller Body
    cx, cy = size / 2.0, size / 2.0
    w, h = size * 0.54, size * 0.36
    body_rect = QRectF(cx - w / 2, cy - h / 2, w, h)
    
    painter.setBrush(QBrush(QColor("#FFFFFF")))
    painter.setPen(Qt.PenStyle.NoPen)
    painter.drawRoundedRect(body_rect, h * 0.42, h * 0.42)

    # 3. Left D-Pad (Dark Blue / Slate)
    dpad_color = QColor("#1E2235")
    painter.setBrush(QBrush(dpad_color))
    
    d_size = size * 0.06
    lx = cx - w * 0.24
    ly = cy
    painter.drawRect(QRectF(lx - d_size / 3, ly - d_size, d_size * 0.66, d_size * 2))
    painter.drawRect(QRectF(lx - d_size, ly - d_size / 3, d_size * 2, d_size * 0.66))

    # 4. Right Action Buttons (4 vibrant colored dots)
    rx = cx + w * 0.24
    ry = cy
    b_radius = size * 0.035
    spacing = size * 0.055

    btn_colors = [
        QColor("#FF7675"),  # Top - Red/Pink
        QColor("#74B9FF"),  # Right - Blue
        QColor("#55E6C1"),  # Bottom - Green
        QColor("#FDCB6E")   # Left - Yellow
    ]
    positions = [
        (rx, ry - spacing),      # Top
        (rx + spacing, ry),      # Right
        (rx, ry + spacing),      # Bottom
        (rx - spacing, ry)       # Left
    ]
    for (bx, by), col in zip(positions, btn_colors):
        painter.setBrush(QBrush(col))
        painter.drawEllipse(QRectF(bx - b_radius, by - b_radius, b_radius * 2, b_radius * 2))

    painter.end()

    # Wrap in QIcon and add multiple scaled resolutions for crisp system tray rendering
    icon = QIcon(pixmap)
    for s in [16, 24, 32, 48, 64, 128, 256]:
        scaled = pixmap.scaled(s, s, Qt.AspectRatioMode.KeepAspectRatio, Qt.TransformationMode.SmoothTransformation)
        icon.addPixmap(scaled)

    return icon
