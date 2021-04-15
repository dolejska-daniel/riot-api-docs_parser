from dataclasses import dataclass, field


@dataclass(unsafe_hash=True)
class Operation:
    id: int
    method: str
    returns: str = field(compare=False)
    docs_link: str = field(compare=False)
    api_path: str = field(compare=False)
