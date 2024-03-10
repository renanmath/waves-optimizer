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
        self.boxes = boxes
        self.items = items
        self.max_capacity = max_capacity

    @abstractmethod
    def build_waves(self) -> list[Wave]:
        pass


class WavesProblemSolver:
    def __init__(self, builder: WavesBuilder) -> None:
        self.builder = builder
        self.waves: list[Wave] | None = None
        self.optimization_start: int | None = None
        self.optimization_end: int | None = None

    @property
    def max_capacity(self):
        return self.builder.max_capacity

    def solve(self, show_metrics: bool = False):
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
