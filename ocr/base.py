from dataclasses import dataclass, field


@dataclass
class OCRResult:
    text: str
    confidence: float
    provider: str
    page_count: int = 1
    metadata: dict | None = None
    is_synthetic: bool = False

    def __post_init__(self) -> None:
        # Surface a clear warning whenever synthetic sample data is returned
        # so the pipeline cannot silently process non-real documents.
        if self.is_synthetic:
            import structlog

            structlog.get_logger(__name__).warning(
                "ocr_synthetic_data",
                provider=self.provider,
                message="OCR returned SYNTHETIC sample data, not extracted from the uploaded document.",
            )
