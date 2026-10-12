# Word Helper — Super-Diccionario

Asistente de palabras de escritorio para Windows y macOS, desarrollado con Python y PyQt6.

Captura un fragmento de texto con OCR, busca candidatos en diccionarios locales y permite escribir la selección en la aplicación anterior. El nombre del producto es **Word Helper**; el repositorio conserva **Super-Diccionario**.

## Funciones actuales

- Captura por atajo global, overlay y ejecución en bandeja.
- Selección con clic o teclas 1–9 y escritura en la aplicación activa anterior.
- Diccionarios inglés/español, filtros de longitud y perfiles.
- Favoritos, historial, estadísticas y prevención de repeticiones.
- OCR con Apple Vision en macOS y Tesseract en Windows.
- Modo automático de prueba con dos regiones calibradas.
- Flujos de GitHub Actions para pruebas y generación de instaladores.

## Requisitos

Python 3.11 o superior, compatible con las dependencias de `requirements.txt` y sesión gráfica en Windows o macOS. En Windows, Tesseract debe estar instalado y en `PATH` para OCR. En macOS se necesitan permisos de Accesibilidad y Grabación de pantalla para las funciones de captura y escritura.

## Instalación de desarrollo

Clona el repositorio:

```bash
git clone https://github.com/DonMilo-22/Super-Diccionario.git
cd Super-Diccionario
```

En Windows, desde PowerShell:

```powershell
powershell -ExecutionPolicy Bypass -File .\setup_windows.ps1
```

Después abre `Word Helper.bat`, generado por el instalador de desarrollo.

En macOS:

```bash
bash setup_macos.sh
```

Después abre `Word Helper.command`.

## Uso básico

1. Abre Word Helper y la aplicación donde quieres usarlo.
2. Pulsa `Alt + Space` y selecciona el fragmento en pantalla.
3. Elige una sugerencia con clic o una tecla del 1 al 9.
4. Consulta ajustes para cambiar el atajo, idioma y escritura automática de Enter.

La [guía detallada en inglés](docs/README.en.md) explica calibración del modo automático, perfiles, historial y compilación de instaladores. Los instaladores se generan mediante el workflow de build; su existencia como descarga publicada depende de las ejecuciones/releases disponibles.

## Almacenamiento y límites

El historial de palabras usadas se guarda en `~/Library/Application Support/WordHelper/used_words.json` en macOS y `%APPDATA%\WordHelper\used_words.json` en Windows. Configuración y estadísticas son locales. El OCR puede equivocarse; revisa resultados y regiones calibradas. Las funciones de captura, atajos y escritura dependen de permisos del sistema.

## Comprobaciones

```bash
python -m compileall -q main.py auto_mode.py capture.py dialogs.py dictionary.py ocr.py platform_utils.py settings.py stats.py used_words.py
python -m unittest discover -s tests -v
```

GitHub Actions está configurado para ejecutar la suite en Windows y macOS.

## Autor y licencia

Desarrollado por [DonMilo-22](https://github.com/DonMilo-22). No se declara una licencia explícita del código en el repositorio.
