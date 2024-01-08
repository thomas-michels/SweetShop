from abc import ABC, abstractmethod


class DBConnection(ABC):

    @abstractmethod
    def execute(self, sql_statement: str, values: dict = None, many: bool = False):
        """
        Method to execute query
        """

    @abstractmethod
    def commit(self):
        """
        Method to commit current changes
        """

    @abstractmethod
    def rollback(self):
        """
        Method to rollback current changes
        """
    
    @abstractmethod
    def set_client(self, sql_statement: str) -> str:
        """
        Method to set client
        """
