from abc import abstractmethod

from middleware.repository.entity.entity import BaseEntity


class CyodaEntity(BaseEntity):

    @abstractmethod
    def get_cyoda_meta(self):
        pass

