from abc import ABC, abstractmethod


class StrategyBase(ABC):
    @abstractmethod
    def score(self, assetid: int) -> None:
        pass
