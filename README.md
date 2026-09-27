# Word Helper

Word Helper is a fast desktop word assistant built for games and any workflow where you need to capture a text fragment, find a matching word, and type it back into the app you were using.

## New workflow

1. Keep Word Helper running in the system tray.
2. In Roblox or another app, press **Alt + Space**.
3. Select the text fragment on screen.
4. Word Helper runs OCR and opens a compact overlay near the cursor.
5. Choose a suggestion by clicking it or pressing **1–9**.
6. Word Helper returns to the previous app, types the word, and optionally presses Enter.
7. The word is stored as used and is hidden from future suggestions.

## Highlights

- Cross-platform support for Windows and macOS.
- Compact overlay instead of a large always-visible window.
- System tray mode.
- Keyboard selection with **1–9**.
- Click-to-type back into Roblox or the previous active window.
- Optional automatic **Enter** after typing.
- Optional instant selection when only one valid word exists.
- Automatic search mode that checks both word beginnings and endings.
- English, Spanish, or combined results.
- Profiles for Roblox, English, Spanish, and mixed use.
- Configurable global hotkey.
- Word length filters.
- Optional proper-name filtering.
- Ranking that prioritizes favorites, words you use frequently, and common words.
- Favorites from the result context menu.
- Used-word history where individual words can be restored.
- Smart anti-repeat that can also hide close grammatical variants.
- New-game/session reset.
- Automatic Roblox session reset when a new Roblox target is detected.
- Local session statistics.
- Subtle sound feedback.
- Subtle overlay fade-in animation.
- OCR preprocessing for small/low-contrast text.
- OCR correction for common mistakes such as **0/O** and **1/I**.
- OCR confidence indicator based on how many valid dictionary results were found.
- Optional launch at system startup.
- Real Windows installer build and macOS DMG build.

## OCR

### macOS

Word Helper prefers **Apple Vision**, using the native macOS OCR framework.

macOS can request:

- Accessibility permission
- Screen Recording permission

These permissions are needed for capture, global shortcuts, and automatic typing.

### Windows

Word Helper uses **Tesseract OCR** with image preprocessing before recognition.

Tesseract must be installed and available in PATH for screenshot OCR. Manual searches still work without OCR.

## Quick development install

### Windows

Open PowerShell inside the repository:

```powershell
powershell -ExecutionPolicy Bypass -File .\setup_windows.ps1
```

Then open:

```text
Word Helper.bat
```

### macOS

```bash
bash setup_macos.sh
```

Then open:

```text
Word Helper.command
```

## Real installers

The GitHub Actions build workflow creates:

- **Windows:** `Word-Helper-Setup.exe`
- **macOS:** `Word-Helper-macOS.dmg`

The workflow can be started manually from GitHub Actions or by pushing a version tag such as:

```text
v2.0.0
```

## Controls

| Action | Control |
| --- | --- |
| Capture screen text | Alt + Space |
| Select suggestion | Click or 1–9 |
| Favorite a word | Right-click result |
| Start fresh game/session | Nueva partida |
| Restore a used word | Historial |
| Change profile/settings | Gear button |
| Open hidden app | System tray |

The global shortcut can be changed in Settings.

## Profiles

### Roblox

Optimized for fast gameplay:

- English by default
- automatic start/end search
- common-word ranking
- compact overlay
- automatic Enter enabled
- session reset support

### English / Español / Ambos

Profiles switch language and sensible defaults without requiring you to change every option manually.

## Used words and history

Used words are stored outside the repository:

- macOS: `~/Library/Application Support/WordHelper/used_words.json`
- Windows: `%APPDATA%\WordHelper\used_words.json`

The **Historial** window lets you restore one word instead of clearing the entire list.

Smart anti-repeat can additionally hide related variants such as close suffix variants during a session.

## Statistics

Word Helper stores local-only statistics such as:

- words used in the current session
- total words used
- session count
- per-word usage count
- favorites

These statistics are used to improve ranking locally.

## Project structure

```text
Super-Diccionario/
├── main.py
├── capture.py
├── dialogs.py
├── dictionary.py
├── ocr.py
├── platform_utils.py
├── settings.py
├── stats.py
├── used_words.py
├── build_app.py
├── build_dmg.sh
├── installer.iss
├── setup_windows.ps1
├── setup_macos.sh
├── requirements.txt
├── requirements-dev.txt
├── data/
├── tests/
└── .github/workflows/
```

## Development checks

```bash
python -m compileall -q main.py capture.py dialogs.py dictionary.py ocr.py platform_utils.py settings.py stats.py used_words.py
python -m unittest discover -s tests -v
```

GitHub Actions runs the test suite on both Windows and macOS.

## Build manually

Install build dependencies:

```bash
pip install -r requirements-dev.txt
python build_app.py
```

On macOS, create the DMG after building:

```bash
bash build_dmg.sh
```

On Windows, `installer.iss` can be compiled with Inno Setup after the PyInstaller build.
