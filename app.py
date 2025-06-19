# app.py

from cProfile import label
from gettext import install
from itertools import count
from matplotlib import colors
from matplotlib.pylab import matrix
import pip
from shiny import App, ui, reactive, render
import pandas as pd
import matplotlib.pyplot as plt


import pandas as pd
import mplcursors

# Opt in to the new replace behavior and silence the warning:
pd.set_option('future.no_silent_downcasting', True)

# ───── Color palette for the pie chart ─────
PALETTE = {
  "Pathogenic":             "#D62728",
  "Likely Pathogenic":      "#FF7F0E",
  "Likely Benign":          "#2CA02C",
  "Uncertain Significance": "#1F77B4",
}

import seaborn as sns
sns.set_theme(style="whitegrid")


# ───── 1) Load synthetic dataset ─────
df = pd.read_csv("TSO500_Synthetic_Final.csv")

# ───── 2) Prepare dropdown choices ─────
genes       = ["All"] + sorted(df["gene"].dropna().unique())
assessments = ["All"] + sorted(df["assessment"].dropna().unique())

# ───── 3) UI definition ─────
app_ui = ui.page_fluid(
    ui.h1("TSO500 Synthetic Variant Explorer"),

    # filters
    ui.input_select("selected_gene",       "Select Gene:",       choices=genes,       selected="All"),
    ui.input_select("selected_assessment", "Select Assessment:", choices=assessments, selected="All"),
    ui.tags.style(
    """
    .card {
      border: 1px solid #ddd;
      border-radius: 4px;
      padding: 12px;
      margin: 8px;
      box-shadow: 0 2px 4px rgba(0,0,0,0.05);
      background: #fff;
      /* make cards wider: */
      min-width: 180px;
    }
    .card-title {
      font-size: 1.1rem;
      font-weight: 600;
      margin-bottom: 4px;
      /* allow wrapping */
      white-space: normal;
    }
    .card-value {
      font-size: 1.4rem;
      text-align: center;
      margin-top: 4px;
    }
    """
),


       # ─── summary cards ───
    ui.layout_columns(
        # first card
        ui.column(4,
          ui.tags.div(
            # the “card” container
            ui.tags.div("Total Variants", class_="card-title"),
            ui.output_text("total_count"),
            class_="card"
          )
        ),
        # second card
        ui.column(4,
          ui.tags.div(
            ui.tags.div("Unique Genes", class_="card-title"),
            ui.output_text("unique_genes"),
            class_="card"
          )
        ),
        # third card
        ui.column(4,
          ui.tags.div(
            ui.tags.div("Actionable Variants", class_="card-title"),
            ui.output_text("actionable_count"),
            class_="card"
          )
        )
    ),   


    ui.hr(),

    # plots
    ui.output_plot("pie_plot"),
    ui.output_plot("bar_plot"),
    ui.output_plot("hist_plot"),
    ui.output_plot("oncoprint"),
  
)

