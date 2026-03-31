"""Panel D: Scatter plot — two-variable relationship."""


def make_figure(**kwargs):
    import matplotlib.pyplot as plt
    import numpy as np

    rng = np.random.default_rng(3)
    x = rng.standard_normal(120)
    y = 1.5 * x + rng.standard_normal(120) * 0.6

    fig, ax = plt.subplots(figsize=(3.5, 2.5))
    ax.scatter(x, y, s=12, alpha=0.6, color="#2ca02c", edgecolors="none")
    # Regression line
    m, b = np.polyfit(x, y, 1)
    xr = np.array([x.min(), x.max()])
    ax.plot(xr, m * xr + b, color="black", lw=1, ls="--")
    ax.set_xlabel("Feature X")
    ax.set_ylabel("Feature Y")
    ax.set_title("X vs Y (r²={:.2f})".format(np.corrcoef(x, y)[0, 1] ** 2))
    fig.tight_layout()
    return fig
