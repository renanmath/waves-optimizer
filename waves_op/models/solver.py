from abc import abstractmethod, ABC
from pprint import pprint
from time import time
from waves_op.io import save_result
from waves_op.metrics import get_metrics
from waves_op.models.box import Box, Item
from waves_op.models.wave import Wave


class WavesBuilder(ABC):
    def __init__(
        self, boxes: list[Box], items: list[Item], max_capacity: int = 2000
    ) -> None:
        """
        Abstract class to build waves
        Args:
            boxes (list[Box]): list of boxes to be allocated in waves
            items (list[Item]): list of items of those boxes
            max_capacity (int): maximum quantity of items a wave can contain
        """
        self.boxes = boxes
        self.items = items
        self.max_capacity = max_capacity

    @abstractmethod
    def build_waves(self) -> list[Wave]:
        """
        Abstract method that returns waves
        Must be implemented for the child classes
        """
        pass


class WavesProblemSolver:
    def __init__(self, builder: WavesBuilder) -> None:
        """
        Interface to solve waves problem
        It receives a instance of a builder and use it to construct the waves
        """
        self.builder = builder
        self.waves: list[Wave] | None = None
        self.optimization_start: int | None = None
        self.optimization_end: int | None = None

    @property
    def max_capacity(self):
        return self.builder.max_capacity

    def solve(self, show_metrics: bool = False):
        """
        Solves waves optimization problem, using the builder
        Args:
            show_metrics (bool): a flag to indicate weather or not compute the metrics 
                                to measure waves quality            
        """
        self.optimization_start = time()
        self.waves = self.builder.build_waves()
        self.optimization_end = time()

        if show_metrics:
            metrics = get_metrics(self.waves)
            metrics["optimization_time"] = (
                self.optimization_end - self.optimization_start
            )
            pprint(metrics)

    def save_result(self, sheet_name: str):
        save_result(sheet_name=sheet_name, waves=self.waves)

    def solve_and_save(self, sheet_name: str, show_metrics: bool = False):
        self.solve(show_metrics=show_metrics)
        self.save_result(sheet_name=sheet_name)
