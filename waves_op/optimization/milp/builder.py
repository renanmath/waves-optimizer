"""
Build optimization MILP solver
"""

from ortools.linear_solver import pywraplp

import math
from waves_op.models.box import Box, Item
from waves_op.models.wave import Wave


class WavesProblemBuilder:
    def __init__(
        self,
        boxes: list[Box],
        items: list[Item],
        max_capacity: int = 2000,
        use_wave_activation: bool = True,
    ) -> None:
        """
        Class to construct the MILP formulation of waves problem
        It sets the variables, the constraints and the objective function
        based on the data of boxes and items
        Args:
            boxes (list[Box]): list of boxes to be allocated in waves
            items (list[Item]): list of items of those boxes
            max_capacity (int): maximum quantity of items a wave can contain
            use_wave_activation (bool): flag to indicate whether to use or not the y variables in the MILP formulation
        """

        self.boxes = boxes
        self.items = items
        self.max_capacity = max_capacity
        self.use_wave_activation = use_wave_activation
        self.waves = self.build_empty_waves()

        self.variables = {"x": list(), "y": list(), "z": list()}

    @property
    def num_boxes(self):
        return len(self.boxes)

    @property
    def num_items(self):
        return len(self.items)

    @property
    def num_waves(self):
        return len(self.waves)

    def build_empty_waves(self) -> list[Wave]:
        total_sum = sum(box.total for box in self.boxes)
        num_waves = math.ceil(total_sum / self.max_capacity)

        waves: list[Wave] = list()
        for index in range(num_waves):
            new_wave = Wave(
                index=index, active=False, boxes=list(), max_capacity=self.max_capacity
            )
            waves.append(new_wave)

        return waves

    def build_optimization_problem(self):
        """
        Create a solver, build variables, set constraints and define objective function
        Return:
            solver: instance of MILP solver
        """
        solver = pywraplp.Solver.CreateSolver("CBC")

        if solver is None:
            raise ValueError("Not a valid solver")

        self.create_variables(solver=solver)
        self.set_constraints(solver=solver)
        self.set_objective_function(solver=solver)

        return solver

    def create_variables(self, solver):
        """
        Create all variables for the MILP problem
        All variables are binary
        x_{i,j}: the i-th box is allocated in the j-th wave
        y_{j}: the j-th wave is activated
        z_{k,j}: the k-th item is allocated in the j-th wave
        If use_wave_activation flag is False, y variables are ignored
        """

        # x variables
        for i_index in range(self.num_boxes):
            self.variables["x"].append(list())
            for j_index in range(self.num_waves):
                var_name = f"x[{i_index}, {j_index}]"
                x_var = solver.IntVar(0, 1, var_name)
                self.variables["x"][i_index].append(x_var)

        # y variables
        for j_index in range(self.num_waves):
            var_name = f"y[{j_index}]"
            y_var = solver.IntVar(0, 1, var_name)
            self.variables["y"].append(y_var)

        # z variables
        for k_index in range(self.num_items):
            self.variables["z"].append(list())
            for j_index in range(self.num_waves):
                var_name = f"z[{k_index}, {j_index}]"
                z_var = solver.IntVar(0, 1, var_name)
                self.variables["z"][k_index].append(z_var)

    def set_constraints(self, solver):
        """Set all constraints for the problem"""
        self.constraint_boxes_must_be_assigned_to_waves(solver=solver)
        self.constraint_boxes_must_be_assigned_only_to_active_waves(solver=solver)
        self.constraint_if_box_in_wave_item_must_be_in_wave(solver=solver)
        self.constraint_wave_must_obey_max_capacity(solver=solver)

    def constraint_boxes_must_be_assigned_to_waves(self, solver):
        """
        Ensures each box must be allocated in exactly one wave
        LaTex Formula:
            \sum_{j \in J} x_{i,j} = 1 \forall i \in I
        """

        for i_index in range(self.num_boxes):
            constraint = solver.Constraint(1, 1)
            for j_index in range(self.num_waves):
                x_i_j = self.variables["x"][i_index][j_index]
                constraint.SetCoefficient(x_i_j, 1)

    def constraint_boxes_must_be_assigned_only_to_active_waves(self, solver):
        """
        If use_wave_activation is True, ensures only activated waves can be used to carry boxes
        LaTex Formula:
            x_{i,j} \le y_j \forall i \in I \forall j \in J
        """
        if not self.use_wave_activation:
            return None

        for j_index in range(self.num_waves):
            y_j = self.variables["y"][j_index]

            for i_index in range(self.num_boxes):
                constraint = solver.Constraint(-solver.infinity(), 0)
                constraint.SetCoefficient(y_j, -1)
                x_i_j = self.variables["x"][i_index][j_index]
                constraint.SetCoefficient(x_i_j, 1)

    def constraint_if_box_in_wave_item_must_be_in_wave(self, solver):
        """
        Ensures that, if a item is allocated in one wave, its box is also allocated in that wave
        LaTex Formula:
            Z_{k,j} \ge x_{i,j} \forall k \in K_i \forall j in J
        """

        for j_index in range(self.num_waves):
            for i_index in range(self.num_boxes):
                box_i = self.boxes[i_index]
                for k_index in range(self.num_items):
                    item_k = self.items[k_index]
                    if box_i.check_if_item_is_in_box(item_k):
                        constraint = solver.Constraint(-solver.infinity(), 0)
                        x_i_j = self.variables["x"][i_index][j_index]
                        z_k_j = self.variables["z"][k_index][j_index]
                        constraint.SetCoefficient(x_i_j, 1)
                        constraint.SetCoefficient(z_k_j, -1)

    def constraint_wave_must_obey_max_capacity(self, solver):
        """
        Ensures waves will respect maximum quantity of items
        LaTex Formula:
            \sum_{i \in I} x_{i,j} \cdot p_i \le c \cdot y_{j} \forall j \in J
        """
        for j_index in range(self.num_waves):
            constraint = solver.Constraint(
                -solver.infinity(),
                0 + 1 * (not self.use_wave_activation) * self.max_capacity,
            )
            if self.use_wave_activation:
                y_j = self.variables["y"][j_index]
                constraint.SetCoefficient(y_j, -self.max_capacity)
            for i_index in range(self.num_boxes):
                box_i = self.boxes[i_index]
                total_i = box_i.total
                x_i_j = self.variables["x"][i_index][j_index]
                constraint.SetCoefficient(x_i_j, total_i)

    def set_objective_function(self, solver):
        """
        Define objective function
        The goal is to minimize the distribution of items across waves,
        i.e., minimize the quantity of items with same sku in different waves
        """
        objective = solver.Objective()

        for j_index in range(self.num_waves):
            for k_index in range(self.num_items):
                z_k_j = self.variables["z"][k_index][j_index]
                objective.SetCoefficient(z_k_j, 1)

        objective.SetMinimization()
