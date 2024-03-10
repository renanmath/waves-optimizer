from pydantic import PositiveInt
from pydantic.dataclasses import dataclass


@dataclass
class Item:
    sku: str


@dataclass
class ItemInBox:
    item: Item
    quantity: PositiveInt


@dataclass
class Box:
    box_id: int
    content: list[ItemInBox]

    @property
    def total(self) -> int:
        return sum(prod.quantity for prod in self.content)

    @property
    def skus(self):
        return [prod.item.sku for prod in self.content]

    def check_if_item_is_in_box(self, item: Item):
        for prod in self.content:
            if prod.item.sku == item.sku:
                return True

        return False


@dataclass
class SkuInfo:
    sku: str
    boxes: list[Box]

    @property
    def total(self):
        return sum(box.total for box in self.boxes)

    @property
    def total_sku(self):
        total = 0
        for box in self.boxes:
            for prod in box.content:
                if prod.item.sku == self.sku:
                    total += prod.quantity

        return total

    @property
    def sorted_boxes(self):
        return sorted(self.boxes, key=lambda box: box.total, reverse=True)

    @property
    def all_skus(self):
        all_skus: list[str] = list()
        for box in self.boxes:
            all_skus.extend(box.skus)

        return list(set(all_skus))
