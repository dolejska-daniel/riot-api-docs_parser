import abc

from docs_parser.objects import ObjectDefinition, Resource


class ConverterBase(metaclass=abc.ABCMeta):

    def __init__(self, resources: list[Resource]):
        self._resources = resources

    @abc.abstractmethod
    def dirname(self, obj: ObjectDefinition) -> str:
        pass

    @abc.abstractmethod
    def filename(self, obj: ObjectDefinition) -> str:
        pass

    @abc.abstractmethod
    def contents(self, obj: ObjectDefinition) -> str:
        pass
