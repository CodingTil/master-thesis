import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
from scipy.interpolate import make_smoothing_spline
import scipy.stats as st

from typing import Dict


order = [
    "compbnd",
    "compbnd+dvs",
    "compbnd-mdm",
    "compbnd-mdm+dvs",
    "compbnd-mrm",
    "compbnd-mrm+dvs"
]


def plot_num_bounds(name: str, dfs: Dict[str, pd.DataFrame], slides: bool):
    df: pd.DataFrame = pd.DataFrame()

    for test_name, test_df in dfs.items():
        df = pd.concat([df, test_df[["Test Name", "num_bounds"]]])

    # Order by Test Name
    df["Test Name"] = pd.Categorical(df["Test Name"], categories=[x for x in order if x in df["Test Name"].unique()], ordered=True).map(lambda x: f"\\texttt{{{x}}}")

    # For each TestName (group_outter): For each num_bounds (group_inner): Create a new column "perc_num_bounds" by count the number of occurrences in group inner / count the number of occurrences in group outer
    counts_df = df.groupby(['Test Name', 'num_bounds']).size().reset_index(name='count')
    total_counts_df = df.groupby('Test Name').size().reset_index(name='total_count')
    proportion_df = pd.merge(counts_df, total_counts_df, on='Test Name')
    proportion_df['perc_num_bounds'] = 100 * proportion_df['count'] / proportion_df['total_count']

    g = sns.catplot(
        data=proportion_df, x="num_bounds", y="perc_num_bounds", hue="Test Name",
        kind="bar"
    )
    sns.move_legend(g, loc="upper right", bbox_to_anchor=(1, 0.9))
    #if not slides:
        #g.set(title=f"Distribution of Number of Bounds")
    g.set_axis_labels("Number of Bounds", "Distribution (\\%)")
    g.legend.set_title("")
    g.figure.get_axes()[0].set_yscale('log')

    # Save the plot as SVG
    plt.tight_layout()
    g.figure.savefig(f".{"/slides" if slides else ""}/bound_stats/{name}/num_bounds.{"png" if slides else "svg"}", transparent=True, dpi=1200)
    g.figure.clf()


def plot_num_bounds2(dfs: Dict[str, pd.DataFrame], slides: bool):
    df: pd.DataFrame = pd.DataFrame()

    for test_name, test_df in dfs.items():
        df = pd.concat([df, test_df[["Test Name", "num_bounds"]]])

    # sort df by num_bounds ascending
    df = df.sort_values(by="num_bounds")

    # Order by Test Name
    df["Test Name"] = pd.Categorical(df["Test Name"], categories=[x for x in order if x in df["Test Name"].unique()], ordered=True).map(lambda x: f"\\texttt{{{x}}}")

    # For each TestName (group_outter): For each num_bounds (group_inner): Create a new column "perc_num_bounds" by count the number of occurrences in group inner / count the number of occurrences in group outer
    counts_df = df.groupby(['Test Name', 'num_bounds']).size().reset_index(name='count')
    total_counts_df = df.groupby('Test Name').size().reset_index(name='total_count')
    proportion_df = pd.merge(counts_df, total_counts_df, on='Test Name')
    proportion_df['perc_num_bounds'] = 100 * proportion_df['count'] / proportion_df['total_count']

    g = sns.catplot(
        data=proportion_df, x="num_bounds", y="perc_num_bounds", hue="Test Name",
        kind="bar"
    )
    sns.move_legend(g, loc="upper right", bbox_to_anchor=(1, 0.9))
    #if not slides:
        #g.set(title=f"Distribution of Number of Bounds")
    g.set_axis_labels("Number of Bounds", "Proportion (\\%)")
    g.legend.set_title("")
    g.figure.get_axes()[0].set_yscale('log')

    # Save the plot as SVG
    plt.tight_layout()
    g.figure.savefig(f".{"/slides" if slides else ""}/bound_stats/num_bounds.{"png" if slides else "svg"}", transparent=True, dpi=1200)
    g.figure.clf()


