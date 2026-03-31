"""Minimal panel script with make_figure() for testing."""

from __future__ import annotations


def make_figure(**kwargs):
    """Return a simple matplotlib figure with one axes."""
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    import numpy as np

    fig, ax = plt.subplots(figsize=(3, 2))
    x = np.linspace(0, 2 * np.pi, 50)
    ax.plot(x, np.sin(x), label="sin(x)")
    ax.set_xlabel("x")
    ax.set_ylabel("y")
    ax.set_title("Test Panel")
    return fig
