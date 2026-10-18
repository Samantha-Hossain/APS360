"""
Copies only the usable images from each YOLO-format herb dataset into
Dataset/clean/<herb>/ . Originals are never modified.

An image is kept only if it has at least one annotation and ALL of its
annotations belong to the classes listed for that dataset (KEEP below).
Images with no annotation, or with other classes, are skipped.
"""
import shutil
from pathlib import Path
import yaml

PROJECT = Path(__file__).resolve().parent.parent
DATA = PROJECT / "Dataset"
OUT_ROOT = DATA / "clean"

# herb -> list of (filename prefix, dataset folder, class names to keep)
# Use None for "keep" if the dataset has exactly one class.
# If a dataset has several classes, the script will print them and skip it;
# then put the herb's class name(s) in a set, e.g. {"basil"}.
SOURCES = {
    "basil":       [("basil",  "basil.v1i.yolov12",                    None)],
    "bay_leaf":    [("bay1",   "Bay Leaf.v2i.yolov12",                 None),
                    ("bay2",   "Bay Leaf -Defne yarpagi-.v1i.yolov12", None)],
    "dill":        [("dill",   "Dill.v1i.yolov12",                     None)],
    "green_onion": [("gonion", "greenonion.v1i.yolov12",               None)],
}

summary = []
for herb, datasets in SOURCES.items():
    out = OUT_ROOT / herb
    out.mkdir(parents=True, exist_ok=True)
    for prefix, folder, keep in datasets:
        raw = DATA / folder
        if not (raw / "data.yaml").exists():
            print(f"[!] {folder}: data.yaml not found, check the folder name. Skipping.")
            continue
        names = yaml.safe_load((raw / "data.yaml").read_text())["names"]
        if isinstance(names, dict):
            names = [names[k] for k in sorted(names)]
        print(f"{folder}: classes = {names}")
        if keep is None:
            if len(names) != 1:
                print(f"[!] {folder} has several classes. Set the class name(s) to keep "
                      f"for it in SOURCES, then rerun. Skipping for now.")
                continue
            keep = set(names)
        keep_ids = {names.index(n) for n in keep}

        kept = no_label = other_class = 0
        for split in ["train", "valid", "test"]:
            img_dir, lbl_dir = raw / split / "images", raw / split / "labels"
            if not img_dir.exists():
                continue
            images = {p.stem: p for p in img_dir.iterdir() if p.is_file()}
            for stem, img in images.items():
                lbl = lbl_dir / f"{stem}.txt"
                lines = lbl.read_text().splitlines() if lbl.exists() else []
                ids = {int(float(l.split()[0])) for l in lines if l.strip()}
                if not ids:
                    no_label += 1
                elif ids <= keep_ids:
                    shutil.copy(img, out / f"{prefix}_{split}_{img.name}")
                    kept += 1
                else:
                    other_class += 1
        total = kept + no_label + other_class
        print(f"   kept {kept} of {total}  (no annotation: {no_label}, other classes: {other_class})\n")
        summary.append((herb, folder, total, kept, no_label, other_class))

print("SUMMARY (herb, dataset, total, kept, no annotation, other classes)")
for row in summary:
    print(*row, sep=" | ")
(OUT_ROOT / "summary.txt").write_text(
    "herb | dataset | total | kept | no annotation | other classes\n"
    + "\n".join(" | ".join(map(str, r)) for r in summary))
