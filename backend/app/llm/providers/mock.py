from pydantic import BaseModel
from pydantic_core import PydanticUndefined


class MockLLMProvider:
    provider_name = "mock"

    def complete_json(self, prompt: str, schema: type[BaseModel]) -> BaseModel:
        fields = {}
        for name, field in schema.model_fields.items():
            if field.default is not PydanticUndefined:
                fields[name] = field.default
            elif field.default_factory is not None:  # type: ignore[attr-defined]
                fields[name] = field.default_factory()  # type: ignore[misc]
            else:
                fields[name] = None
        if "confidence" in fields:
            fields["confidence"] = 0.0
        if "red_flags" in fields:
            fields["red_flags"] = []
        return schema.model_validate(fields)
