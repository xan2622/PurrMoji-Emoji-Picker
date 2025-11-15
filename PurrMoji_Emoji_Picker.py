#!/usr/bin/env python3
# -*- coding: utf-8 -*-

#    PurrMoji Emoji Picker, Open-source emoji viewer and emoji picker 
#    developped in Python and released under the GPL 3.0 license.
#    Copyright (C) 2025 xan2622
#
#    This program is free software: you can redistribute it and/or modify
#    it under the terms of the GNU General Public License as published by
#    the Free Software Foundation, either version 3 of the License, or
#    (at your option) any later version.
#
#    This program is distributed in the hope that it will be useful,
#    but WITHOUT ANY WARRANTY; without even the implied warranty of
#    MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
#    GNU General Public License for more details.
#
#    You should have received a copy of the GNU General Public License
#    along with this program.  If not, see <https://www.gnu.org/licenses/>.


import sys
import os

# Add data directory to Python path to allow imports
# This works both when running as script and as PyInstaller executable
if getattr(sys, 'frozen', False):
    # Running as compiled executable
    exe_dir = os.path.dirname(sys.executable)
    
    # Try multiple possible locations for data directory
    possible_data_dirs = [
        os.path.join(exe_dir, "data"),  # Data moved to root by build script
        os.path.join(exe_dir, "_internal", "data"),  # Data in _internal (before move)
    ]
    
    # Also check _MEIPASS if available
    base_dir = getattr(sys, '_MEIPASS', None)
    if base_dir:
        possible_data_dirs.extend([
            os.path.join(base_dir, "data"),
            base_dir,  # In case data modules are directly in _MEIPASS
        ])
    
    # Add first existing data directory to path
    for data_dir in possible_data_dirs:
        if os.path.exists(data_dir) and data_dir not in sys.path:
            sys.path.insert(0, data_dir)
            break
else:
    # Running as script
    script_dir = os.path.dirname(os.path.abspath(__file__))
    data_dir = os.path.join(script_dir, "data")
    if os.path.exists(data_dir):
        if data_dir not in sys.path:
            sys.path.insert(0, data_dir)

from PyQt5.QtCore import QtMsgType, qInstallMessageHandler
from PyQt5.QtWidgets import QApplication

from ui import EmojiPicker, ExtractionDialog
from managers import ZipExtractor


def qt_message_handler(msg_type, context, message):
    """Custom Qt message handler to filter out OpenType warnings
    
    Args:
        msg_type: Type of message (debug, warning, critical, etc.)
        context: Context information about the message
        message: The message string
    """
    # Filter out OpenType support warnings for special Unicode scripts
    if "OpenType support missing" in message:
        return
    
    # Message type mapping
    msg_types = {
        QtMsgType.QtDebugMsg: "Qt Debug",
        QtMsgType.QtWarningMsg: "Qt Warning",
        QtMsgType.QtCriticalMsg: "Qt Critical",
        QtMsgType.QtFatalMsg: "Qt Fatal"
    }
    
    if msg_type in msg_types:
        print(f"{msg_types[msg_type]}: {message}", file=sys.stderr)


def check_and_extract_packages(app):
    """Check if packages need extraction and extract them if necessary
    
    Args:
        app: QApplication instance
    
    Returns:
        bool: True if successful, False if extraction failed
    """
    extractor = ZipExtractor()
    
    # Check if any package needs extraction
    packages_needed = []
    for package_name in extractor.PACKAGE_CONFIG.keys():
        if not extractor.is_package_extracted(package_name):
            packages_needed.append(package_name)
    
    # If all packages are already extracted, return success
    if not packages_needed:
        return True
    
    # Show extraction dialog
    dialog = ExtractionDialog()
    dialog.show()
    app.processEvents()
    
    # Start extraction
    dialog.start_extraction()
    
    # Wait for dialog to close
    result = dialog.exec_()
    
    return result == 1  # QDialog.Accepted


def main():
    """Main function to run the application"""
    qInstallMessageHandler(qt_message_handler)
    
    app = QApplication(sys.argv)
    app.setApplicationName("PurrMoji Emoji Picker")
    app.setApplicationVersion("1.0")
    
    # Check and extract packages if needed (first launch)
    if not check_and_extract_packages(app):
        sys.exit(1)
    
    # Create and show main window
    window = EmojiPicker()
    window.show()
    
    sys.exit(app.exec_())


if __name__ == "__main__":
    main()