def plot_avg_num_bounds_vs_depth(name: str, dfs: Dict[str, pd.DataFrame], slides: bool):
    df: pd.DataFrame = pd.DataFrame()

    for test_name, test_df in dfs.items():
        df = pd.concat([df, test_df[["Test Name", "num_bounds", "depth"]]])

    # remove all the depths after 500
    df = df[df["depth"] <= 500]

    # group by Test Name and depth, compute average num_bounds to new column avg_num_bounds
    df["avg_num_bounds"] = df.groupby(["Test Name", "depth"])["num_bounds"].transform("mean")

    # group by Test Name and depth, compute 95% confidence interval to new columns lower_bound and upper_bound
    df["lower_bound"] = df.groupby(["Test Name", "depth"])["num_bounds"].transform(lambda x: st.t.interval(0.95, len(x)-1, loc=np.mean(x), scale=st.sem(x))[0])
    df["upper_bound"] = df.groupby(["Test Name", "depth"])["num_bounds"].transform(lambda x: st.t.interval(0.95, len(x)-1, loc=np.mean(x), scale=st.sem(x))[1])

    # replace any nan values in lower_bound and upper_bound with the corresponding avg_num_bounds
    df["lower_bound"] = df["lower_bound"].fillna(df["avg_num_bounds"])
    df["upper_bound"] = df["upper_bound"].fillna(df["avg_num_bounds"])

    for test_name in df["Test Name"].unique():
        subset = df[df["Test Name"] == test_name]
        avg_subset = subset[["depth", "avg_num_bounds"]].drop_duplicates(subset="depth").sort_values(by="depth")
        lower_bound = subset[["depth", "lower_bound"]].drop_duplicates(subset="depth").sort_values(by="depth")
        upper_bound = subset[["depth", "upper_bound"]].drop_duplicates(subset="depth").sort_values(by="depth")

        x = avg_subset["depth"]
        y = avg_subset["avg_num_bounds"]
        x_new = np.linspace(x.min(), x.max(), 200)

        # Spline for avg values
        spline = make_smoothing_spline(x, y)
        y_smooth = spline(x_new)

        # Spline for lower and upper bounds
        spline_lower = make_smoothing_spline(lower_bound["depth"], lower_bound["lower_bound"])
        spline_upper = make_smoothing_spline(upper_bound["depth"], upper_bound["upper_bound"])
        lower_smooth = spline_lower(x_new)
        upper_smooth = spline_upper(x_new)

        plt.plot(x_new, y_smooth, label=f'\\texttt{{{test_name}}}')
        plt.fill_between(x_new, lower_smooth, upper_smooth, alpha=0.2)

    # Save the plot as SVG
    plt.legend()
    plt.xlabel("Depth")
    plt.ylabel("Average Number of Bounds")
    #if not slides:
        #plt.title(f"Average Number of Bounds vs Depth")
    plt.tight_layout()
    plt.savefig(f".{"/slides" if slides else ""}/bound_stats/{name}/avg_num_bounds_vs_depth.{"png" if slides else "svg"}", transparent=True, dpi=1200)
    plt.clf()


def plot_avg_num_bounds(dfs: Dict[str, pd.DataFrame], slides: bool):
    df: pd.DataFrame = pd.DataFrame()

    for test_name, test_df in dfs.items():
        df = pd.concat([df, test_df[["Test Name", "num_bounds"]]])

    # compute average num_bounds in each test
    avg_num_bounds = df.groupby("Test Name").mean().reset_index()

    # Order by Test Name
    df["Test Name"] = pd.Categorical(df["Test Name"], categories=[x for x in order if x in df["Test Name"].unique()], ordered=True).map(lambda x: f"\\texttt{{{x}}}")

    g = sns.barplot(
        data=avg_num_bounds, x="Test Name", y="num_bounds"
    )
    #if not slides:
        #g.set(title=f"Average Number of Bounds")
    g.set_ylabel("Average Number of Bounds")
    g.set_xlabel("")
    plt.xticks(rotation=45)

    # Save the plot as SVG
    plt.tight_layout()
    g.figure.savefig(f".{"/slides" if slides else ""}/bound_stats/avg_num_bounds.{"png" if slides else "svg"}", transparent=True, dpi=1200)
    g.figure.clf()


def plot_depths_distribution(name: str, dfs: Dict[str, pd.DataFrame], slides: bool):
    df: pd.DataFrame = pd.DataFrame()

    for test_name, test_df in dfs.items():
        df = pd.concat([df, test_df[["Test Name", "depth"]]])

    g = sns.kdeplot(
        data=df, x="depth", hue="Test Name",
    )
    #if not slides:
        #g.set(title=f"Distribution of Depths")
    g.set_xlabel("Depth")
    g.set_ylabel("Density")
    g.get_legend().set_title("")

    # Save the plot as SVG
    plt.tight_layout()
    g.figure.savefig(f".{"/slides" if slides else ""}/bound_stats/{name}/depths_distribution.{"png" if slides else "svg"}", transparent=True, dpi=1200)
    g.figure.clf()
