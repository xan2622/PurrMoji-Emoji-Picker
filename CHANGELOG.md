# PurrMoji Emoji Picker Changelog

## Version 1.2.0

### Added:

- **Global Hotkey:** Added a configurable global hotkey (default: `Ctrl+Alt+X`) to instantly show/hide PurrMoji from anywhere.
- **Auto-Start:** Added option to automatically launch PurrMoji when the OS session starts (Windows, Linux, macOS).
- **System Tray Integration:** Added option to minimize PurrMoji to the system tray, keeping it running in the background for quick access.
- **Customizable Shortcuts:** All application shortcuts (navigation, themes, size, etc.) are now fully customizable in the Hotkeys dialog.
- **Customizable Mouse Actions:** Mouse actions (copy to clipboard, toggle favorites, resize wheel) are now customizable with modifier keys and click types.
- **Start Minimized:** Added option to start PurrMoji silently in the background (minimized to tray) on startup.

### Improved:

- **Reset Buttons Logic:** Reset buttons (↩) in Hotkeys and Settings dialogs are now only clickable when the current value differs from the default.
- **Disabled State Styling:** Improved visual feedback for disabled UI elements (labels, buttons, inputs) in Dark and Medium themes.
- **Checkbox/RadioButton Hover:** Fixed hover background color for checkboxes and radio buttons in Light theme to be more visible.
- **Button Font Consistency:** OK and Cancel buttons now use the same font size as Hotkeys, Settings, and About buttons.
- **Global Hotkey UI:** When the global hotkey is disabled, related elements (label, warning text, buttons) are now properly grayed out.
- **Win+. Conflict Warning:** When `Win+.` is set as the global hotkey, a warning is displayed to inform the user that this hotkey conflicts with Windows' own emoji picker.

### Released binaries:

- PurrMoji_Emoji_Picker-1.2.0-windows-x64.zip
- purrmoji-1.2.0-1.x86_64.rpm
- purrmoji_1.2.0_amd64.deb


## Version 1.1.0

### Fixed: 

- **Dependency Issues on Linux:** Added numpy as a required dependency for skia-python. This resolves the ModuleNotFoundError: No module named 'numpy' crash.
- **Better Cross-Platform Support:** Replaced Windows-specific explorer.exe calls with a robust cross-platform file opener. The "Open Folder" button now works correctly on Linux and WSL by detecting available file managers (xdg-open, nautilus, dolphin, etc.).
- **Missing Emojis:** Resolved an issue where Kaomoji category icons and grid emojis appeared as empty rectangles on Linux (due to missing "Segoe UI Emoji" font). They now fallback to Noto Color Emoji, ensuring consistent rendering across all platforms.
- **Font Size Consistency Across Platforms:** Implemented a new FontManager system that ensures consistent font sizes across Windows, Linux, and macOS. The UI now uses Arial (universally available) with automatic size adjustments (+2 points on Linux) to compensate for rendering differences. This fixes the issue where fonts appeared smaller on Linux in tabs, dropdowns, buttons, and dialog windows (Hotkeys, Settings, About).
- **Custom Folder Buttons on Linux:** Fixed insufficient height for "Open custom folder" and "Refresh custom emoji folder" buttons on Linux. 
- **Refresh Button Icon on Linux:** Replaced the Unicode emoji "🔄" in the "Refresh custom emoji folder" button with an SVG icon (Refresh.svg from Icons8) to ensure it displays correctly on all Linux distributions.
- **Initialization Order:** Resolved an AttributeError crash on startup where current_emoji_package was accessed before initialization.

### Improved:

- **Dialog Layouts:** Added scroll areas to Settings and Hotkeys dialogs to fix unwanted spacing and match About dialog style.
- **Console Output:** Removed verbose debug messages that were displayed when emojis rendered successfully. Console now only shows errors and warnings.
- **Button Alignment:** Aligned OK/Cancel buttons to the right in all dialogs (About, Hotkeys, Settings) for consistent UI.
- **Default Accent Color:** Changed the default accent color from #5555ff to #00557f for active UI elements (category buttons, tabs, radio buttons, checkboxes, dropdown selections). 
- **Scrollbar Styling:** Changed the scrollbar thumb color in Light and Medium themes.
- **UI Element Heights:** Adjusted heights of dropdown menus (emoji package selector and variation filter). Reduced search bar height and Size input field height.
- **Code Cleanup:** Removed redundant checks and Windows-specific hardcoded paths in favor of PathManager logic.
- **Refresh Icon Theme Support:** The icon of the 'Refresh custom folder' button now automatically inverts colors for Medium and Dark themes.
- **Search Bar Placeholder Text Color:** Changed the placeholder text color in the search bar for Medium theme to make the text more readable.
- **UI Spacing Refinement:** Removed the 'dot' separator between the background color button and Size label, replaced with a 10px spacing.

### Released binaries:

- PurrMoji_Emoji_Picker-1.1.0-windows-x64.zip
- purrmoji-1.1.0-1.x86_64.rpm
- purrmoji_1.1.0_amd64.deb


## Version 1.0.0

### Added:

- A drop-down menu to choose between 5 available emoji sets (EmojiTwo, Noto, OpenMoji, Segoe UI Emoji, Twemoji) + a few Kaomojis
- A drop-down menu to display All emojis / Only the ones with variations / Only the ones without variations
- A search field (to quickly find emojis by name or by unicode) and a button to clear the search field
- Radio buttons to display either Colored or Black emojis, PNG / SVG / TTF emojis, 72 px or 618 px emojis sets
- A button to view Recent / Favorite / Frequently used emojis
- 12 buttons to switch between emoji categories
- Up to 3 rows of tabs for sub-categories (depending on the category)
- An emoji preview with emoji name and unicode code
- A contrast button to invert emoji colors (useful when viewing black emojis in dark mode)
- A color button to change emoji background color (located next to the "Size" controls)
- An input field to directly set the emoji size and two - and + buttons to decrease or increase emojis size
- A 'Hotkeys' dialog to give information about the three available hotkeys
- A 'Settings' dialog to configure which preferences are saved persistently across app restarts
- "Add to favorites" button, a "Copy to clipboard" button, a "Clear" button in Recent / Favorites
- Custom folder support: add your own PNG, SVG, or TTF icons and emojis alongside the bundled emoji packages

### Released binaries:

- PurrMoji_Emoji_Picker-1.0.0-windows-x64.zip