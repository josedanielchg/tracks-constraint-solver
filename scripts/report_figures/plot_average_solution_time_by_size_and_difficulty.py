"""Plot average exact-flow solve time by board size and difficulty."""

from __future__ import annotations

from common import DIFFICULTIES, DIFFICULTY_COLORS, IMAGE_DIR, configure_matplotlib, grouped, load_rows, mean_solve_time, save_figure


def main() -> None:
    configure_matplotlib()
    import matplotlib.pyplot as plt

    rows = [row for row in load_rows() if row.get("generation_status") != "error"]
    fig, ax = plt.subplots(figsize=(7.2, 3.6))

    for difficulty in DIFFICULTIES:
        difficulty_rows = [row for row in rows if row.get("difficulty") == difficulty]
        groups = grouped(difficulty_rows, "rows")
        sizes = sorted(groups, key=int)
        labels = [f"{size}x{size}" for size in sizes]
        values = [mean_solve_time(groups[size]) for size in sizes]
        ax.plot(
            labels,
            values,
            marker="o",
            linewidth=2.0,
            color=DIFFICULTY_COLORS[difficulty],
            label=difficulty,
        )

    ax.set_title("Average Exact-Flow Solve Time by Size and Difficulty")
    ax.set_xlabel("Board size")
    ax.set_ylabel("Average solve time (s)")
    ax.tick_params(axis="x", rotation=30)
    ax.legend(frameon=True)
    save_figure(fig, IMAGE_DIR / "tracks_average_solution_time_by_size_and_difficulty.png")


if __name__ == "__main__":
    main()
