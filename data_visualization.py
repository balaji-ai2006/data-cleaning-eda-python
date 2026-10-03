"""
data_visualization.py
=====================
Generates high-quality EDA visualizations from cleaned_data.csv:
1. Histograms with KDE for numerical features
2. Box plots for outlier checks & feature distributions
3. Bar charts for categorical attributes
4. Correlation heatmap for numerical features

All plots are saved to the 'plots/' directory with high resolution (300 DPI).
"""

import os
import matplotlib.pyplot as plt
import seaborn as sns
import pandas as pd
import numpy as np

def setup_plot_environment():
    """Sets modern visual styling for seaborn and matplotlib."""
    sns.set_theme(style="whitegrid", palette="deep")
    plt.rcParams.update({
        "font.sans-serif": ["Segoe UI", "DejaVu Sans", "Arial"],
        "axes.edgecolor": "#cccccc",
        "axes.linewidth": 0.8,
        "grid.color": "#ebebeb",
        "grid.linestyle": "--",
        "grid.alpha": 0.7,
        "figure.titlesize": 16,
        "axes.titlesize": 13,
        "axes.labelsize": 11,
    })

def create_histograms(df, output_dir):
    """Plot histograms with KDE for numerical features."""
    num_cols = ["age", "salary", "years_of_experience", "performance_score"]
    palette = ["#2b5c8f", "#2a9d8f", "#e76f51", "#7b2cbf"]

    fig, axes = plt.subplots(2, 2, figsize=(13, 9))
    fig.suptitle("Distribution of Numerical Features (Cleaned Data)", fontsize=16, fontweight="bold", y=0.98)

    for i, col in enumerate(num_cols):
        ax = axes[i // 2, i % 2]
        color = palette[i % len(palette)]
        sns.histplot(
            df[col],
            kde=True,
            ax=ax,
            color=color,
            bins=8,
            edgecolor="white",
            linewidth=1.2,
            alpha=0.65
        )
        # Add mean and median vertical indicator lines
        mean_val = df[col].mean()
        median_val = df[col].median()
        ax.axvline(mean_val, color="#d90429", linestyle="--", linewidth=1.5, label=f"Mean: {mean_val:.1f}")
        ax.axvline(median_val, color="#1d3557", linestyle="-", linewidth=1.5, label=f"Median: {median_val:.1f}")
        
        ax.set_title(col.replace("_", " ").title(), fontweight="bold", pad=8)
        ax.set_xlabel(col.replace("_", " ").title())
        ax.set_ylabel("Frequency")
        ax.legend(frameon=True, facecolor="white", edgecolor="#cccccc", fontsize=9)

    plt.tight_layout()
    output_path = os.path.join(output_dir, "histograms_numerical.png")
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f" [OK] Generated: {output_path}")

def create_boxplots(df, output_dir):
    """Plot box plots for numerical features to inspect distributions and verify outliers."""
    num_cols = ["age", "salary", "years_of_experience", "performance_score"]
    
    # 1. Individual subplots for numerical features
    fig, axes = plt.subplots(2, 2, figsize=(13, 9))
    fig.suptitle("Outlier Verification & Quartile Analysis (Box Plots)", fontsize=16, fontweight="bold", y=0.98)

    box_colors = ["#457b9d", "#2a9d8f", "#f4a261", "#9d4edd"]

    for i, col in enumerate(num_cols):
        ax = axes[i // 2, i % 2]
        sns.boxplot(
            y=df[col],
            ax=ax,
            color=box_colors[i],
            width=0.35,
            fliersize=5,
            linewidth=1.5,
            boxprops=dict(alpha=0.8)
        )
        sns.stripplot(
            y=df[col],
            ax=ax,
            color="#222222",
            size=5,
            jitter=0.15,
            alpha=0.5
        )
        ax.set_title(col.replace("_", " ").title(), fontweight="bold", pad=8)
        ax.set_ylabel(col.replace("_", " ").title())

    plt.tight_layout()
    output_path = os.path.join(output_dir, "boxplots_outliers.png")
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f" [OK] Generated: {output_path}")

    # 2. Additional domain insight: Salary by Department boxplot
    fig, ax = plt.subplots(figsize=(10, 6))
    sns.boxplot(
        x="department",
        y="salary",
        hue="department",
        data=df,
        ax=ax,
        palette="Blues_d",
        legend=False,
        width=0.45,
        linewidth=1.3,
        boxprops=dict(alpha=0.85)
    )
    sns.stripplot(x="department", y="salary", data=df, ax=ax, color="#222222", size=5, jitter=0.15, alpha=0.6)
    ax.set_title("Salary Distribution across Departments", fontweight="bold", fontsize=14, pad=10)
    ax.set_xlabel("Department", fontweight="bold")
    ax.set_ylabel("Salary ($)", fontweight="bold")
    ax.yaxis.set_major_formatter("${x:,.0f}")
    plt.tight_layout()
    dept_box_path = os.path.join(output_dir, "boxplots_salary_by_department.png")
    plt.savefig(dept_box_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f" [OK] Generated: {dept_box_path}")

