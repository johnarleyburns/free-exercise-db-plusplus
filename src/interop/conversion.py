"""Source-tree compatibility export for the installable conversion API."""
def _api():
    try:
        from fedbpp.conversion import ConversionError, ConversionResult, export_workout, import_workout
        return ConversionError, ConversionResult, export_workout, import_workout
    except ImportError as exc:
        raise ImportError("install packages/python to use conversion tooling") from exc

def import_workout(*args, **kwargs):
    return _api()[3](*args, **kwargs)

def export_workout(*args, **kwargs):
    return _api()[2](*args, **kwargs)

class ConversionError(ValueError):
    pass

ConversionResult = object

__all__ = ["ConversionError", "ConversionResult", "import_workout", "export_workout"]
