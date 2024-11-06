from enum import Enum
from abc import ABC, abstractmethod


class Health(Enum):
    OK = 'ok'
    NOT_OK = 'not_ok'


class HealthMixin(ABC):
    @abstractmethod
    def health(self) -> Health:
        """
        Check whether the object is capable of handing method calls.
        The health check mechanism is applicable for objects that interact with
        third-party services and resources that can be unavailable during the
        object lifecycle.

        :return:
        """
        pass
