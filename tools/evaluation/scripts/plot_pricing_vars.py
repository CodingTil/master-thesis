import matplotlib.pyplot as plt
import pandas as pd
import seaborn as sns
from typing import List, Callable

from parse_results import TestResult, SolveStatus

def plot_pricing_vars(name: str, test_results: List[TestResult], slides: bool):
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
                "Pricing Vars": instance.pricing_vars
            })

    df = pd.DataFrame(data)

    g = sns.boxplot(
        data=df, x="Test Name", y="Pricing Vars",
        showfliers=False, showmeans=True,
        meanprops={'marker':'o','markerfacecolor':'white','markeredgecolor':'black','markersize':'8'}
    )
    if not slides:
        #g.set(title=f"{"" if slides else f"{name} $\\cdot$ "}Nodes")
        plt.xticks(rotation=45)
    g.set_xlabel("")

    # Save the plot as SVG
    plt.tight_layout()
    g.figure.savefig(f'.{"/slides" if slides else ""}/general/{name}/pricing_vars.{"png" if slides else "svg"}', transparent=True, dpi=1200)
    g.figure.clf()
