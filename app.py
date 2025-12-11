"""
MediaKit Pro - Main Application Entry Point

A Python desktop application for exporting videos and livestreaming using FFmpeg,
combining visuals, audio, and overlays with a modern GUI.
"""
import sys
import os

# Ensure the package directory is in the path
package_dir = os.path.dirname(os.path.abspath(__file__))
if package_dir not in sys.path:
    sys.path.insert(0, package_dir)

from PySide6.QtWidgets import QApplication
from PySide6.QtCore import Qt
from PySide6.QtGui import QFont, QPalette, QColor

from ui.main_window import MainWindow


def setup_application() -> QApplication:
    """
    Setup and configure the Qt application.
    
    Returns:
        Configured QApplication instance.
    """
    # Enable high DPI scaling
    QApplication.setHighDpiScaleFactorRoundingPolicy(
        Qt.HighDpiScaleFactorRoundingPolicy.PassThrough
    )
    
    app = QApplication(sys.argv)
    app.setApplicationName("MediaKit Pro")
    app.setApplicationVersion("2.0.0")
    app.setOrganizationName("MediaKitPro")
    
    # Set default font
    font = QFont("Segoe UI", 10)
    app.setFont(font)
    
    # Set application style
    app.setStyle("Fusion")
    
    # Create dark palette
    palette = create_dark_palette()
    app.setPalette(palette)
    
    return app


def create_dark_palette() -> QPalette:
    """
    Create a dark color palette for the application.
    
    Returns:
        Configured QPalette with dark colors.
    """
    palette = QPalette()
    
    # Base colors
    dark_color = QColor(26, 26, 46)  # #1a1a2e
    darker_color = QColor(22, 33, 62)  # #16213e
    accent_color = QColor(0, 212, 255)  # #00d4ff
    text_color = QColor(204, 214, 246)  # #ccd6f6
    disabled_color = QColor(136, 146, 176)  # #8892b0
    
    # Window
    palette.setColor(QPalette.ColorRole.Window, dark_color)
    palette.setColor(QPalette.ColorRole.WindowText, text_color)
    
    # Base (input fields)
    palette.setColor(QPalette.ColorRole.Base, darker_color)
    palette.setColor(QPalette.ColorRole.AlternateBase, dark_color)
    
    # Text
    palette.setColor(QPalette.ColorRole.Text, text_color)
    palette.setColor(QPalette.ColorRole.PlaceholderText, disabled_color)
    
    # Button
    palette.setColor(QPalette.ColorRole.Button, darker_color)
    palette.setColor(QPalette.ColorRole.ButtonText, text_color)
    
    # Highlight
    palette.setColor(QPalette.ColorRole.Highlight, accent_color)
    palette.setColor(QPalette.ColorRole.HighlightedText, dark_color)
    
    # Disabled
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.WindowText, disabled_color)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.Text, disabled_color)
    palette.setColor(QPalette.ColorGroup.Disabled, QPalette.ColorRole.ButtonText, disabled_color)
    
    # Tool tips
    palette.setColor(QPalette.ColorRole.ToolTipBase, darker_color)
    palette.setColor(QPalette.ColorRole.ToolTipText, text_color)
    
    # Link
    palette.setColor(QPalette.ColorRole.Link, accent_color)
    palette.setColor(QPalette.ColorRole.LinkVisited, accent_color)
    
    return palette


def main() -> int:
    """
    Main entry point for the application.
    
    Returns:
        Application exit code.
    """
    # Create application
    app = setup_application()
    
    # Create and show main window
    window = MainWindow()
    window.show()
    
    # Run application event loop
    return app.exec()


if __name__ == "__main__":
    sys.exit(main())
