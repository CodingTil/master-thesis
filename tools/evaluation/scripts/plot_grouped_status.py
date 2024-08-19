import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
from collections import Counter
from typing import List, Dict
from parse_results import SolveStatus, TestResult

def count_solve_status(test_results: List[TestResult]) -> Dict[str, Counter[SolveStatus]]:
    return {result.name: Counter([instance.solve_status if instance.solve_status is not SolveStatus.SOLVEDNOTVERIFIED else SolveStatus.SOLVED for instance in result.instance_results]) for result in test_results}

def plot_solve_status_counts(name: str, test_results: List[TestResult], slides: bool):
    status_counts: Dict[str, Counter[SolveStatus]] = count_solve_status(test_results)

    # Prepare data for seaborn
    data = []
    for test_result in test_results:
        for status in SolveStatus:
            count = status_counts[test_result.name][status]
            if count == 0:
                continue
            data.append({
                "Test Name": f"\\texttt{{{test_result.name}}}",
                "Solve Status": status.value,
                "Count": count
            })

    df = pd.DataFrame(data)

    # Draw a nested barplot
    g = sns.catplot(
        data=df, kind="bar",
        x="Solve Status", y="Count", hue="Test Name"
    )
    #if not slides:
        #g.set(title=f"{"" if slides else f"{name} $\\cdot$ "}Solve Status Counts")
    g.set_axis_labels("", "Number of Instances")
    g.legend.set_title("")

    # Save the plot as SVG
    plt.tight_layout()
    g.figure.savefig(f'.{"/slides" if slides else ""}/general/{name}/solve_status.{"png" if slides else "svg"}', transparent=True, dpi=1200)
    g.figure.clf()
