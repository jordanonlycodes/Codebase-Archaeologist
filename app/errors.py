class AnalysisError(Exception):
    """An expected, user-correctable ingestion or analysis failure."""

    def __init__(self, message: str, code: str = "invalid_archive", status: int = 400):
        super().__init__(message)
        self.message = message
        self.code = code
        self.status = status
