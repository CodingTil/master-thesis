import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt

from typing import Dict, List
from pathlib import Path
import argparse

from plot_bound_stats import plot_num_bounds, plot_num_bounds2, plot_avg_num_bounds, plot_avg_num_bounds_vs_depth, plot_depths_distribution

def extract_name(csv_file: str) -> str:
    # remove .csv
    name = csv_file[:-4]
    # remove "../check/results_stats/stats_"
    name = name[len("../check/results_stats/stats_"):]
    return name

def detail(name: str, dfs: Dict[str, pd.DataFrame], slides: bool):
    # Create the output directory
    output_directory = Path(f".{"/slides" if slides else ""}/bound_stats/{name}")
    output_directory.mkdir(parents=True, exist_ok=True)

    plot_num_bounds(name, dfs, slides)
    plot_avg_num_bounds_vs_depth(name, dfs, slides)
    plot_depths_distribution(name, dfs, slides)


def all(dfs: Dict[str, pd.DataFrame], slides: bool):
    plot_avg_num_bounds(dfs, slides)
    plot_num_bounds2(dfs, slides)


def preprocess(csv_file: str):
    print(f"Preprocessing {csv_file}")

    # Open the CSV file and read its lines
    with open(csv_file, "r") as f:
        lines = f.readlines()

    # Filter out lines with more than 3 commas
    filtered_lines = [line for line in lines if line.count(",") <= 3]

    # Write the filtered lines back to the CSV file
    with open(csv_file, "w") as f:
        f.writelines(filtered_lines)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--slides", action="store_true")

    csv_files: List[str] = [
        "../check/results_stats/stats_compbnd.csv",
        "../check/results_stats/stats_compbnd+dvs.csv",
    ]

    parsed_args = parser.parse_args()

    if not parsed_args.slides:
        csv_files += [
            "../check/results_stats/stats_compbnd-mdm.csv",
            "../check/results_stats/stats_compbnd-mdm+dvs.csv",
            "../check/results_stats/stats_compbnd-mrm.csv",
            "../check/results_stats/stats_compbnd-mrm+dvs.csv"
        ]

    for csv_file in csv_files:
        preprocess(csv_file)

    names: List[str] = [extract_name(csv_file) for csv_file in csv_files]

    dfs: Dict[str, pd.DataFrame] = {}
    for name, csv_file in zip(names, csv_files):
        print(f"Reading {csv_file}")
        df = pd.read_csv(csv_file)
        df["Test Name"] = name
        dfs[name] = df

    # set style
    plt.rcParams["text.usetex"] = True
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = "Latin Modern Sans"
    sns.set_theme(context="talk", style="white") # , rc={"figure.figsize": (1.3837000138370001, 0.855173638784966)}

    # only compbnd and compbnd+dvs
    detail("compbnd", {name: dfs[name] for name in names[:2]}, parsed_args.slides)
    if not parsed_args.slides:
        detail("compbnd-mdm", {name: dfs[name] for name in names[2:4]}, parsed_args.slides)
        detail("compbnd-mrm", {name: dfs[name] for name in names[4:]}, parsed_args.slides)

    all(dfs, parsed_args.slides)
