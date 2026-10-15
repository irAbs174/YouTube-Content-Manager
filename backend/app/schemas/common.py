"""Shared schema plumbing: camelCase JSON for the frontend contract."""

from __future__ import annotations

from pydantic import BaseModel, ConfigDict
from pydantic.alias_generators import to_camel


class CamelModel(BaseModel):
    """Base model serializing to camelCase (the frontend's JSON dialect)."""

    model_config = ConfigDict(alias_generator=to_camel, populate_by_name=True)
