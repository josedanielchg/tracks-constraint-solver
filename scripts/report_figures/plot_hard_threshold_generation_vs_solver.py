"""Plot hard-instance generation and exact-flow solve times by board size."""

from __future__ import annotations

from common import IMAGE_DIR, configure_matplotlib, grouped, load_rows, mean_numeric, mean_solve_time, save_figure


def main() -> None:
    configure_matplotlib()
    import matplotlib.pyplot as plt

    rows = [
        row
        for row in load_rows()
        if row.get("difficulty") == "Hard" and row.get("generation_status") != "error"
    ]
    groups = grouped(rows, "rows")
    sizes = sorted(groups, key=int)
    labels = [f"{size}x{size}" for size in sizes]
    generation_times = [mean_numeric(groups[size], "generation_time") for size in sizes]
    solve_times = [mean_solve_time(groups[size]) for size in sizes]

    fig, ax = plt.subplots(figsize=(7.0, 3.4))
    ax.plot(labels, generation_times, marker="o", linewidth=2.0, label="Generation time")
    ax.plot(labels, solve_times, marker="s", linewidth=2.0, label="Exact-flow solve time")
    ax.set_title("Hard Threshold: Generation vs Exact-Flow Solving")
    ax.set_xlabel("Board size")
    ax.set_ylabel("Average time (s)")
    ax.tick_params(axis="x", rotation=30)
    ax.legend(frameon=True)
    save_figure(fig, IMAGE_DIR / "tracks_hard_threshold_generation_vs_solver.png")


if __name__ == "__main__":
    main()
