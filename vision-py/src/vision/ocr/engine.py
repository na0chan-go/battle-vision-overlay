from __future__ import annotations

import os
import warnings
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path

import certifi
import easyocr


class OCRRuntimeError(RuntimeError):
    """Raised when the OCR backend cannot produce a result."""


@dataclass(frozen=True)
class OCRResult:
    text: str
    confidence: float


def _configure_ssl_certificates() -> None:
    cert_path = certifi.where()
    os.environ.setdefault("SSL_CERT_FILE", cert_path)
    os.environ.setdefault("REQUESTS_CA_BUNDLE", cert_path)


@lru_cache(maxsize=1)
def _get_reader() -> easyocr.Reader:
    _configure_ssl_certificates()
    try:
        warnings.filterwarnings(
            "ignore",
            message=".*pin_memory.*MPS.*",
            category=UserWarning,
        )
        return easyocr.Reader(["ja", "en"], gpu=False, verbose=False)
    except Exception as exc:  # pragma: no cover - library/runtime failure path
        raise OCRRuntimeError(f"failed to initialize easyocr: {exc}") from exc


def recognize_text(image_path: Path) -> OCRResult:
    try:
        reader = _get_reader()
        results = reader.readtext(str(image_path), detail=1, paragraph=False)
    except OCRRuntimeError:
        raise
    except Exception as exc:  # pragma: no cover - library/runtime failure path
        raise OCRRuntimeError(f"easyocr failed: {exc}") from exc

    if not results:
        return OCRResult(text="", confidence=0.0)

    texts = [str(entry[1]).strip() for entry in results if len(entry) >= 2 and str(entry[1]).strip()]
    if not texts:
        return OCRResult(text="", confidence=0.0)

    confidences = [
        float(entry[2])
        for entry in results
        if len(entry) >= 3
    ]

    return OCRResult(
        text="".join(texts),
        confidence=max(confidences, default=0.0),
    )
