import json

from ...config import (
    CHECKPOINT_FILE,
    OUTPUT_DIR,
    CATEGORIES
)

def load_checkpoint() -> dict:

    if not CHECKPOINT_FILE.exists():

        return {
            "categories": {
                category: 0
                for category in CATEGORIES
            }
        }

    with CHECKPOINT_FILE.open(
        "r",
        encoding="utf-8"
    ) as f:

        checkpoint = json.load(f)

    for category in CATEGORIES:

        if category not in checkpoint["categories"]:

            checkpoint["categories"][category] = 0

    return checkpoint

def save_checkpoint(
    checkpoint: dict
):

    OUTPUT_DIR.mkdir(
        parents=True,
        exist_ok=True
    )

    temp_file = CHECKPOINT_FILE.with_suffix(
        ".tmp"
    )

    with temp_file.open(
        "w",
        encoding="utf-8"
    ) as f:

        json.dump(
            checkpoint,
            f,
            indent=2,
            ensure_ascii=False
        )

    temp_file.replace(
        CHECKPOINT_FILE
    )