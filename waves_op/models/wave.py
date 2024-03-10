from collections import defaultdict
from pydantic import NonNegativeInt, PositiveInt
from pydantic.dataclasses import dataclass

from waves_op.models.box import Box


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
