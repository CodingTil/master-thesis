import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from typing import List, Callable

from parse_results import TestResult, SolveStatus

def plot_nodes(name: str, test_results: List[TestResult], slides: bool):
    # Prepare data for seaborn
    data = []
    for test_result in test_results:
        for instance in test_result.instance_results:
            if instance.solve_status == SolveStatus.FAIL:
                continue
            if instance.solve_status == SolveStatus.TIMEOUT and instance.num_nodes == 0:
                continue
            data.append({
                "Test Name": f"\\texttt{{{test_result.name}}}",
                "Nodes": instance.num_nodes
            })

    df = pd.DataFrame(data)

    g = sns.boxplot(
        data=df, x="Test Name", y="Nodes",
        showfliers=False, showmeans=True,
        meanprops={'marker':'o','markerfacecolor':'white','markeredgecolor':'black','markersize':'8'}
    )
    if not slides:
        #g.set(title=f"{"" if slides else f"{name} $\\cdot$ "}Nodes")
        plt.xticks(rotation=45)
    g.set_xlabel("")

    # Save the plot as SVG
    plt.tight_layout()
    g.figure.savefig(f'.{"/slides" if slides else ""}/general/{name}/nodes.{"png" if slides else "svg"}', transparent=True, dpi=1200)
    g.figure.clf()

def plot_times(name: str, test_results: List[TestResult], slides: bool):
    # Prepare data for seaborn
    data = []
    for test_result in test_results:
        for instance in test_result.instance_results:
            if instance.solve_status == SolveStatus.FAIL:
                continue
            data.append({
                "Test Name": f"\\texttt{{{test_result.name}}}",
                "Solving Times": instance.solve_time
            })

    df = pd.DataFrame(data)

    g = sns.boxplot(
        data=df, x="Test Name", y="Solving Times",
        showfliers=False, showmeans=True,
        meanprops={'marker':'o','markerfacecolor':'white','markeredgecolor':'black','markersize':'8'}
    )
    g.set_xlabel("")
    g.set_ylabel("Solving Time (s)")
    if not slides:
        #g.set(title=f"{"" if slides else f"{name} $\\cdot$ "}Solving Time (s)")
        plt.xticks(rotation=45)

    # Save the plot as SVG
    plt.tight_layout()
    g.figure.savefig(f'.{"/slides" if slides else ""}/general/{name}/times.{"png" if slides else "svg"}', transparent=True, dpi=1200)
    g.figure.clf()
