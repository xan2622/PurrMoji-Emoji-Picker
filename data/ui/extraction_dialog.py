#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: Copyright (C) 2025 xan2622
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Extraction Dialog - Shows progress when extracting emoji packages
"""

import sys
import os
import subprocess
import platform
import time

from PyQt5.QtWidgets import (
    QDialog, QVBoxLayout, QHBoxLayout, QLabel, QProgressBar, QApplication, 
    QPushButton, QMessageBox
)
from PyQt5.QtCore import Qt, QThread, pyqtSignal
from PyQt5.QtGui import QFont

from managers import ZipExtractor


class ExtractionWorker(QThread):
    """Worker thread for package extraction"""
    
    progress_updated = pyqtSignal(int, int, str)  # current, total, message
    extraction_completed = pyqtSignal(bool, str)  # success, message
    
    def __init__(self):
        super().__init__()
        self.extractor = ZipExtractor()
        self.cancelled = False
        self.paused = False
    
    def cancel(self):
        """Request cancellation of extraction"""
        self.cancelled = True
    
    def pause(self):
        """Request pause of extraction"""
        self.paused = True
    
    def resume(self):
        """Request resume of extraction"""
        self.paused = False
    
    def is_cancelled(self):
        """Check if extraction is cancelled"""
        return self.cancelled
    
    def is_paused(self):
        """Check if extraction is paused"""
        return self.paused
    
    def run(self):
        """Extract all packages in background thread"""
        try:
            def progress_callback(current, total, message):
                # Check for pause
                while self.paused and not self.cancelled:
                    time.sleep(0.1)
                
                # Check for cancellation
                if self.cancelled:
                    return False
                
                self.progress_updated.emit(current, total, message)
                return True
            
            results = self.extractor.extract_all_packages(progress_callback)
            
            # Check if cancelled
            if self.cancelled:
                self.extraction_completed.emit(False, "Extraction cancelled by user")
                return
            
            # Check if all extractions succeeded
            all_success = all(results.values())
            
            if all_success:
                self.extraction_completed.emit(True, "All packages extracted successfully!")
            else:
                failed = [pkg for pkg, success in results.items() if not success]
                self.extraction_completed.emit(
                    False,
                    f"Failed to extract: {', '.join(failed)}"
                )
        except Exception as e:
            self.extraction_completed.emit(False, f"Extraction error: {e}")


class ExtractionDialog(QDialog):
    """Dialog showing emoji package extraction progress"""
    
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("PurrMoji Emoji Picker")
        self.setWindowFlags(Qt.Dialog | Qt.WindowTitleHint | Qt.CustomizeWindowHint | Qt.WindowCloseButtonHint)
        self.setModal(True)
        self.setFixedSize(500, 320)
        
        self.extractor = ZipExtractor()
        self.setup_ui()
        self.worker = None
        self.extraction_started = False
    
    def setup_ui(self):
        """Setup the user interface"""
        layout = QVBoxLayout()
        layout.setSpacing(15)
        layout.setContentsMargins(30, 30, 30, 30)
        
        # Title label
        self.title_label = QLabel("Initializing Emoji Packages")
        title_font = QFont()
        title_font.setPointSize(12)
        title_font.setBold(True)
        self.title_label.setFont(title_font)
        self.title_label.setAlignment(Qt.AlignCenter)
        layout.addWidget(self.title_label)
        
        # Status label
        self.status_label = QLabel("Preparing to extract packages...")
        self.status_label.setAlignment(Qt.AlignCenter)
        self.status_label.setWordWrap(True)
        layout.addWidget(self.status_label)
        
        # Progress bar
        self.progress_bar = QProgressBar()
        self.progress_bar.setMinimum(0)
        self.progress_bar.setMaximum(100)
        self.progress_bar.setValue(0)
        self.progress_bar.setTextVisible(True)
        layout.addWidget(self.progress_bar)
        
        # Info label
        self.info_label = QLabel(
            "This operation only happens once.\n"
            "Emoji packages are being extracted to your user directory."
        )
        self.info_label.setAlignment(Qt.AlignCenter)
        info_font = QFont()
        info_font.setPointSize(8)
        self.info_label.setFont(info_font)
        self.info_label.setStyleSheet("color: gray;")
        layout.addWidget(self.info_label)
        
        # Control buttons layout
        control_buttons_layout = QHBoxLayout()
        control_buttons_layout.setSpacing(10)
        
        # Pause/Resume button
        self.pause_resume_button = QPushButton("Pause")
        self.pause_resume_button.setFixedHeight(32)
        self.pause_resume_button.clicked.connect(self.toggle_pause_resume)
        control_buttons_layout.addWidget(self.pause_resume_button)
        
        # Cancel button
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.setFixedHeight(32)
        self.cancel_button.clicked.connect(self.cancel_extraction)
        control_buttons_layout.addWidget(self.cancel_button)
        
        layout.addLayout(control_buttons_layout)
        
        # Open folder button
        self.open_folder_button = QPushButton("Open Packages Folder")
        self.open_folder_button.setFixedHeight(32)
        self.open_folder_button.clicked.connect(self.open_packages_folder)
        layout.addWidget(self.open_folder_button)
        
        self.setLayout(layout)
    
    def start_extraction(self):
        """Start the extraction process"""
        self.extraction_started = True
        self.worker = ExtractionWorker()
        self.worker.progress_updated.connect(self.on_progress_updated)
        self.worker.extraction_completed.connect(self.on_extraction_completed)
        self.worker.start()
    
    def toggle_pause_resume(self):
        """Toggle pause/resume state"""
        if not self.worker or not self.worker.isRunning():
            return
        
        if self.worker.is_paused():
            self.worker.resume()
            self.pause_resume_button.setText("Pause")
            self.status_label.setText("Extraction resumed...")
        else:
            self.worker.pause()
            self.pause_resume_button.setText("Resume")
            self.status_label.setText("Extraction paused")
    
    def cancel_extraction(self):
        """Cancel the extraction process"""
        if not self.worker or not self.worker.isRunning():
            self.reject()
            return
        
        # Ask for confirmation
        reply = QMessageBox.question(
            self,
            "Cancel Extraction",
            "Are you sure you want to cancel the extraction?\n\n"
            "You will need to extract the packages again next time.",
            QMessageBox.Yes | QMessageBox.No,
            QMessageBox.No
        )
        
        if reply == QMessageBox.Yes:
            self.worker.cancel()
            self.status_label.setText("Cancelling extraction...")
            self.pause_resume_button.setEnabled(False)
            self.cancel_button.setEnabled(False)
    
    def on_progress_updated(self, current, total, message):
        """Update progress bar and status message"""
        self.status_label.setText(message)
        
        if total > 0:
            progress_percent = int((current / total) * 100)
            self.progress_bar.setValue(progress_percent)
            self.progress_bar.setFormat(f"{progress_percent}%")
        else:
            self.progress_bar.setValue(100)
            self.progress_bar.setFormat("100%")
        
        # Process events to keep UI responsive
        QApplication.processEvents()
    
    def on_extraction_completed(self, success, message):
        """Handle extraction completion"""
        self.extraction_started = False
        self.pause_resume_button.setEnabled(False)
        self.cancel_button.setEnabled(False)
        
        if success:
            self.status_label.setText(message)
            self.progress_bar.setValue(100)
            self.accept()
        else:
            self.status_label.setText(f"<span style='color: red;'>{message}</span>")
            
            # If cancelled, show zero progress
            if "cancelled" in message.lower():
                self.progress_bar.setValue(0)
            
            # Still accept to allow app to continue (user can try again later)
            self.accept()
    
    def open_packages_folder(self):
        """Open the folder where packages are extracted"""
        packages_dir = self.extractor.get_user_packages_dir()
        
        # Ensure directory exists
        os.makedirs(packages_dir, exist_ok=True)
        
        # Open folder in file explorer based on OS
        system = platform.system()
        
        try:
            if system == "Windows":
                os.startfile(packages_dir)
            elif system == "Darwin":  # macOS
                subprocess.run(["open", packages_dir])
            else:  # Linux and others
                subprocess.run(["xdg-open", packages_dir])
        except Exception as e:
            print(f"[ERROR] Failed to open packages folder: {e}", file=sys.stderr)
    
    def closeEvent(self, event):
        """Handle dialog close event with confirmation if extraction is running"""
        if self.worker and self.worker.isRunning():
            # Ask for confirmation before closing during extraction
            reply = QMessageBox.question(
                self,
                "Close Dialog",
                "Extraction is still in progress.\n\n"
                "Do you want to cancel the extraction and close?",
                QMessageBox.Yes | QMessageBox.No,
                QMessageBox.No
            )
            
            if reply == QMessageBox.Yes:
                self.worker.cancel()
                self.worker.wait(1000)  # Wait up to 1 second for thread to finish
                event.accept()
            else:
                event.ignore()
        else:
            event.accept()

