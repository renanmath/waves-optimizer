from collections import defaultdict
from pydantic import NonNegativeInt, PositiveInt
from pydantic.dataclasses import dataclass

from waves_op.models.box import Box, SkuInfo


@dataclass
class Wave:
    index: NonNegativeInt
    active: bool
    boxes: list[Box]
    max_capacity: PositiveInt

    @property
    def total_items(self):
        return sum(box.total for box in self.boxes)

    @property
    def remaining_capacity(self):
        return self.max_capacity - self.total_items

    @property
    def usage_ratio(self):
        return self.total_items / self.max_capacity

    @property
    def sku_count(self):
        sku_count = defaultdict(int)
        for box in self.boxes:
            for prod in box.content:
                sku_count[prod.item.sku] += prod.quantity

        return sku_count

    def compute_sku_similarity(self, sku: str, boxes: list[Box]):
        sku_count = self.sku_count
        wave_total = self.total_items

        if wave_total == sku_count[sku]:
            return float("inf")

        boxes_total = sum(
            sum(prod.quantity for prod in box.content if prod.item.sku == sku)
            for box in boxes
        )

        return (boxes_total + sku_count[sku]) / (wave_total - sku_count[sku])

    def get_similarity_vector(self, sku_info: SkuInfo):
        similarities: list[float] = [
            self.compute_sku_similarity(sku=sku, boxes=sku_info.boxes)
            for sku in sku_info.all_skus
        ]

        return similarities
