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
    """Custom QPushButton that emits signals on various click types"""
    doubleClicked = pyqtSignal()
    shiftClicked = pyqtSignal()
    ctrlClicked = pyqtSignal()
    altClicked = pyqtSignal()
    singleClicked = pyqtSignal()
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
    
    def mouseDoubleClickEvent(self, event):
        """Handle mouse double-click event"""
        self.doubleClicked.emit()
        super().mouseDoubleClickEvent(event)
    
    def mousePressEvent(self, event):
        """Handle mouse press event to detect modifier+Click"""
        modifiers = event.modifiers()
        if modifiers & Qt.ShiftModifier:
            self.shiftClicked.emit()
        elif modifiers & Qt.ControlModifier:
            self.ctrlClicked.emit()
        elif modifiers & Qt.AltModifier:
            self.altClicked.emit()
        super().mousePressEvent(event)
    
    def mouseReleaseEvent(self, event):
        """Handle mouse release for single click without modifiers"""
        modifiers = event.modifiers()
        if not (modifiers & (Qt.ShiftModifier | Qt.ControlModifier | Qt.AltModifier)):
            self.singleClicked.emit()
        super().mouseReleaseEvent(event)


class EmojiScrollArea(QScrollArea):
    """Custom QScrollArea that intercepts wheel events for modifier+Wheel size adjustment"""
    wheelEventWithCtrl = pyqtSignal(int)
    wheelEventWithShift = pyqtSignal(int)
    wheelEventWithAlt = pyqtSignal(int)
    wheelEventNoModifier = pyqtSignal(int)
    
    def wheelEvent(self, event):
        """Handle wheel event - check for modifier+Wheel for size adjustment"""
        modifiers = event.modifiers()
        delta = event.angleDelta().y()
        
        if modifiers & Qt.ControlModifier:
            self.wheelEventWithCtrl.emit(delta)
            event.accept()
            return
        elif modifiers & Qt.ShiftModifier:
            self.wheelEventWithShift.emit(delta)
            event.accept()
            return
        elif modifiers & Qt.AltModifier:
            self.wheelEventWithAlt.emit(delta)
            event.accept()
            return
        
        # No modifier - allow normal scrolling
        super().wheelEvent(event)


