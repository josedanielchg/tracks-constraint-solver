"""Dataset generation helpers for Tracks."""

from __future__ import annotations

import random
from pathlib import Path

from .generate_instance import generate_tracks_instance, save_tracks_instance


def generate_dataset(
    output_dir: str | Path,
    *,
    count: int,
    rows: int,
    cols: int,
    seed: int | None = None,
    prefix: str = "tracks",
    min_path_length: int | None = None,
) -> list[Path]:
    """Generate a dataset of Tracks instances and write them to disk."""
    rng = random.Random(seed)
    target_dir = Path(output_dir)
    target_dir.mkdir(parents=True, exist_ok=True)

    # Each file gets its own seed so the dataset is reproducible but varied.
    written_files: list[Path] = []
    for index in range(1, count + 1):
        instance = generate_tracks_instance(
            rows,
            cols,
            seed=rng.randint(0, 10**9),
            min_path_length=min_path_length,
        )
        file_path = target_dir / f"{prefix}_{index:03d}.txt"
        written_files.append(save_tracks_instance(instance, file_path))

    return written_files
