import seaborn as sns
import matplotlib.pyplot as plt
import pandas as pd
from typing import List
from collections import OrderedDict

from parse_results import SolveStatus, TestResult, InstanceResult

order = [
    "compbnd",
    "compbnd+dvs",
    "compbnd-mdm",
    "compbnd-mdm+dvs",
    "compbnd-mrm",
    "compbnd-mrm+dvs"
]

def plot_outperforms_other(name: str, other: str, test_results: List[TestResult], slides: bool):
    generic: TestResult = filter(lambda x: x.name == other, test_results).__next__()
    other_results = [x for x in test_results if not x.name.startswith("generic")]

    instances_size = len(generic.instance_results) # universal for all test_results

    generic_solved_instances = 0

    # Prepare data for seaborn
    data = OrderedDict()
    for index in range(instances_size):
        generic_instance: InstanceResult = generic.instance_results[index]
        if generic_instance.solve_status == SolveStatus.FAIL:
            continue
        if generic_instance.solve_status == SolveStatus.TIMEOUT and generic_instance.num_nodes == 0:
            continue

        if generic_instance.solve_status == SolveStatus.TIMEOUT:
            assert generic_instance.solve_time >= 599

        generic_solved_instances += 1

        for test_result in other_results:
            other_instance: InstanceResult = test_result.instance_results[index]

            assert(generic_instance.name == other_instance.name)

            if other_instance.solve_status == SolveStatus.FAIL:
                continue
            if other_instance.solve_status == SolveStatus.TIMEOUT and other_instance.num_nodes == 0:
                continue

            if other_instance.solve_status == SolveStatus.TIMEOUT:
                assert other_instance.solve_time >= 599

            if other_instance.solve_time < generic_instance.solve_time:
                #print(f"Test {test_result.name} outperforms generic on instance {index} with time {other_instance.solve_time} < {generic_instance.solve_time}")
                tmp_name = test_result.name
                if tmp_name not in data:
                    data[tmp_name] = 0
                data[tmp_name] += 1

    df = pd.DataFrame(data.items(), columns=["Test Name", "Count"])
    df["Fraction"] = df["Count"] / generic_solved_instances * 100
    df["Test Name"] = pd.Categorical(df["Test Name"], categories=[x for x in order if x in df["Test Name"].unique()], ordered=True).map(lambda x: f"\\texttt{{{x}}}")

    g = sns.catplot(
        data=df, kind="bar",
        x="Test Name", y="Fraction"
    )
    if not slides:
        #g.set(title=f"{"" if slides else f"{name} $\\cdot$ "}Outperformance Rate over \\texttt{{{other}}}")
        plt.xticks(rotation=45)
    g.set_axis_labels("", f"Outperformance Rate (\\%)")

    # Save the plot as SVG
    plt.tight_layout()
    g.figure.savefig(f'.{"/slides" if slides else ""}/general/{name}/outperforms_{other}.{"png" if slides else "svg"}', transparent=True, dpi=1200)
    g.figure.clf()

def plot_outperforms_generic(name: str, test_results: List[TestResult], slides: bool):
    plot_outperforms_other(name, "generic", test_results, slides)
    plot_outperforms_other(name, "generic-mip", test_results, slides)
