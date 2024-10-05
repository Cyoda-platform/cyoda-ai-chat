from abc import ABC, abstractmethod

class BaseEntity(ABC):

    @abstractmethod
    def get_meta(self):
        pass