# ───── 4) Server logic ─────
def server(input, output, session):

    @reactive.Calc
    def filtered_data():
        d = df.copy()
        if input.selected_gene() != "All":
            d = d[d["gene"] == input.selected_gene()]
        if input.selected_assessment() != "All":
            d = d[d["assessment"] == input.selected_assessment()]
        return d

    @output
    @render.text
    def total_count():
        return str(len(filtered_data()))

    @output
    @render.text
    def unique_genes():
        return str(filtered_data()["gene"].nunique())

    @output
    @render.text
    def actionable_count():
        d = filtered_data()
        return str(d[d["assessment"].isin(["Pathogenic","Likely Pathogenic"])].shape[0])
    
    @output
    @render.plot
    def pie_plot():
        # 1) pull and call your method
        counts = filtered_data()["assessment"].value_counts()
        values = counts.values
        labels = counts.index.tolist()

        # 2) map to your palette
        colors = [PALETTE.get(lbl, "#888888") for lbl in labels]

        # 3) draw a donut so labels don’t get cut off
        fig, ax = plt.subplots(figsize=(6,6), dpi=100)
        wedges, texts, autotexts = ax.pie(
            values,
            labels=None,               # we’ll show a legend instead
            colors=colors,
            startangle=140,
            autopct="%.1f%%",
            pctdistance=0.80,          # push % labels in toward slice
            wedgeprops=dict(width=0.4),# thickness of donut
            textprops=dict(color="white", weight="bold", fontsize=12),
        )

        ax.set_title("Assessment Distribution", fontsize=18, weight="bold", pad=20)
        ax.axis("equal")  # keeps it a perfect circle

        # 4) put a legend on the right
        ax.legend(
            wedges,
            labels,
            title="Assessment",
            loc="center left",
            bbox_to_anchor=(1.0, 0.5),
            frameon=False,
            fontsize=12,
        )
        
        # 5) give room for that legend
        fig.subplots_adjust(left=0.0, right=0.75)

        return fig

    @output
    @render.plot
    def bar_plot():
        d = filtered_data()
        counts = d["gene"].value_counts()
        fig, ax = plt.subplots(figsize=(6,4), dpi=100)

        # bar chart
        bars = counts.plot.bar(ax=ax)

        # annotate each bar with its height
        for bar in bars.patches:
            h = bar.get_height()
            ax.text(
                bar.get_x() + bar.get_width()/2,
                h + 0.3,
                f"{int(h)}",
                ha="center",
                va="bottom",
                fontsize=10,
            )

        ax.set_xlabel("Gene", fontsize=12, weight="bold")
        ax.set_ylabel("Count", fontsize=12, weight="bold")
        ax.set_title("Mutation Count by Gene", fontsize=16, weight="bold", pad=12)

        # remove top/right spines
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        plt.tight_layout(pad=2)
        return fig

    @output
    @render.plot
    def hist_plot():
        arr = filtered_data()["allelefraction"].dropna()
        fig, ax = plt.subplots(figsize=(6,4), dpi=100)

        # histogram
        ax.hist(arr, bins=20, edgecolor="black")

        # mean line
        mean_val = arr.mean()
        ax.axvline(mean_val, color="firebrick", linestyle="--", linewidth=2)
        ax.text(
            mean_val + 0.01, 
            ax.get_ylim()[1]*0.9,
            f"Mean: {mean_val:.2f}",
            color="firebrick",
            fontsize=10,
            weight="bold"
        )

        ax.set_xlabel("Allele Fraction", fontsize=12, weight="bold")
        ax.set_ylabel("Frequency", fontsize=12, weight="bold")
        ax.set_title("Allele Fraction Distribution", fontsize=16, weight="bold", pad=12)

        # remove top/right spines
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)

        plt.tight_layout(pad=2)
        return fig
    
    @output
    @render.plot
    def oncoprint():
        import numpy as np
        import pandas as pd
        import matplotlib.pyplot as plt
        from matplotlib.colors import ListedColormap
        from matplotlib.patches import Patch

        # 1) Pull the filtered data
        d = filtered_data()

        # 2) Pick top genes & samples
        top_genes   = d["gene"].value_counts().nlargest(8).index.tolist()
        top_samples = d["MRN"].value_counts().nlargest(10).index.tolist()
        sub = d.loc[
            d["gene"].isin(top_genes)
            & d["MRN"].isin(top_samples)
        ]

        # 3) Build empty “no variant” grid
        matrix = pd.DataFrame("", index=top_genes, columns=top_samples)
        for _, row in sub.iterrows():
            matrix.at[row["gene"], row["MRN"]] = row["assessment"]

        # 4) Map labels → ints
        levels  = list(PALETTE.keys())                            # ["Pathogenic", ...]
        mapping = {lvl: i for i, lvl in enumerate(levels)}        # {"Pathogenic":0,...}
        grid = (
            matrix
            .replace(mapping)             # map assessments to ints
            .replace("", -1)              # no-variant → -1
            .astype(int, copy=False)      # ensure integer dtype
        )

        # 5) Compute “pathogenic load” & sort
        path_code   = mapping["Pathogenic"]
        likely_code = mapping["Likely Pathogenic"]
        load = (
            (grid == path_code) 
            | (grid == likely_code)
        ).sum(axis=1) / len(top_samples)
        order = load.sort_values(ascending=False).index.tolist()
        grid  = grid.loc[order]

        # 6) Build colormap (grey + your PALETTE)
        colors = ["#EEEEEE"] + [PALETTE[l] for l in levels]
        cmap   = ListedColormap(colors)

        # 7) Draw heatmap
        fig, ax = plt.subplots(figsize=(10, 5), dpi=100)
        ax.imshow(
            grid.values,
            cmap=cmap,
            aspect="auto",
            vmin=-1,
            vmax=len(levels) - 1,
        )

        # 8) Grid lines & alternating row shading
        ax.set_xticks(np.arange(grid.shape[1] + 1) - 0.5, minor=True)
        ax.set_yticks(np.arange(grid.shape[0] + 1) - 0.5, minor=True)
        ax.grid(which="minor", color="white", linewidth=1)
        ax.tick_params(which="minor", length=0)
        for i in range(len(order)):
            if i % 2 == 1:
                ax.axhspan(i - 0.5, i + 0.5, color="#f7f7f7", zorder=0)

        # 9) Axis labels & ticks
        ax.set_xticks(np.arange(len(top_samples)))
        ax.set_xticklabels(top_samples, rotation=90, ha="center", fontsize=8)
        ax.set_xlabel("Sample (MRN)", fontsize=12, weight="bold")

        ax.set_yticks(np.arange(len(order)))
        ax.set_yticklabels(order, fontsize=10)
        ax.set_ylabel("Gene", fontsize=12, weight="bold")

        # 10) Horizontal line under header row
        ax.axhline(-0.5, color="black", lw=1)

        # 11) Legend out to the right
        patches = [Patch(facecolor=colors[0], label="No Variant")]
        for i, lvl in enumerate(levels):
            patches.append(Patch(facecolor=colors[i + 1], label=lvl))

        ax.legend(
            handles=patches,
            title="Assessment",
            bbox_to_anchor=(1.3, 1.2),    # push further right
            loc="upper left",
            frameon=True,
            edgecolor="#ccc",
            framealpha=1,
            title_fontsize=12,
            fontsize=10,
            labelspacing=1.2,
        )

        # 12) Draw pathogenic‐load % labels on right
        for i, gene in enumerate(order):
            pct = load.loc[gene] * 100
            ax.text(
                grid.shape[1] + 0.3,      # just right of last column
                i,
                f"{pct:.0f}%",
                va="center",
                ha="left",
                fontsize=10,
            )

        # 13) Final title and tight layout
        ax.set_title(
            "Oncoprint: Clinical Assessment by Gene & Sample",
            fontsize=16, weight="bold", pad=12
        )

        plt.tight_layout(pad=2)
        return fig

# ───── 5) Launch the app ─────
app = App(app_ui, server)
