"""
Input / Output
"""
import pandas as pd

from waves_op.models.box import Box, Item, ItemInBox
from waves_op.models.wave import Wave


def read_sheet(path: str):
    df = pd.read_excel(path)

    return df


def build_boxes_and_items(path: str) -> tuple[list[Box], list[Item]]:
    print("Loading data")
    df = read_sheet(path)

    boxes: list[Box] = list()
    items: list[Item] = list()

    boxes_ids = list(df["Caixa Id"].unique())
    for box_id in boxes_ids:
        box = Box(box_id=box_id, content=list())
        result = df[df["Caixa Id"] == box_id]

        for index in result.index:
            sku = result["Item"][index].split("sku-")[-1]
            qtd = result["Peças"][index]
            new_item = Item(sku=sku)
            new_item_in_box = ItemInBox(item=new_item, quantity=qtd)
            box.content.append(new_item_in_box)
            items.append(new_item)

        boxes.append(box)

    return boxes, items


def parse_waves_to_sheet(waves: list[Wave], sheet_name: str):
    boxes_info = list()
    waves_info = list()
    for wave in waves:
        wave_id = wave.index
        for box in wave.boxes:
            boxes_info.append(box.box_id)
            waves_info.append(wave_id)
    info = {"Caixa Id": boxes_info, "Onda": waves_info}
    df = pd.DataFrame(info)
    df.to_excel(sheet_name, index=False)


def save_result(sheet_name: str, waves: list[Wave] | None = None):
    """
    Parse the waves to a sheet
    """
    if waves is None:
        raise ValueError("No waves has been build yet")

    parse_waves_to_sheet(waves=waves, sheet_name=sheet_name)

