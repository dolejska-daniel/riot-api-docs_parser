from dataclasses import dataclass

from .resource import Resource
from .operation import Operation
from .object_property import ObjectProperty


@dataclass()
class ObjectDefinition:
    name: str
    description: str
    properties: dict[str, ObjectProperty]
    sources: dict[Resource, set[Operation]]
