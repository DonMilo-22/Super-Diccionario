from Vision import (
    VNRecognizeTextRequest,
    VNImageRequestHandler
)
from Foundation import NSURL

def read_text(image_path):
    request = VNRecognizeTextRequest.alloc().init()

    handler = VNImageRequestHandler.alloc().initWithURL_options_(
        NSURL.fileURLWithPath_(image_path),
        None
    )

    success = handler.performRequests_error_([request], None)

    if not success:
        return ""

    results = []

    for observation in request.results():
        candidate = observation.topCandidates_(1)

        if candidate:
            results.append(candidate[0].string())

    return " ".join(results)