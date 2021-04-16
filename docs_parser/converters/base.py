import abc

from ..objects import ObjectDefinition, Resource, Operation


class ConverterBase(metaclass=abc.ABCMeta):

    def __init__(self, resources: list[Resource]):
        self._resources = resources

    @abc.abstractmethod
    def dirname(self, op: Operation) -> str:
        pass

    @abc.abstractmethod
    def filename(self, obj: ObjectDefinition) -> str:
        pass

    @abc.abstractmethod
    def contents(self, obj: ObjectDefinition, op: Operation) -> str:
        pass
