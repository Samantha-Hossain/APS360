import json, shutil
from pathlib import Path

PROJECT = Path(__file__).resolve().parent.parent          # the Project folder
RAW = PROJECT / "Dataset" / "Rosemary.v5-final-version.coco"
OUT = PROJECT / "Dataset" / "clean" / "rosemary"
OUT.mkdir(parents=True, exist_ok=True)

kept = skipped = 0
for split in ["train", "valid", "test"]:
    folder = RAW / split
    coco = json.loads((folder / "_annotations.coco.json").read_text())

    cats = {c["id"]: c["name"] for c in coco["categories"]}
    print(split, "categories:", cats)                     # check the exact spelling

    # collect the set of category names used by each image
    names_per_image = {}
    for ann in coco["annotations"]:
        names_per_image.setdefault(ann["image_id"], set()).add(cats[ann["category_id"]])

    for img in coco["images"]:
        names = names_per_image.get(img["id"], set())
        if names == {"Rosemary"}:                         # only healthy rosemary, nothing else
            src = folder / img["file_name"]
            shutil.copy(src, OUT / f"{split}_{img['file_name']}")   # split prefix avoids name clashes
            kept += 1
        else:
            skipped += 1                                  # diseased, mixed, or no annotation

print(f"Kept {kept} images, skipped {skipped}")