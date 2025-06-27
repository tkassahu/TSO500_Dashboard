# app.py

#Imports and Configuration 
from cProfile import label
from gettext import install
from itertools import count
from matplotlib import colors
from matplotlib.pylab import matrix
from matplotlib.colors import ListedColormap
from matplotlib.patches import Patch
import pip
from shiny import App, ui, reactive, render
import pandas as pd
import matplotlib.pyplot as plt
import pandas as pd
from neo4j import GraphDatabase
import numpy as np
import mplcursors

#Data Loading
df = pd.read_csv("TSO500_Synthetic_Final.csv") 
demo_df = pd.read_csv("clean_demographics.csv")
variants_df = pd.read_csv("variants_with_50_demo_mrn.csv")
df = variants_df.merge(demo_df, on="mrn", how="left")

#Memgraph connection
mg_driver = GraphDatabase.driver("bolt://127.0.0.1:7687", auth=None)



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

#  Prepare dropdown choices ─────
genes       = ["All"] + sorted(df["gene"].dropna().unique())
assessments = ["All"] + sorted(df["assessment"].dropna().unique())

# 3) UI definition
app_ui = ui.page_fluid(
    ui.h2("TSO-500 Variant Explorer"),

    # ─── Custom CSS to tighten up cards ───
    ui.tags.style(
        """
        .card {
          border: 1px solid #ddd;
          border-radius: 4px;
          padding: 8px;
          margin-bottom: 8px;
          background: #fff;
        }
        .card-title { font-size: 1.1rem; font-weight: 600; margin-bottom: 4px; }
        .card-value { font-size: 1.4rem; }
        """
    ),

    # ─── Sidebar + Main Content ───
    ui.layout_sidebar(
        # ─── 1) Filters go here ───
        ui.sidebar(
            ui.input_select(
                "filter_gene", "Gene:",
                choices=["All"] + sorted(df["gene"].dropna().unique()),
                selected="All",
            ),
            ui.input_select(
                "filter_assessment", "Assessment:",
                choices=["All"] + sorted(df["assessment"].dropna().unique()),
                selected="All",
            ),
            ui.input_select(
                "filter_sex", "Sex:",
                choices=["All", "female", "male"],
                selected="All",
            ),
            ui.input_slider(
                "filter_age", "Age range:",
                min=0, max=100, value=[0, 100]
            ),
        ),

        # ─── 2) Summary cards ───
        ui.layout_column_wrap(
            ui.tags.div(
                ui.tags.div("Total Variants", class_="card-title"),
                ui.tags.div(ui.output_text("total_count"), class_="card-value"),
                class_="card",
            ),
            ui.tags.div(
                ui.tags.div("Unique Genes", class_="card-title"),
                ui.tags.div(ui.output_text("unique_genes"), class_="card-value"),
                class_="card",
            ),
            ui.tags.div(
                ui.tags.div("Actionable Variants", class_="card-title"),
                ui.tags.div(ui.output_text("actionable_count"), class_="card-value"),
                class_="card",
            ),
            width=4,   # 3 cards × width 4 = full 12-col row
        ),

        # ─── 3) First plot row: Pie & Bar ───
        ui.layout_column_wrap(
            ui.tags.div(ui.output_plot("pie_plot"), class_="card"),
            ui.tags.div(ui.output_plot("bar_plot"), class_="card"),
            width=6,  # each plot takes half the width
        ),

        # ─── 4) Second plot row: Hist & Oncoprint ───
        ui.layout_column_wrap(
            ui.tags.div(ui.output_plot("hist_plot"), class_="card"),
            ui.tags.div(ui.output_plot("oncoprint"), class_="card"),
            width=6,
        ),
    )
)

