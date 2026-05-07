"""Plot cumulative solved instances over time for 16x16 boards."""

from __future__ import annotations

from common import DIFFICULTIES, DIFFICULTY_COLORS, IMAGE_DIR, as_float, configure_matplotlib, is_true, load_rows, save_figure


def main() -> None:
    configure_matplotlib()
    import matplotlib.pyplot as plt

    rows = [row for row in load_rows() if row.get("size") == "16x16"]
    fig, ax = plt.subplots(figsize=(6.8, 3.4))

    for difficulty in DIFFICULTIES:
        solve_times = sorted(
            as_float(row["solve_time"])
            for row in rows
            if row.get("difficulty") == difficulty and is_true(row.get("validation_passed"))
        )
        if not solve_times:
            continue
        x_values = [0.0] + solve_times
        y_values = [0] + list(range(1, len(solve_times) + 1))
        ax.step(
            x_values,
            y_values,
            where="post",
            linewidth=2.0,
            color=DIFFICULTY_COLORS[difficulty],
            label=difficulty,
        )

    ax.set_title("Cumulative Solved Instances on 16x16 Boards")
    ax.set_xlabel("Solve time threshold (s)")
    ax.set_ylabel("Solved instances")
    ax.set_ylim(bottom=0)
    ax.legend(frameon=True)
    save_figure(fig, IMAGE_DIR / "tracks_cumulative_solved_16x16.png")


if __name__ == "__main__":
    main()
