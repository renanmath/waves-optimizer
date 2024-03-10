from pprint import pprint
from waves_op.io import save_result
from waves_op.models.box import Box, Item
from waves_op.models.solver import WavesBuilder
from waves_op.models.wave import Wave
from waves_op.optimization.milp.builder import WavesProblemBuilder


class WavesOptimizer:
    def __init__(
        self, boxes: list[Box], items: list[Item],
        max_capacity: int = 2000,
        use_wave_activation:bool=True
    ) -> None:
        self.boxes = boxes
        self.items = items
        self.max_capacity = max_capacity
        self.use_wave_activation = use_wave_activation

        self.builder = WavesProblemBuilder(self.boxes, self.items, self.max_capacity)
        self.solver = self.builder.build_optimization_problem()
        self.activated_waves: list[Wave] | None = None

    @property
    def variables(self):
        return self.builder.variables

    def solve_optimization_problem(self):
        status = self.solver.Solve()

        if status in [self.solver.FEASIBLE, self.solver.OPTIMAL]:
            self.activated_waves = self.build_solution_from_solver()
            return self.activated_waves
        else:
            raise InfeasibleProblemException(
                "Optimizer did not found a feasible solution"
            )

    def build_solution_from_solver(self):

        activated_waves: list[Wave] = list()
        for j_index in range(self.builder.num_waves):
            y_j = self.variables["y"][j_index]
            if not self.use_wave_activation or y_j.solution_value() > 0:
                # wave was activated
                wave = self.builder.waves[j_index]
                wave.active = True
                activated_waves.append(wave)
                for i_index in range(self.builder.num_boxes):
                    x_i_j = self.variables["x"][i_index][j_index]
                    if x_i_j.solution_value() > 0:
                        # box was assigned to wave
                        box = self.boxes[i_index]
                        wave.boxes.append(box)

        return activated_waves

    def save_result(self, sheet_name: str):
        save_result(sheet_name=sheet_name, waves=self.activated_waves)


class MILPBuilder(WavesBuilder):
    def __init__(
        self, boxes: list[Box], items: list[Item],
        max_capacity: int = 2000, use_wave_activation:bool = True
    ) -> None:
        super().__init__(boxes, items, max_capacity)
        self.use_wave_activation = use_wave_activation

    def build_waves(self) -> list[Wave]:
        optimizer = WavesOptimizer(self.boxes, self.items, self.max_capacity,self.use_wave_activation)
        return optimizer.solve_optimization_problem()


class InfeasibleProblemException(Exception):
    pass

