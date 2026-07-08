import os

import numpy as np


class Process:
    def __init__(self, pid, arrival, burst, priority):
        self.pid = str(pid)
        self.arrival = max(0, int(arrival))
        self.burst = max(1, int(burst))
        self.priority = max(0, int(priority))

        self.remaining = self.burst
        self.finish = 0
        self.waiting = 0
        self.turnaround = 0
        self.response = 0
        self.first_start = None


def _clean_input_lines(filename):
    with open(filename, "r", encoding="utf-8") as file:
        lines = []
        for raw_line in file:
            line = raw_line.split("#", 1)[0].strip()
            if line:
                lines.append(line)
    return lines


def _parse_two_numbers(line, label):
    parts = line.split()
    if len(parts) != 2:
        raise ValueError(f"{label} must contain exactly two numbers.")

    try:
        return float(parts[0]), float(parts[1])
    except ValueError as error:
        raise ValueError(f"{label} must contain valid numbers.") from error


def _validate_parameters(n, arrival_std, burst_mean, burst_std, priority_lambda):
    if n < 1:
        raise ValueError("Number of processes must be at least 1.")
    if arrival_std < 0:
        raise ValueError("Arrival standard deviation cannot be negative.")
    if burst_mean <= 0:
        raise ValueError("Burst mean must be greater than 0.")
    if burst_std < 0:
        raise ValueError("Burst standard deviation cannot be negative.")
    if priority_lambda < 0:
        raise ValueError("Priority lambda cannot be negative.")


def read_input_file(filename):
    lines = _clean_input_lines(filename)

    if len(lines) != 4:
        raise ValueError(
            "Invalid input file format. Expected exactly 4 non-empty lines:\n"
            "1) number of processes\n"
            "2) arrival mean and arrival standard deviation\n"
            "3) burst mean and burst standard deviation\n"
            "4) priority lambda"
        )

    try:
        n = int(lines[0])
    except ValueError as error:
        raise ValueError("Number of processes must be an integer.") from error

    arrival_mean, arrival_std = _parse_two_numbers(lines[1], "Arrival line")
    burst_mean, burst_std = _parse_two_numbers(lines[2], "Burst line")

    try:
        priority_lambda = float(lines[3])
    except ValueError as error:
        raise ValueError("Priority lambda must be a valid number.") from error

    _validate_parameters(n, arrival_std, burst_mean, burst_std, priority_lambda)
    return n, arrival_mean, arrival_std, burst_mean, burst_std, priority_lambda


def generate_processes(
    n=5,
    arrival_mean=5,
    arrival_std=2,
    burst_mean=8,
    burst_std=2,
    priority_lambda=3,
):
    n = int(n)
    _validate_parameters(n, arrival_std, burst_mean, burst_std, priority_lambda)

    processes = []
    for i in range(n):
        arrival = np.random.normal(arrival_mean, arrival_std)
        burst = np.random.normal(burst_mean, burst_std)
        priority = np.random.poisson(priority_lambda)
        processes.append(Process(f"P{i + 1}", arrival, burst, priority))

    return processes


def save_processes(processes, output_file):
    output_dir = os.path.dirname(os.path.abspath(output_file))
    if output_dir:
        os.makedirs(output_dir, exist_ok=True)

    with open(output_file, "w", encoding="utf-8") as file:
        file.write(f"{len(processes)}\n")
        for process in processes:
            file.write(f"{process.pid} {process.arrival} {process.burst} {process.priority}\n")


def generate_processes_from_file(input_file, output_file):
    n, arrival_mean, arrival_std, burst_mean, burst_std, priority_lambda = read_input_file(input_file)
    processes = generate_processes(
        n,
        arrival_mean,
        arrival_std,
        burst_mean,
        burst_std,
        priority_lambda,
    )
    save_processes(processes, output_file)
    return processes
