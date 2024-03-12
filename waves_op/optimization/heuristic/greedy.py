from collections import defaultdict

import numpy as np
from waves_op.metrics import get_sku_distribution_dict
from waves_op.models.box import Box, Item, SkuInfo
from waves_op.models.wave import Wave
from waves_op.models.solver import WavesBuilder


class GreedyBuilder(WavesBuilder):
    def __init__(
        self,
        boxes: list[Box],
        items: list[Item],
        max_capacity: int = 2000,
        sort_method: str = "cluster",
        aggregation_method: str = "max",
    ) -> None:
        """
        Builder that uses heuristic algorithms to construct the waves.
        The construction is done in two phases.
        In the first one, boxes are allocated in waves using a greedy algorithm.
        Then, the boxes from the initial waves are permuted across waves,
        in order to minimize the number of skus in different waves.
        The greedy algorithm takes the current wave and insert on it the boxes
        where the skus are more related to the skus already present on the wave.
        To do so, the skus are sorted using a sort_method, and the one with the best value is selected.
        There are two sort methods:
        - sort by cluster: we look to skus that are already in the wave, sorted by size of the boxes
        - sort by similarity: we look to skus that maximize a similarity metric, which measures the ratio of
        boxes if that sku out of wave by the boxes with that sku inside wave
        """
        super().__init__(boxes, items, max_capacity)
        self.skus_info: list[SkuInfo] = self.build_sku_info()
        self.allocated_boxes: list[Box] = list()
        self.allocated_skus: list[str] = list()
        self.waves: list[Wave] = list()

        self.sort_method = sort_method
        self.aggregation_method = aggregation_method

        self.aggregation_functions_map = {
            "max": lambda vector: max(vector),
            "mean": lambda vector: np.mean(vector),
            "median": lambda vector: np.median(vector),
        }

    def apply_cluster_sorting_method(
        self, info: SkuInfo, previous_sku: str, last_skus: list[str]
    ):
        return (
            info.sku in last_skus,
            info.sku == previous_sku,
            previous_sku in info.all_skus,
            info.total,
            info.total_sku,
            len(info.boxes),
        )

    def apply_similarity_sorting_method(self, info: SkuInfo, wave: Wave):
        return self.aggregation_functions_map[self.aggregation_method](
            wave.get_similarity_vector(info)
        )

    def apply_sorting_method(
        self,
        info: SkuInfo,
        previous_wave: Wave,
        previous_sku: str,
        last_skus: list[str],
    ):

        if self.sort_method == "cluster":
            return self.apply_cluster_sorting_method(
                info=info, previous_sku=previous_sku, last_skus=last_skus
            )
        elif self.sort_method == "similarity":
            return self.apply_similarity_sorting_method(info=info, wave=previous_wave)

    def build_sku_info(self):
        raw_info = defaultdict(list)
        for box in self.boxes:
            for prod in box.content:
                if box not in raw_info[prod.item.sku]:
                    raw_info[prod.item.sku].append(box)

        skus_info = [SkuInfo(sku=sku, boxes=boxes) for sku, boxes in raw_info.items()]
        return skus_info

    def allocate_box_in_wave(self, box: Box, wave: Wave):
        if box not in self.allocated_boxes:
            wave.boxes.append(box)
            self.allocated_boxes.append(box)

    def build_initial_waves(self) -> list[Wave]:
        """
        Construct initial solution using a greedy algorithm
        Returns:
            list[Wave]
        """

        previous_wave = Wave(
            index=0, active=True, boxes=list(), max_capacity=self.max_capacity
        )
        skus_info_copy = self.skus_info.copy()
        previous_sku = ""

        while skus_info_copy:
            last_skus = list(previous_wave.sku_count.keys())
            skus_info_copy.sort(
                key=lambda info: self.apply_sorting_method(
                    info, previous_wave, previous_sku, last_skus
                ),
                reverse=True,
            )

            sku_info = skus_info_copy.pop(0)

            previous_wave, next_wave, use_next_wave = self.fill_wave_from_sku_info(
                sku_info=sku_info, previous_wave=previous_wave
            )

            self.cross_swap_boxes(previous_wave, next_wave)

            previous_sku = sku_info.sku
            if sku_info.boxes:
                skus_info_copy.append(sku_info)
            else:
                self.allocated_skus.append(sku_info.sku)

            if use_next_wave:
                self.waves.append(previous_wave)
                previous_wave = next_wave
                sku_count = next_wave.sku_count
                sku_count_as_list = [
                    (sku, count)
                    for sku, count in sku_count.items()
                    if sku not in self.allocated_skus
                ]
                if not sku_count_as_list:
                    previous_sku = ""
                else:
                    sku_count_as_list.sort(key=lambda data: data[1], reverse=True)
                    previous_sku = sku_count_as_list[0][0]

        if len(self.allocated_boxes) < len(self.boxes):
            raise ValueError("Not all boxes allocated in waves")

        return self.waves

    def fill_wave_from_sku_info(self, sku_info: SkuInfo, previous_wave: Wave):
        """
        Check if all boxes from the sku can be fitted in the current wave
        If not, create a new wave to allocate them
        """
        next_wave = Wave(
            index=previous_wave.index + 1,
            active=True,
            boxes=list(),
            max_capacity=self.max_capacity,
        )
        use_next_wave = False
        not_allocated_boxes: list[Box] = list()

        remaining_boxes = [
            box for box in sku_info.boxes if box not in self.allocated_boxes
        ]
        total_of_boxes = sum(b.total for b in remaining_boxes)
        if total_of_boxes <= previous_wave.remaining_capacity:
            wave = previous_wave
        elif total_of_boxes <= next_wave.remaining_capacity:
            wave = next_wave
            use_next_wave = True
        else:
            not_allocated_boxes.extend(remaining_boxes)

        for box in remaining_boxes:
            self.allocate_box_in_wave(box, wave)

        sku_info.boxes = not_allocated_boxes

        return previous_wave, next_wave, use_next_wave

    def cross_swap_boxes(
        self, previous_wave: Wave, next_wave: Wave, both_ways: bool = True
    ):
        """
        Perform permutations in the boxes across waves,
        aiming to minimize sku distribution
        """

        changed = True
        while not changed:
            sku_distribution = get_sku_distribution_dict(
                waves=[previous_wave, next_wave]
            )
            changed = False
            for sku, count in sku_distribution.items():
                if count > 1:
                    boxes_in_previous = [
                        box for box in previous_wave.boxes if sku in box.skus
                    ]
                    boxes_in_next = [box for box in next_wave.boxes if sku in box.skus]

                    if previous_wave.remaining_capacity < next_wave.remaining_capacity:
                        origin_wave, destination_wave = previous_wave, next_wave
                        list_of_boxes, other_boxes = boxes_in_previous, boxes_in_next
                    else:
                        origin_wave, destination_wave = next_wave, previous_wave
                        list_of_boxes, other_boxes = boxes_in_next, boxes_in_previous

                    swapped = self.try_swap_boxes_across_waves(
                        list_of_boxes, origin_wave, destination_wave
                    )
                    if swapped:
                        changed = True
                        break
                    elif both_ways:
                        swapped = self.try_swap_boxes_across_waves(
                            other_boxes, destination_wave, origin_wave
                        )
                        if swapped:
                            changed = True
                            break

    def try_swap_boxes_across_waves(
        self, list_of_boxes: list[Box], origin_wave: Wave, destination_wave: Wave
    ):
        """
        Check if boxes from different waves can be swapped
        To avoid increase sku distribution, this method grantees
        all additional boxes linked to the original boxes are swapped too
        A box is linked to the original boxes if it contains any sku present in them
        """
        total_to_move = sum(box.total for box in list_of_boxes)
        new_capacity = origin_wave.remaining_capacity + total_to_move
        total_to_accept = max(total_to_move - destination_wave.remaining_capacity, 0)

        if total_to_accept > new_capacity:
            return False

        # create enough space in destination wave
        boxes_to_swap: list[Box] = list()
        swap_total = 0
        other_waves = [
            wave for wave in self.waves if wave not in [origin_wave, destination_wave]
        ]

        possible_to_swap = False
        for box in destination_wave.boxes:

            if any(any(sku in box.skus for sku in b.skus) for b in list_of_boxes):
                continue

            if self.check_if_box_skus_appears_in_other_waves(box, other_waves):
                continue

            if swap_total + box.total <= new_capacity:
                boxes_to_swap.append(box)
                swap_total += box.total

            if swap_total >= total_to_accept and boxes_to_swap:
                possible_to_swap = True
                break

        if not possible_to_swap:
            return False

        # check for boxes linked to boxes to swap by any sku
        remaining_boxes = [
            box for box in destination_wave.boxes if box not in boxes_to_swap
        ]
        leftovers = list()
        appended = True
        while appended:
            appended = False
            for box in remaining_boxes:
                if any(
                    any(sku in box.skus for sku in b.skus) for b in origin_wave.boxes
                ):
                    appended = True
                    leftovers.append(box)

            remaining_boxes = [
                box
                for box in destination_wave.boxes
                if box not in boxes_to_swap + leftovers
            ]

        if sum(b.total for b in leftovers) + swap_total > new_capacity:
            possible_to_swap = False
        else:
            for box in leftovers:
                if self.check_if_box_skus_appears_in_other_waves(box, other_waves):
                    possible_to_swap = False
                    break

        if possible_to_swap:
            boxes_to_swap.extend(leftovers)
        else:
            return False

        remaining_boxes = [
            box for box in destination_wave.boxes if box not in boxes_to_swap
        ]
        for box in remaining_boxes:
            if any(any(sku in box.skus for sku in b.skus) for b in boxes_to_swap):
                possible_to_swap = False

        if possible_to_swap:
            new_boxes_in_origin = [
                box for box in origin_wave.boxes if box not in list_of_boxes
            ] + boxes_to_swap
            new_boxes_in_destination = [
                box for box in destination_wave.boxes if box not in boxes_to_swap
            ] + list_of_boxes

            origin_wave.boxes = new_boxes_in_origin
            destination_wave.boxes = new_boxes_in_destination

            return True
        else:
            return False

    def check_if_box_skus_appears_in_other_waves(
        self, box: Box, other_waves: list[Wave]
    ):
        tiny_wave = Wave(
            index=2 * len(other_waves) + 3,
            active=False,
            boxes=[box],
            max_capacity=self.max_capacity,
        )

        for other_wave in other_waves:
            sku_count = get_sku_distribution_dict(waves=[tiny_wave, other_wave])
            repeated_sku = [s for s, v in sku_count.items() if v > 1]
            if repeated_sku:
                return True

        return False

    def refine_waves(self, waves: list[Wave]):
        """
        Perform moves across waves to minimize sku distribution
        """
        for index, wave in enumerate(waves):
            for other_index, other_wave in enumerate(waves):
                if index == other_index:
                    continue

                self.cross_swap_boxes(
                    previous_wave=wave, next_wave=other_wave, both_ways=True
                )

    def build_waves(self) -> list[Wave]:
        waves = self.build_initial_waves()
        self.refine_waves(waves)

        return waves
