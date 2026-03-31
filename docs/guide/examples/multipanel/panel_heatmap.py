"""Panel C: Heatmap — correlation matrix."""


def make_figure(**kwargs):
    import matplotlib.pyplot as plt
    import numpy as np

    rng = np.random.default_rng(2)
    n = 5
    # Build a random positive-definite correlation matrix
    raw = rng.standard_normal((n, n))
    cov = raw @ raw.T
    d = np.sqrt(np.diag(cov))
    corr = cov / np.outer(d, d)

    labels = [f"X{i+1}" for i in range(n)]

    fig, ax = plt.subplots(figsize=(3.5, 2.5))
    im = ax.imshow(corr, vmin=-1, vmax=1, cmap="RdBu_r")
    ax.set_xticks(range(n))
    ax.set_yticks(range(n))
    ax.set_xticklabels(labels)
    ax.set_yticklabels(labels)
    fig.colorbar(im, ax=ax, fraction=0.046, pad=0.04)
    ax.set_title("Correlation matrix")
    fig.tight_layout()
    return fig
