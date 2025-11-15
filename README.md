# PurrMoji Emoji Picker

**PurrMoji Emoji Picker** is a lightweight open-source emoji picker designed to make browsing, searching, and copying emojis quick and easy.

<img width="30%" height="30%" alt="light theme" src="https://github.com/user-attachments/assets/614b28fc-6326-4fb6-9762-a0ee1379bc1f" />
<img width="30%" height="30%" alt="medium theme" src="https://github.com/user-attachments/assets/97b61c53-32e0-4b41-bb55-039c4b3290a8" />
<img width="30%" height="30%" alt="dark theme" src="https://github.com/user-attachments/assets/d24a91a9-2416-4af5-9c11-10b8936ebdfb" />
</br>

Supported emoji packages:
| Emoji Package | Preview |
|---|---|
| **[Emojitwo 2.2.5](https://emojitwo.github.io/)** | [emojipedia.org/joypixels/2.2.5](https://emojipedia.org/joypixels/2.2.5) |
| **[Noto Emoji 17.0](https://github.com/googlefonts/noto-emoji)** | [emojipedia.org/google/17.0](https://emojipedia.org/google/17.0) |
| **[OpenMoji 16.0](https://openmoji.org/)** | [emojipedia.org/openmoji](https://emojipedia.org/openmoji) |
| **[Segoe UI Emoji 1.33](https://learn.microsoft.com/en-us//typography/font-list/segoe-ui-emoji)** | [emojipedia.org/microsoft](https://emojipedia.org/microsoft) |
| **[Twemoji 14.0](https://github.com/twitter/twemoji)** | [emojipedia.org/twitter/twemoji-14.0](https://emojipedia.org/twitter/twemoji-14.0) |
| **Kaomoji** | Includes support for various kaomoji sets |
| **Custom** | Allows you to add your own images, icons or emojis (PNG, SVG, TTF) |

## 💡 Origin of PurrMoji Emoji Picker

This project was initially created specifically for the **[OpenMoji](https://openmoji.org/)** open-source emoji library. OpenMoji's mission is to create and maintain a consistent set of open-source emojis but not to develop an emoji picker app, hence this software.

Since then, the goal of the PurrMoji project has evolved, expanding its support to include multiple emoji packages.

## 📋 Some of its features
  
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
- An input field to directly set the emoji size and two - + buttons to decrease or increase emojis size
- A 'Hotkeys' dialog to give information about the three available hotkeys
- A 'Settings' dialog to configure which preferences are saved persistently across app restarts
- "Add to favorites" button, a "Copy to clipboard" button, a "Clear" button in Recent / Favorites
- Hotkeys: "Double-click" to copy emoji to clipboard, "Shift + Left Click" to add/remove emoji to/from favorites, "Ctrl + Wheel Up/Down" to increase/decrease emoji size in the grid, the "+" key to increase emoji size in the grid, the "-" key to decrease emoji size in the grid, "Page Up" to select the next package, "Page Down" to select the previous package, "T" to cycle through themes (Light > Medium > Dark)
- Custom folder support: add your own PNG, SVG, or TTF icons and emojis alongside the bundled emoji packages

## 💬 Feedback & Community

If you have ideas or want to report a bug about **PurrMoji Emoji Picker**, feel free to [open an issue](https://github.com/xan2622/PurrMoji-Emoji-Picker/issues) on this Github repository.

If you want to contribute to the emoji library projects themselves, please visit their respective repositories linked above.

If you want to chat about PurrMoji, you can join my Discord server: [https://discord.gg/DSVQthQKsf](https://discord.gg/DSVQthQKsf)

## ⚙️ Under the hood

### Rendering Engine

- All emoji formats (PNG, SVG, TTF) are rendered using **[Skia-Python](https://github.com/kyamagu/skia-python/)** for optimal performance and quality. [Skia](https://skia.org/) provides hardware-accelerated rendering with direct memory processing, ensuring fast loading and beautiful emoji display across all formats.

- When Skia is not available or fails to render an emoji, **[PyQt5](https://www.riverbankcomputing.com/software/pyqt/download)**'s native renderer (QSvgRenderer for SVG, QPixmap for PNG) is used as a fallback system.

### First Launch Setup

On the first launch, PurrMoji will display an extraction dialog window to unpack the emoji packages from their compressed ZIP archives. 

The extraction takes a few moments and shows a progress bar with the current operation. Once completed, the emoji packages are stored in:
- **Windows**: `%APPDATA%\PurrMoji\emoji_packages\`
- **macOS**: `~/Library/Application Support/PurrMoji/emoji_packages/`
- **Linux**: `~/.local/share/PurrMoji/emoji_packages/`

The Custom emoji folder and Kaomoji data remain in the application directory and don't require extraction. Segoe UI Emoji also doesn't require extraction as it uses the system TTF font already installed on Windows.

## ⚖️ Licenses
  
### Emoji Packages

Each emoji package included in PurrMoji Emoji Picker retains its original license:

| Emoji Package | License |
|---|---|
| **Emojitwo (2.2.5)** | <a href="https://emojitwo.github.io/#emojione-2x-artwork-license">https://emojitwo.github.io/#emojione-2x-artwork-license</a> |
| **Noto Emoji (17.0)** | <a href="https://github.com/googlefonts/noto-emoji?tab=OFL-1.1-1-ov-file">https://github.com/googlefonts/noto-emoji?tab=OFL-1.1-1-ov-file</a> |
| **OpenMoji (16.0)** | <a href="https://github.com/hfg-gmuend/openmoji?tab=CC-BY-SA-4.0-1-ov-file#readme">https://github.com/hfg-gmuend/openmoji?tab=CC-BY-SA-4.0-1-ov-file#readme</a> |
| **Segoe UI Emoji (1.33)** | <a href="https://learn.microsoft.com/en-us/typography/fonts/font-faq">https://learn.microsoft.com/en-us/typography/fonts/font-faq</a> (these emojis are not bundled in PurrMoji, they are just displayed) |
| **Twemoji (14.0)** | <a href="https://github.com/twitter/twemoji/blob/master/LICENSE-GRAPHICS">https://github.com/twitter/twemoji/blob/master/LICENSE-GRAPHICS</a> |

Each emoji has been designed by contributors to their respective projects, who remain the original authors of their works. 

A huge "thanks" to all contributors of these projects.

### Custom Folder Test Icons

The "Custom" folder allows you to add your own PNG/SVG/TTF icons or emojis. The test icons provided in "Custom" are from the following websites. You can remove them from the "Custom" folder and add your own ones.

| File type | License |
|---|---|
| **SVG Icons:** [SVGrepo.com](https://www.svgrepo.com/) | [SVGrepo Licensing (CC0)](https://www.svgrepo.com/page/licensing/) |
| **PNG Icons:** [3dicons.co](https://3dicons.co/) | [3dicons License (CC0)](https://3dicons.co/about) |

### PurrMoji Emoji Picker

- PurrMoji Emoji Picker has been released under the [GPL 3.0 license](https://www.gnu.org/licenses/gpl-3.0.en.html). This license only covers the source code of PurrMoji.
- The few custom SVG icons it uses for its UI are released under the [CC BY-SA 4.0 license](https://creativecommons.org/licenses/by-sa/4.0/deed.en). It also uses some of the emojis from the current package.
