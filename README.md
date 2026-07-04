# Super Diccionario (Word Helper)

[![License](https://img.shields.io/badge/license-MIT-blue.svg)](LICENSE)

A small **Python + Qt6** desktop application that helps you discover English and Spanish words based on a text fragment.  It can capture a region of the screen, run OCR on the image, and instantly suggest words that **start** or **end** with the captured text.  The UI is styled with a dark theme and a modern glass‑morphism look.

---

## ✨ Features

- **Global hot‑key** (`Alt + Space`) to capture a screenshot anywhere on macOS.
- **OCR integration** (uses Tesseract) to turn the screenshot into text.
- Instant word suggestions from built‑in English and Spanish dictionaries.
- Two search modes:
  - *Start* – words that begin with the fragment.
  - *End* – words that end with the fragment.
- Check‑boxes to mark words as "used"; used words are persisted in `used_words.json`.
- Simple *reset* button to clear the used‑words list.
- Dark, glass‑morphic UI built with **Qt6** and custom CSS.

---

## 📦 Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/DonMilo-22/Super-Diccionario.git
   cd super-diccionario
   ```

2. **Create a virtual environment (optional but recommended)**
   ```bash
   python3 -m venv venv
   source venv/bin/activate   # on macOS / Linux
   # .\venv\Scripts\activate   # on Windows
   ```

3. **Install Python dependencies**
   ```bash
   pip install -r requirements.txt
   ```
   *If a `requirements.txt` does not exist yet, you can generate it with:*
   ```bash
   pip freeze > requirements.txt
   ```

4. **Install Tesseract OCR** (required by `ocr.py`)
   ```bash
   # macOS (Homebrew)
   brew install tesseract
   ```
   ```bash
   # Ubuntu/Debian
   sudo apt-get install tesseract-ocr
   ```

5. **Run the app**
   ```bash
   python main.py
   ```

---

## 🎮 Usage

1. Press **Alt + Space** (the global hot‑key). A screen‑capture selector appears.
2. Select the area that contains the text you want to analyse.
3. The captured image is processed with OCR and the resulting text appears in the input box.
4. Press **Enter** or click **Inicio** to see word suggestions that *start* with the fragment.
5. Click **Final** to see suggestions that *end* with the fragment.
6. Check a word to mark it as used – it will be removed from the list and stored in `used_words.json`.
7. Click **Reiniciar palabras** to clear the used‑words history.

> **Tip:** The application stays on top of other windows (`WindowStaysOnTopHint`) for a smooth workflow.

---

## 📁 Project Structure

```
Super Diccionario/
├─ main.py                # UI & application logic
├─ ocr.py                 # OCR wrapper around Tesseract
├─ dictionary.py          # Word lists & search helpers
├─ used_words.py          # Persistence of used words (JSON)
├─ used_words.json        # Stored used‑words (auto‑generated)
├─ capture.png            # Example screenshot (optional)
├─ Word Helper.spec       # PyInstaller spec for building an .app
├─ README.md              # **You are reading it!**
└─ data/                  # (optional) extra resources
```

---

## 🛠️ Building a Stand‑alone Executable (optional)

The project includes a PyInstaller spec file. To create a macOS `.app` bundle:

```bash
pip install pyinstaller
pyinstaller Word\ Helper.spec
```

The resulting app will be available in the `dist/` folder.

---

## 🤝 Contributing

Contributions are welcome! Feel free to:
- Add more languages or larger dictionaries.
- Improve the UI/UX (animations, dark‑mode tweaks, etc.).
- Fix bugs or add unit tests.

Please fork the repository, create a feature branch, and submit a pull request.

---

## 📜 License

This project is licensed under the **MIT License** – see the `LICENSE` file for details.

---

## 🙏 Acknowledgements

- **PyQt6** – powerful Qt bindings for Python.
- **pynput** – handling global hot‑keys.
- **Tesseract OCR** – open‑source optical character recognition.
- **Qt's stylesheet system** – for the sleek dark theme.

---

*Happy word hunting!*
