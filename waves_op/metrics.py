from collections import defaultdict
from waves_op.models.wave import Wave
import numpy as np


def compute_usage_ratio_metrics(waves: list[Wave]):

    return {
        "mean": np.mean([wave.usage_ratio for wave in waves]),
        "median": np.median([wave.usage_ratio for wave in waves]),
        "minimum": min([wave.usage_ratio for wave in waves]),
        "maximum": max([wave.usage_ratio for wave in waves]),
    }


def compute_sku_total_distribution(waves: list[Wave]):
    sku_general_count = get_sku_distribution_dict(waves)

    return sum(v - 1 for v in sku_general_count.values())


def get_sku_distribution_dict(waves: list[Wave]):
    sku_general_count = defaultdict(int)
    for wave in waves:
        sku_wave_count = wave.sku_count
        for sku in sku_wave_count:
            sku_general_count[sku] += 1
    return sku_general_count


def get_metrics(waves: list[Wave]):
    return {
        "number_of_waves": len(waves),
        "usage_ratio": compute_usage_ratio_metrics(waves),
        "sku_distribution": compute_sku_total_distribution(waves),
    }