# ─── 4) Server logic ───
def server(input, output, session):
    # 1) Reactive expression that returns a pandas DataFrame
    @reactive.Calc
    def filtered_data():
        # start with the merged DataFrame
        d = df.copy()

        # apply the Gene & Assessment filters in pandas
        if input.filter_gene() != "All":
            d = d[d["gene"] == input.filter_gene()]
        if input.filter_assessment() != "All":
            d = d[d["assessment"] == input.filter_assessment()]

        # now use Memgraph to filter on sex & age
        clauses = []
        params = {}
        if input.filter_sex() != "All":
            clauses.append("p.sex = $sex")
            params["sex"] = input.filter_sex()
        min_age, max_age = input.filter_age()
        clauses.append("p.age >= $min_age")
        clauses.append("p.age <= $max_age")
        params["min_age"] = min_age
        params["max_age"] = max_age

        cypher = f"""
            MATCH (p:Patient)-[:HAS_VARIANT]->(v)
            WHERE {' AND '.join(clauses)}
            RETURN DISTINCT p.mrn AS mrn
        """
        with mg_driver.session() as sess:
            result = sess.run(cypher, params)
            valid_mrns = {record["mrn"] for record in result}

        # subset your pandas DataFrame by those MRNs
        return d[d["mrn"].isin(valid_mrns)]

    # ─── Summary card texts ───
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
        return str(d[d["assessment"].isin(["Pathogenic", "Likely Pathogenic"])].shape[0])

    # ─── Four plot outputs ───
    @output
    @render.plot
    def pie_plot():
        counts = filtered_data()["assessment"].value_counts()
        values, labels = counts.values, counts.index.tolist()
        colors = [PALETTE.get(l, "#888888") for l in labels]

        fig, ax = plt.subplots(figsize=(6, 6), dpi=100)
        wedges, _, _ = ax.pie(
            values,
            labels=None,
            colors=colors,
            startangle=140,
            autopct="%.1f%%",
            pctdistance=0.8,
            wedgeprops=dict(width=0.4),
            textprops=dict(color="white", weight="bold", fontsize=12),
        )
        ax.set_title("Assessment Distribution", fontsize=18, weight="bold", pad=20)
        ax.axis("equal")
        ax.legend(wedges, labels, title="Assessment",
                  loc="center left", bbox_to_anchor=(1, 0.5), frameon=False)
        fig.subplots_adjust(left=0.0, right=0.75)
        return fig

    @output
    @render.plot
    def bar_plot():
        d = filtered_data()
        counts = d["gene"].value_counts()
        fig, ax = plt.subplots(figsize=(6, 4), dpi=100)
        bars = counts.plot.bar(ax=ax)
        for bar in bars.patches:
            ax.text(bar.get_x() + bar.get_width() / 2,
                    bar.get_height() + 0.3,
                    f"{int(bar.get_height())}",
                    ha="center", va="bottom", fontsize=10)
        ax.set_xlabel("Gene", fontsize=12, weight="bold")
        ax.set_ylabel("Count", fontsize=12, weight="bold")
        ax.set_title("Mutation Count by Gene", fontsize=16, weight="bold", pad=12)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        plt.tight_layout(pad=2)
        return fig

    @output
    @render.plot
    def hist_plot():
        arr = filtered_data()["allelefraction"].dropna()
        fig, ax = plt.subplots(figsize=(6, 4), dpi=100)
        ax.hist(arr, bins=20, edgecolor="black")
        mean_val = arr.mean()
        ax.axvline(mean_val, linestyle="--", linewidth=2, label=f"Mean: {mean_val:.2f}")
        ax.text(mean_val + 0.01, ax.get_ylim()[1] * 0.9,
                f"Mean: {mean_val:.2f}", color="firebrick", weight="bold")
        ax.set_xlabel("Allele Fraction", fontsize=12, weight="bold")
        ax.set_ylabel("Frequency", fontsize=12, weight="bold")
        ax.set_title("Allele Fraction Distribution", fontsize=16, weight="bold", pad=12)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        plt.tight_layout(pad=2)
        return fig

    @output
    @render.plot
    def oncoprint():
        d = filtered_data()
        top_genes = d["gene"].value_counts().nlargest(8).index.tolist()
        top_samples = d["mrn"].value_counts().nlargest(10).index.tolist()
        sub = d[d["gene"].isin(top_genes) & d["mrn"].isin(top_samples)]

        # build matrix
        matrix = pd.DataFrame("", index=top_genes, columns=top_samples)
        for _, row in sub.iterrows():
            matrix.at[row["gene"], row["mrn"]] = row["assessment"]

        levels = list(PALETTE.keys())
        mapping = {lbl: i for i, lbl in enumerate(levels)}
        grid = (matrix.replace(mapping)
                      .replace("", -1)
                      .astype(int))

        # compute load & sort
        path_code, likely_code = mapping["Pathogenic"], mapping["Likely Pathogenic"]
        load = ((grid == path_code) | (grid == likely_code)).sum(axis=1) / len(top_samples)
        grid = grid.loc[load.sort_values(ascending=False).index]

        colors = ["#EEEEEE"] + [PALETTE[l] for l in levels]
        cmap = ListedColormap(colors)

        fig, ax = plt.subplots(figsize=(10, 5), dpi=100)
        ax.imshow(grid.values, cmap=cmap, aspect="auto", vmin=-1, vmax=len(levels) - 1)

        # gridlines
        ax.set_xticks(np.arange(grid.shape[1] + 1) - 0.5, minor=True)
        ax.set_yticks(np.arange(grid.shape[0] + 1) - 0.5, minor=True)
        ax.grid(which="minor", color="white", linewidth=1)
        ax.tick_params(which="minor", length=0)

        # alternating shading
        for i in range(len(grid)):
            if i % 2:
                ax.axhspan(i - 0.5, i + 0.5, color="#f7f7f7", zorder=0)

        # labels
        ax.set_xticks(np.arange(len(top_samples)))
        ax.set_xticklabels(top_samples, rotation=90, ha="center", fontsize=8)
        ax.set_xlabel("Sample (MRN)", fontsize=12, weight="bold")

        ax.set_yticks(np.arange(len(grid)))
        ax.set_yticklabels(grid.index, fontsize=10)
        ax.set_ylabel("Gene", fontsize=12, weight="bold")

        # legend
        patches = [Patch(facecolor=colors[0], label="No Variant")] + [
            Patch(facecolor=colors[i + 1], label=lvl) for i, lvl in enumerate(levels)
        ]
        ax.legend(handles=patches, title="Assessment",
                  bbox_to_anchor=(1.3, 1.2), loc="upper left",
                  frameon=True, edgecolor="#ccc", fontsize=10)

        # load % labels
        for i, g in enumerate(grid.index):
            pct = load.loc[g] * 100
            ax.text(len(top_samples) + 0.3, i, f"{pct:.0f}%", va="center", ha="left", fontsize=10)

        ax.set_title("Oncoprint: Clinical Assessment by Gene & Sample", fontsize=16, weight="bold", pad=12)
        plt.tight_layout(pad=2)
        return fig



# ───── 5) Launch the app ─────
app = App(app_ui, server)

if __name__ == "__main__":
    print("🔹 Starting Shiny on http://127.0.0.1:8000")
    # debug=True removed
    app.run(host="127.0.0.1", port=8000)