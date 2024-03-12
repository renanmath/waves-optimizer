# About

This project aims to solve the waves allocation problem: given a set a items, distributed in boxes, the goal is to allocate the boxes in waves, with a pre-determined maximum capacity. The allocation must be in a such way that the number of boxes containing items with same sku in different waves is minimum as possible. In other words, we want to minimize the distribution of skus across the waves. 

To do so, we develop two solutions, with variations. The first solution is a MILP (Mix Integer Linear Programming) formulation. The implementation is done in [optimizer.py](waves_op/optimization/milp/optimizer.py). There are two variations of this formulation. The second one is a greedy algorithm, which can be seen [greedy.py](waves_op/optimization/heuristic/greedy.py). This solver has four variations, one of them showed better performance then the MILP solver.

We tested all implementations and its variations in [example.py](waves_op/example.py). The results are salved in the [output folder](data/outputs). The data to run the tests is in the [input folder](data/inputs).

All important details about the solution can be read in the docstrings around the code. 
