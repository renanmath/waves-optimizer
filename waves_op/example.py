"""
Test diferent solutions from diferent builders
"""


from waves_op.io import build_boxes_and_items
from waves_op.models.solver import WavesProblemSolver
from waves_op.optimization.heuristic.greedy import GreedyBuilder
from waves_op.optimization.milp.optimizer import MILPBuilder


# laod data
boxes, items = build_boxes_and_items("data/inputs/dados.xlsx")

# set optimization parameters
max_capacity = 2000
show_metrics = True

# create builders
milp_builder_1 = MILPBuilder(
    boxes=boxes, items=items, max_capacity=max_capacity, use_wave_activation=True
)
milp_builder_2 = MILPBuilder(
    boxes=boxes, items=items, max_capacity=max_capacity, use_wave_activation=False
)
greedy_builder_1 = GreedyBuilder(
    boxes=boxes, items=items, max_capacity=max_capacity, sort_method="cluster"
)
greedy_builder_2 = GreedyBuilder(
    boxes=boxes,
    items=items,
    max_capacity=max_capacity,
    sort_method="similarity",
    aggregation_method="max",
)
greedy_builder_3 = GreedyBuilder(
    boxes=boxes,
    items=items,
    max_capacity=max_capacity,
    sort_method="similarity",
    aggregation_method="mean",
)
greedy_builder_4 = GreedyBuilder(
    boxes=boxes,
    items=items,
    max_capacity=max_capacity,
    sort_method="similarity",
    aggregation_method="median",
)

# create solvers
milp_solver_1 = WavesProblemSolver(builder=milp_builder_1)
milp_solver_2 = WavesProblemSolver(builder=milp_builder_2)
greedy_solver_1 = WavesProblemSolver(builder=greedy_builder_1)
greedy_solver_2 = WavesProblemSolver(builder=greedy_builder_2)
greedy_solver_3 = WavesProblemSolver(builder=greedy_builder_3)
greedy_solver_4 = WavesProblemSolver(builder=greedy_builder_4)

# call optimization
print("\nMILP with wave activation")
milp_solver_1.solve_and_save(
    sheet_name="data/outputs/resposta_milp_1.xlsx", show_metrics=show_metrics
)

print("\nMILP without wave activation")
milp_solver_2.solve_and_save(
    sheet_name="data/outputs/resposta_milp_2.xlsx", show_metrics=show_metrics
)

print("\nGreedy algorithm cluster sorting method")
greedy_solver_1.solve_and_save(
    sheet_name="data/outputs/resposta_guloso_1.xlsx", show_metrics=show_metrics
)

print("\nGreedy algorithm similarity sorting method with aggregation function max")
greedy_solver_2.solve_and_save(
    sheet_name="data/outputs/resposta_guloso_2.xlsx", show_metrics=show_metrics
)

print("\nGreedy algorithm similarity sorting method with aggregation function mean")
greedy_solver_3.solve_and_save(
    sheet_name="data/outputs/resposta_guloso_3.xlsx", show_metrics=show_metrics
)

print("\nGreedy algorithm similarity sorting method with aggregation function median")
greedy_solver_4.solve_and_save(
    sheet_name="data/outputs/resposta_guloso_4.xlsx", show_metrics=show_metrics
)
