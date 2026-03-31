"""Panel B: Bar chart — condition means."""


def make_figure(**kwargs):
    import matplotlib.pyplot as plt
    import numpy as np

    rng = np.random.default_rng(1)
    conditions = ["Control", "Drug A", "Drug B", "Drug C"]
    means = rng.uniform(0.4, 0.9, len(conditions))
    errors = rng.uniform(0.02, 0.08, len(conditions))

    fig, ax = plt.subplots(figsize=(3.5, 2.5))
    x = np.arange(len(conditions))
    ax.bar(x, means, yerr=errors, capsize=3, color="#ff7f0e", width=0.5)
    ax.set_xticks(x)
    ax.set_xticklabels(conditions, rotation=20, ha="right")
    ax.set_ylabel("Response (a.u.)")
    ax.set_title("Condition comparison")
    fig.tight_layout()
    return fig
