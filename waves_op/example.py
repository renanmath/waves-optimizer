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
milp_builder_1 = MILPBuilder(boxes=boxes,items=items,max_capacity=max_capacity,use_wave_activation=True)
milp_builder_2 = MILPBuilder(boxes=boxes,items=items,max_capacity=max_capacity,use_wave_activation=False)
greedy_builder = GreedyBuilder(boxes=boxes,items=items,max_capacity=max_capacity)

# create solvers
milp_solver_1 = WavesProblemSolver(builder=milp_builder_1)
milp_solver_2 = WavesProblemSolver(builder=milp_builder_2)
greedy_solver = WavesProblemSolver(builder=greedy_builder)

# call optimization
print("\nMILP with wave activation")
milp_solver_1.solve_and_save(sheet_name="data/outputs/resposta_milp_1.xlsx",show_metrics=show_metrics)

print("\nMILP without wave activation")
milp_solver_2.solve_and_save(sheet_name="data/outputs/resposta_milp_2.xlsx",show_metrics=show_metrics)

print("\nGreedy algorithm")
greedy_solver.solve_and_save(sheet_name="data/outputs/resposta_guloso.xlsx",show_metrics=show_metrics)