class ClaimProcessingError(Exception):
    """Base exception for claims processing."""
    pass

class DocumentMismatchError(ClaimProcessingError):
    """Raised when documents do not belong to the same patient or claim."""
    pass

class GatekeeperRejection(ClaimProcessingError):
    """Raised when the gatekeeper agent rejects a document outright."""
    pass