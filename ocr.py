import platform


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


def _read_with_tesseract(image_path):
    try:
        import pytesseract
        from PIL import Image
    except ImportError as exc:
        raise OCRUnavailableError(
            "Faltan las dependencias de OCR. Ejecuta el instalador de Word Helper."
        ) from exc

    try:
        with Image.open(image_path) as image:
            return pytesseract.image_to_string(
                image,
                config="--psm 7",
            )
    except pytesseract.TesseractNotFoundError as exc:
        raise OCRUnavailableError(
            "Tesseract OCR no esta instalado o no se encontro en PATH."
        ) from exc


def read_text(image_path):
    if platform.system() == "Darwin":
        try:
            return _read_with_vision(image_path)
        except Exception:
            # Vision is the preferred native backend on macOS. If it is not
            # available (for example in a custom Python environment), fall
            # back to the cross-platform Tesseract backend.
            pass

    return _read_with_tesseract(image_path)
