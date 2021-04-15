from dataclasses import dataclass, field

from .operation import Operation


@dataclass(unsafe_hash=True)
class Resource:
    id: int
    name: str = field(compare=False)
    version: str
    api_link: str = field(compare=False)
    operations: list[Operation] = field(compare=False)

    @property
    def as_source(self) -> str:
        return f"{self.name} ({self.version})"
