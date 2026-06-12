from typing import Protocol, TypeVar

from pydantic import BaseModel


SchemaT = TypeVar("SchemaT", bound=BaseModel)


class LLMProvider(Protocol):
    provider_name: str

    def complete_json(self, prompt: str, schema: type[SchemaT]) -> SchemaT:
        ...
