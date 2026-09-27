# Word Helper

Word Helper is a small desktop application for finding English and Spanish words from a text fragment. It is designed for fast use while another application or game is open.

## What it does

- Global shortcut: **Alt + Space**
- Cross-platform screen region capture with Qt
- OCR:
  - macOS: Apple Vision
  - Windows: Tesseract OCR
- English and Spanish word suggestions
- Search by beginning or ending of a word
- Click a suggestion to:
  1. mark it as used,
  2. return focus to the previous window,
  3. type the selected word automatically
- Used words are saved and excluded from future suggestions
- Reset button to clear the used-word history
- Always-on-top desktop interface

## Quick install

### Windows

Requirements:
- Windows 10/11
- Python 3.11 or newer
- Internet connection during setup

Open PowerShell in the repository folder and run:

```powershell
powershell -ExecutionPolicy Bypass -File .\setup_windows.ps1
```

The installer creates a local virtual environment, installs the Python dependencies and tries to install Tesseract OCR through `winget` when necessary.

After setup, open:

```text
Word Helper.bat
```

### macOS

Requirements:
- macOS
- Python 3

From Terminal inside the repository:

```bash
bash setup_macos.sh
```

Then open:

```text
Word Helper.command
```

macOS can ask for **Accessibility** and **Screen Recording** permissions. They are necessary for the global shortcut, capture and automatic typing.

## Manual installation

```bash
git clone https://github.com/DonMilo-22/Super-Diccionario.git
cd Super-Diccionario
python -m venv .venv
```

Activate the environment and install:

```bash
pip install -r requirements.txt
python main.py
```

On Windows, Tesseract OCR must also be installed and available in PATH.

## Usage

1. Keep the application running.
2. Go to the application or game where you want to use Word Helper.
3. Press **Alt + Space**.
4. Select the text fragment on screen.
5. Word Helper reads the capture and shows suggestions.
6. Click a word such as `lovely`.
7. Word Helper hides itself, returns to the previous window and types `lovely`.
8. That word is immediately saved as used and will no longer appear in searches until the used-word list is reset.

You can also type a fragment manually and use **Inicio** or **Final**.

## Project structure

```text
Super-Diccionario/
├── main.py
├── capture.py
├── platform_utils.py
├── ocr.py
├── dictionary.py
├── used_words.py
├── build_app.py
├── requirements.txt
├── requirements-dev.txt
├── setup_windows.ps1
├── setup_macos.sh
├── data/
│   ├── english_words.txt
│   └── spanish_words.txt
├── tests/
└── .github/workflows/
```

## Building a desktop application

Install development dependencies:

```bash
pip install -r requirements-dev.txt
```

Then run:

```bash
python build_app.py
```

The build is written to the `dist/` folder.

A GitHub Actions build workflow is also included for macOS and Windows. It can be started manually from the Actions tab or automatically when a version tag such as `v1.0.0` is pushed.

> Windows builds still require Tesseract OCR on the destination computer for screenshot OCR. Manual text searches work without it.

## Used-word storage

Word Helper keeps its history outside the repository:

- macOS: `~/Library/Application Support/WordHelper/used_words.json`
- Windows: `%APPDATA%\WordHelper\used_words.json`
- Linux-compatible fallback: `~/.local/share/WordHelper/used_words.json`

## Development checks

Run:

```bash
python -m compileall -q main.py capture.py dictionary.py ocr.py platform_utils.py used_words.py
python -m unittest discover -s tests -v
```

GitHub Actions runs these checks on both Windows and macOS for pull requests and relevant pushes.

## Notes

The old README described Tesseract as the macOS OCR engine. The current implementation uses Apple Vision on macOS and Tesseract as the Windows/cross-platform fallback.
