import platform
import re


class OCRUnavailableError(RuntimeError):
    pass


def _read_with_vision(image_path):
    from Foundation import NSURL
    from Vision import VNImageRequestHandler, VNRecognizeTextRequest

    request = VNRecognizeTextRequest.alloc().init()
    request.setRecognitionLevel_(1)

    handler = VNImageRequestHandler.alloc().initWithURL_options_(
        NSURL.fileURLWithPath_(image_path),
        None,
    )

    success = handler.performRequests_error_([request], None)
    if not success:
        return ""

    results = []
    for observation in request.results() or []:
        candidates = observation.topCandidates_(1)
        if candidates:
            results.append(candidates[0].string())

    return " ".join(results)


def _preprocess_for_tesseract(image_path):
    from PIL import Image, ImageEnhance, ImageFilter, ImageOps

    image = Image.open(image_path).convert("L")
    image = ImageOps.autocontrast(image)
    image = image.resize((image.width * 3, image.height * 3))
    image = ImageEnhance.Contrast(image).enhance(1.8)
    return image.filter(ImageFilter.SHARPEN)


def _read_with_tesseract(image_path):
    try:
        import pytesseract
    except ImportError as exc:
        raise OCRUnavailableError(
            "Faltan las dependencias de OCR. Ejecuta el instalador de Word Helper."
        ) from exc

    try:
        image = _preprocess_for_tesseract(image_path)
        return pytesseract.image_to_string(image, config="--psm 7")
    except pytesseract.TesseractNotFoundError as exc:
        raise OCRUnavailableError(
            "Tesseract OCR no esta instalado o no se encontro en PATH."
        ) from exc


def read_text(image_path):
    if platform.system() == "Darwin":
        try:
            return _read_with_vision(image_path)
        except Exception:
            pass
    return _read_with_tesseract(image_path)


def normalize_ocr_text(text):
    text = re.sub(r"\s+", "", text or "")
    text = re.sub(r"[^A-Za-zÁÉÍÓÚÜÑáéíóúüñ0-9]", "", text)
    return text.upper()


def correction_candidates(text):
    normalized = normalize_ocr_text(text)
    candidates = [normalized]
    swaps = {
        "0": "O",
        "1": "I",
        "5": "S",
        "8": "B",
    }

    corrected = "".join(swaps.get(char, char) for char in normalized)
    if corrected != normalized:
        candidates.append(corrected)

    return list(dict.fromkeys(candidate for candidate in candidates if candidate))
