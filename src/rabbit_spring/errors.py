"""Package exceptions."""


class SpringSizingError(RuntimeError):
    """Raised for invalid spring-sizing configuration or derived geometry."""


class SpringModelExportError(RuntimeError):
    """Raised when a CAD backend cannot export the requested spring model."""