def create_barcharts(df, output_dir):
    """Plot bar charts for categorical attributes with counts and percentages."""
    cat_cols = ["department", "gender", "remote_worker"]
    
    fig, axes = plt.subplots(1, 3, figsize=(16, 5))
    fig.suptitle("Categorical Attributes Breakdown", fontsize=16, fontweight="bold", y=1.02)

    for i, col in enumerate(cat_cols):
        ax = axes[i]
        counts = df[col].value_counts().reset_index()
        counts.columns = [col, "count"]
        
        # Format labels nicely
        if col == "remote_worker":
            counts[col] = counts[col].map({True: "Remote (Yes)", False: "On-site (No)"})
        
        palette = sns.color_palette("mako", len(counts))
        bars = sns.barplot(
            x=col,
            y="count",
            hue=col,
            data=counts,
            ax=ax,
            palette=palette,
            legend=False,
            edgecolor="white",
            linewidth=1.2,
            alpha=0.85
        )
        
        # Add value labels on top of each bar
        total = len(df)
        for bar in bars.patches:
            height = bar.get_height()
            percentage = (height / total) * 100
            ax.annotate(
                f"{int(height)}\n({percentage:.0f}%)",
                xy=(bar.get_x() + bar.get_width() / 2, height),
                xytext=(0, 4),
                textcoords="offset points",
                ha="center",
                va="bottom",
                fontsize=9,
                fontweight="bold"
            )

        ax.set_title(col.replace("_", " ").title(), fontweight="bold", pad=10)
        ax.set_xlabel("")
        ax.set_ylabel("Count")
        ax.set_ylim(0, counts["count"].max() * 1.25)
        if col == "department":
            ax.tick_params(axis="x", rotation=25)

    plt.tight_layout()
    output_path = os.path.join(output_dir, "barcharts_categorical.png")
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f" [OK] Generated: {output_path}")

def create_correlation_heatmap(df, output_dir):
    """Plot correlation heatmap for all numerical features."""
    num_cols = ["age", "salary", "years_of_experience", "performance_score"]
    corr_matrix = df[num_cols].corr()

    # Readable labels
    display_labels = [c.replace("_", " ").title() for c in num_cols]

    fig, ax = plt.subplots(figsize=(8, 6.5))
    
    # Mask upper triangle for cleaner triangular heatmap
    mask = np.triu(np.ones_like(corr_matrix, dtype=bool), k=1)

    heatmap = sns.heatmap(
        corr_matrix,
        mask=mask,
        annot=True,
        fmt=".2f",
        cmap="vlag",
        vmin=-1,
        vmax=1,
        center=0,
        square=True,
        linewidths=1.5,
        linecolor="white",
        cbar_kws={"shrink": 0.8, "label": "Pearson Correlation Coefficient"},
        ax=ax,
        annot_kws={"size": 12, "weight": "bold"}
    )

    ax.set_xticklabels(display_labels, rotation=20, ha="right", fontweight="bold")
    ax.set_yticklabels(display_labels, rotation=0, fontweight="bold")
    ax.set_title("Correlation Heatmap (Numerical Features)", fontsize=15, fontweight="bold", pad=15)

    plt.tight_layout()
    output_path = os.path.join(output_dir, "correlation_heatmap.png")
    plt.savefig(output_path, dpi=300, bbox_inches="tight")
    plt.close()
    print(f" [OK] Generated: {output_path}")

def main():
    input_file = "cleaned_data.csv"
    output_dir = "plots"

    if not os.path.exists(input_file):
        raise FileNotFoundError(f"Cleaned dataset '{input_file}' not found. Please run data_cleaning.py first.")

    os.makedirs(output_dir, exist_ok=True)
    print("=" * 60)
    print(f"Loading '{input_file}' and initializing plot generation...")
    print(f"Target Directory: '{output_dir}/'")
    print("=" * 60)

    df = pd.read_csv(input_file)
    setup_plot_environment()

    # Generate each required chart
    create_histograms(df, output_dir)
    create_boxplots(df, output_dir)
    create_barcharts(df, output_dir)
    create_correlation_heatmap(df, output_dir)

    print("=" * 60)
    print(f"[SUCCESS] All plots generated and saved in '{output_dir}/' folder.")
    print("=" * 60)

if __name__ == "__main__":
    main()
