import os
import argparse
from pathlib import Path
from typing import List
import seaborn as sns
import matplotlib.pyplot as plt

from parse_results import TestResult, extract_data_file
from plot_grouped_status import plot_solve_status_counts
from plot_nodes_time import plot_nodes, plot_times
from plot_outperforms_generic import plot_outperforms_generic
from plot_pricing_calls import plot_pricing_calls
from plot_pricing_vars import plot_pricing_vars

order = [
    "generic",
    "generic-mip",
    "compbnd",
    "compbnd+dvs",
    "compbnd-mdm",
    "compbnd-mdm+dvs",
    "compbnd-mrm",
    "compbnd-mrm+dvs"
]
order_index = {name: i for i, name in enumerate(order)}

def set_style():
    plt.rcParams["text.usetex"] = True
    plt.rcParams["font.family"] = "sans-serif"
    plt.rcParams["font.sans-serif"] = "Latin Modern Sans"
    sns.set_theme(context="talk", style="white") # , rc={"figure.figsize": (1.3837000138370001, 0.855173638784966)}

def main(name: str, directory_path: str, slides: bool):
    # Check if the provided path is a directory
    if not os.path.isdir(directory_path):
        print(f"The provided path '{directory_path}' is not a directory.")
        return

    # Get all .res files in the directory
    res_files: List[Path] = list(Path(directory_path).glob("*.res"))

    if not res_files:
        print(f"No .res files found in the directory '{directory_path}'.")
        return

    print(f"Found {len(res_files)} .res files in the directory '{directory_path}'.")

    # Process the .res files
    test_results: List[TestResult] = [extract_data_file(str(res_file.absolute())) for res_file in res_files]

    if slides:
        test_results = [test_result for test_result in test_results if test_result.name in ["generic", "generic-mip", "compbnd", "compbnd+dvs"]]

    # Sort the test results
    test_results.sort(key=lambda x: order_index.get(x.name))

    # Create the output directory
    output_directory = Path(f".{"/slides" if slides else ""}/general/{name}")
    output_directory.mkdir(parents=True, exist_ok=True)

    # Set style
    set_style()

    # Export plots
    plot_solve_status_counts(name, test_results, slides)
    plot_nodes(name, test_results, slides)
    plot_times(name, test_results, slides)
    plot_pricing_calls(name, test_results, slides)
    plot_pricing_vars(name, test_results, slides)
    plot_outperforms_generic(name, test_results, slides)


if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument("--slides", action="store_true")

    parsed_args = parser.parse_args()

    main("MostFractional", "../check/results_mostfractional", parsed_args.slides)
    if not parsed_args.slides:
        main("ClosestToZHalf", "../check/results_closestkhalf", parsed_args.slides)
