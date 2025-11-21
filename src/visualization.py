"""
Visualization utilities for AntibioticResistanceGeneDetector.

This module contains helper functions to create common plots used by the
project: gene detection heatmaps, per-sample antibiotic-class bar charts,
and simple gene→class network diagrams. Plotting uses matplotlib, seaborn
and networkx. Functions write image files into the output directory and
return nothing (side-effecting helpers).
"""
import os
import pandas as pd
import matplotlib.pyplot as plt
import seaborn as sns
import networkx as nx

from src.rich_utils import get_console

_HAS_RICH_VIZ = False

def save_plot(fig, filename, output_dir="output"):
    """
    Save a matplotlib figure to disk under ``output/plots``.

    Parameters
    ----------
    fig : matplotlib.figure.Figure
        The matplotlib figure to save.
    filename : str
        Name of the output file (can be absolute or relative). If relative,
        it will be placed under ``<output_dir>/plots``.
    output_dir : str, optional
        Base output directory (default: ``output``).

    Returns
    -------
    None
    """
    # If filename is an absolute path or contains a directory, respect it; otherwise save under output/plots
    if os.path.isabs(filename) or os.path.dirname(filename):
        out_path = filename
        out_dir = os.path.dirname(out_path)
        if out_dir:
            os.makedirs(out_dir, exist_ok=True)
    else:
        out_dir = os.path.join(output_dir, "plots")
        os.makedirs(out_dir, exist_ok=True)
        out_path = os.path.join(out_dir, filename)
    fig.savefig(out_path, bbox_inches='tight')
    plt.close(fig)

def plot_gene_heatmap(results, filename="gene_heatmap.png", output_dir="output", console=None, rich_enabled: bool = True):
    """
    Create and save a presence/absence heatmap of samples (rows) vs genes
    (columns).

    Parameters
    ----------
    results : list of dict
        Detection results where each dict contains at minimum ``sample_id``
        and ``gene`` keys (see project output format).
    filename : str, optional
        Output image filename (default: ``gene_heatmap.png``).
    output_dir : str, optional
        Base output directory (default: ``output``).
    console : object, optional
        Console-like object used for user feedback (Rich or dummy console).
    rich_enabled : bool, optional
        Whether to print progress/messages via Rich when available.

    Returns
    -------
    None
    """
    if not results or len(results) == 0:
        if rich_enabled and _HAS_RICH_VIZ:
            console = console or get_console(rich_enabled=rich_enabled, quiet=False)
            console.print("No data for heatmap.")
        else:
            print("No data for heatmap.")
        return
    df = pd.DataFrame(results)
    # Create presence/absence matrix: 1 if gene detected in sample, else 0
    presence_df = df.copy()
    presence_df["present"] = 1
    heatmap_df = presence_df.pivot_table(index="sample_id", columns="gene", values="present", aggfunc="sum", fill_value=0)
    heatmap_df = (heatmap_df > 0).astype(int)
    fig, ax = plt.subplots(figsize=(10, max(4, len(heatmap_df)//2)))
    sns.heatmap(heatmap_df, cmap="YlGnBu", linewidths=0.5, linecolor='gray', ax=ax, cbar_kws={'label': 'Detected'})
    ax.set_title("Gene Detection Heatmap")
    ax.set_xlabel("Gene")
    ax.set_ylabel("Sample")
    save_plot(fig, filename, output_dir=output_dir)
    if rich_enabled and _HAS_RICH_VIZ:
        console = console or get_console(rich_enabled=rich_enabled, quiet=False)
        console.print(f"Saved heatmap to {os.path.join(output_dir, 'plots', filename)}")

def plot_class_bar(results, filename="class_bar.png", output_dir="output", console=None, rich_enabled: bool = True):
    """Bar chart: antibiotic classes detected per sample."""
    if not results or len(results) == 0:
        if rich_enabled and _HAS_RICH_VIZ:
            console = console or get_console(rich_enabled=rich_enabled, quiet=False)
            console.print("No data for class bar chart.")
        else:
            print("No data for class bar chart.")
        return
    df = pd.DataFrame(results)
    class_counts = df.groupby(["sample_id", "antibiotic_class"]).size().reset_index(name="count")
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.barplot(data=class_counts, x="sample_id", y="count", hue="antibiotic_class", ax=ax)
    ax.set_title("Antibiotic Classes Detected per Sample")
    ax.set_xlabel("Sample")
    ax.set_ylabel("Gene Count")
    ax.legend(title="Antibiotic Class", bbox_to_anchor=(1.05, 1), loc='upper left')
    save_plot(fig, filename, output_dir=output_dir)
    if rich_enabled and _HAS_RICH_VIZ:
        console = console or get_console(rich_enabled=rich_enabled, quiet=False)
        console.print(f"Saved class bar chart to {os.path.join(output_dir, 'plots', filename)}")

def plot_gene_class_network(results, filename="gene_class_network.png", output_dir="output", console=None, rich_enabled: bool = True):
    """Network plot: gene → antibiotic class relationships."""
    if not results or len(results) == 0:
        if rich_enabled and _HAS_RICH_VIZ:
            console = console or get_console(rich_enabled=rich_enabled, quiet=False)
            console.print("No data for network plot.")
        else:
            print("No data for network plot.")
        return
    df = pd.DataFrame(results)
    edges = df[["gene", "antibiotic_class"]].drop_duplicates().values.tolist()
    G = nx.Graph()
    G.add_edges_from(edges)
    pos = nx.spring_layout(G, seed=42)
    fig, ax = plt.subplots(figsize=(10, 8))
    nx.draw(G, pos, with_labels=True, node_color='skyblue', edge_color='gray', node_size=1200, font_size=10, ax=ax)
    ax.set_title("Gene to Antibiotic Class Network")
    save_plot(fig, filename, output_dir=output_dir)
    if rich_enabled and _HAS_RICH_VIZ:
        console = console or get_console(rich_enabled=rich_enabled, quiet=False)
        console.print(f"Saved network plot to {os.path.join(output_dir, 'plots', filename)}")
