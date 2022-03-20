from dataclasses import dataclass

from .resource import Resource
from .operation import Operation


@dataclass()
class ObjectProperty:
    name: str
    type: str
    description: str
    sources: dict[Resource, set[Operation]]
    is_array: bool
