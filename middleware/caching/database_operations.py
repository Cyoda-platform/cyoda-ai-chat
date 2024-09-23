from abc import ABC, abstractmethod
from typing import List, Any, Optional


class DatabaseOperations(ABC):
    @abstractmethod
    def write(self, entities: List[Any]) -> bool:
        """
        Writes a list of entities to the database.

        :param entities: A list of entities to write back.
        :return: True if the write operation was successful, False otherwise.
        """
        pass

    @abstractmethod
    def read(self, key: str) -> Optional[Any]:
        """
        Reads an entity from the database based on the key.

        :param key: The key of the entity to read.
        :return: The entity if found, or None if not.
        """
        pass

    @abstractmethod
    def delete(self, key: str) -> bool:
        """
        Deletes an entity from the database based on the key.

        :param key: The key of the entity to delete.
        :return: True if the delete operation was successful, False otherwise.
        """
        pass

    @abstractmethod
    def clear(self) -> None:
        """
        Clears all entries from the database.
        """
        pass