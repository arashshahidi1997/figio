"""Panel A: Line plot — time-series signal."""


def make_figure(**kwargs):
    import matplotlib.pyplot as plt
    import numpy as np

    rng = np.random.default_rng(0)
    t = np.linspace(0, 4 * np.pi, 300)
    signal = np.sin(t) + rng.normal(0, 0.15, len(t))

    fig, ax = plt.subplots(figsize=(3.5, 2.5))
    ax.plot(t, signal, lw=0.8, color="#1f77b4")
    ax.set_xlabel("Time (s)")
    ax.set_ylabel("Amplitude")
    ax.set_title("Signal over time")
    fig.tight_layout()
    return fig
