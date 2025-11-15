#!/usr/bin/env python3
# -*- coding: utf-8 -*-
# SPDX-FileCopyrightText: Copyright (C) 2025 xan2622
# SPDX-License-Identifier: GPL-3.0-or-later

"""
Custom event handlers for PurrMoji Emoji Picker
Contains widget classes with custom event handling (double-click, shift-click, Ctrl+wheel).
"""

from PyQt5.QtWidgets import QPushButton, QScrollArea
from PyQt5.QtCore import Qt, pyqtSignal


class DoubleClickButton(QPushButton):
    """Custom QPushButton that emits signals on double-click and shift+click"""
    doubleClicked = pyqtSignal()
    shiftClicked = pyqtSignal()
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def mouseDoubleClickEvent(self, event):
        """Handle mouse double-click event"""
        self.doubleClicked.emit()
        super().mouseDoubleClickEvent(event)
    
    def mousePressEvent(self, event):
        """Handle mouse press event to detect Shift+Click"""
        if event.modifiers() & Qt.ShiftModifier:
            self.shiftClicked.emit()
        super().mousePressEvent(event)


class EmojiScrollArea(QScrollArea):
    """Custom QScrollArea that intercepts wheel events for Ctrl+Wheel size adjustment"""
    wheelEventWithCtrl = pyqtSignal(int)  # Signal for wheel delta when Ctrl is pressed
    
    def wheelEvent(self, event):
        """Handle wheel event - prioritize Ctrl+Wheel for size adjustment"""
        # Check if Ctrl modifier is held
        if event.modifiers() & Qt.ControlModifier:
            # Consume the event and emit signal for size adjustment
            # Positive delta = wheel up = increase size
            # Negative delta = wheel down = decrease size
            self.wheelEventWithCtrl.emit(event.angleDelta().y())
            event.accept()
            return
        
        # If Ctrl is not pressed, allow normal scrolling behavior
        super().wheelEvent(event)


