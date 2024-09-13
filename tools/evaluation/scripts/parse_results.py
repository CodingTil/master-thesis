from dataclasses import dataclass
from enum import Enum
import re
from typing import Tuple, List, Optional

class SolveStatus(Enum):
    SOLVED = "SOLVED"
    SOLVEDNOTVERIFIED = "SOLVED NOT VERIFIED"
    TIMEOUT = "TIMEOUT"
    FAIL = "FAIL"

@dataclass
class InstanceResult:
    name: str
    original_cons: int
    original_vars: int
    pricing_calls: int
    pricing_vars: int
    num_nodes: int
    solve_time: float
    solve_status: SolveStatus

@dataclass
class TestResult:
    name: str
    instance_results: List[InstanceResult]
    sgm_nodes: float
    sgm_time: float

def parse_solve_status(status_str: str) -> SolveStatus:
    if status_str in ["ok", "solved"]:
        return SolveStatus.SOLVED
    elif status_str in ["timeout", "abort"]:
        return SolveStatus.TIMEOUT
    elif status_str == "fail":
        return SolveStatus.FAIL
    elif status_str == "solved not verified":
        return SolveStatus.SOLVEDNOTVERIFIED
    else:
        raise ValueError(f"Unknown solve status: {status_str}")

def parse_instance_results(data: str) -> List[InstanceResult]:
    instance_results: List[InstanceResult] = []
    lines: List[str] = data.strip().split('\n')
    for line in lines:
        if len(line) == 0 or line.startswith("---") or line.startswith("Name"):
            continue
        parts: List[str] = re.split(r'\s+', line.strip())
        name: str = parts[0]
        original_cons: int = int(parts[2])
        original_vars: int = int(parts[3])
        pricing_calls: int = int(parts[16])
        pricing_vars: int = int(parts[17])
        num_nodes: int = int(parts[21])
        solve_time: float = float(parts[22])
        solve_status: SolveStatus = parse_solve_status(" ".join(parts[23:]))
        instance_result: InstanceResult = InstanceResult(name, original_cons, original_vars, pricing_calls, pricing_vars, num_nodes, solve_time, solve_status)
        instance_results.append(instance_result)
    return instance_results

def parse_summary(summary: str) -> Tuple[float, float]:
    lines: List[str] = summary.strip().split('\n')
    sgm_nodes: Optional[float] = None
    sgm_time: Optional[float] = None
    for line in lines:
        if "shifted geom." in line:
            parts: List[str] = re.split(r'\s+', line.strip())
            sgm_nodes = float(parts[4])
            sgm_time = float(parts[5])
    return sgm_nodes, sgm_time

def extract_data_str(input_text: str, name: str) -> TestResult:
    parts: List[str] = input_text.strip().split("\n\n")
    instance_data: str = parts[0]
    summary_data: str = parts[1]

    instance_results: List[InstanceResult] = parse_instance_results(instance_data)
    sgm_nodes, sgm_time = parse_summary(summary_data)

    return TestResult(name, instance_results, sgm_nodes, sgm_time)

def extract_data_file(input_file: str) -> TestResult:
    with open(input_file, 'r') as f:
        input_text: str = f.read()
    name: str = input_file.split("/")[-1].split(".")[-3]
    return extract_data_str(input_text, name)
