import json
from pathlib import Path
from typing import Any

class ValidationError(ValueError): pass

class VolumeTarget:
    """Read-only Volume TARGET 0.1 document."""
    def __init__(self, document: dict[str, Any]): self.document=document

    @classmethod
    def load(cls, path: str | Path, *, validate: bool = True, schema_path: str | Path | None = None) -> "VolumeTarget":
        document=json.loads(Path(path).read_text(encoding="utf-8")); result=cls(document)
        if validate: result.validate(schema_path=schema_path)
        return result

    @classmethod
    def from_dict(cls, document: dict[str, Any], *, validate: bool = True, schema_path: str | Path | None = None) -> "VolumeTarget":
        result=cls(document)
        if validate: result.validate(schema_path=schema_path)
        return result

    def validate(self, *, schema_path: str | Path | None = None) -> None:
        try:
            import jsonschema
        except ImportError as exc: raise ValidationError("validation requires the jsonschema package") from exc
        schema_file=Path(schema_path) if schema_path else Path(__file__).with_name("schemas") / "volume-target.schema.json"
        schema=json.loads(schema_file.read_text(encoding="utf-8"))
        errors=sorted(jsonschema.Draft202012Validator(schema, format_checker=jsonschema.FormatChecker()).iter_errors(self.document), key=lambda e: list(e.path))
        if errors: raise ValidationError("; ".join(e.message for e in errors))
