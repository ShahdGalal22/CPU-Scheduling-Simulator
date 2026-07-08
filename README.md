# CPU Scheduling Simulator

A desktop application that simulates and compares classic CPU scheduling algorithms used in operating systems. Built with Python and Tkinter, it generates process data (randomly, from a file, or manually), runs multiple scheduling algorithms, and visualizes the results with a live Gantt chart.

## Features

- **Multiple scheduling algorithms:**
  - First Come First Served (FCFS)
  - Shortest Job First (SJF)
  - Priority Scheduling
  - Round Robin (with configurable quantum)
  - Multilevel Queue Scheduling
- **Three input modes:**
  - Random process generation (using normal/Poisson distributions via NumPy)
  - Load processes from a text file
  - Manual input with an editable table
- **Interactive Gantt chart** for visualizing each algorithm's execution timeline
- **Automatic performance comparison** — reports average waiting, turnaround, and response time per algorithm, and highlights the best-performing one for the given input
- **Copy-to-clipboard** support for exporting results
- **Editable process table** with double-click cell editing in manual mode

## Tech Stack

- **Python 3**
- **Tkinter** — GUI
- **NumPy** — random process generation

## How It Works

1. Choose an input mode: Random Generation, Load from File, or Manual Input
2. Set the number of processes and (optionally) the Round Robin/Multilevel Queue time quantum
3. Click **Run Algorithms** to execute all five scheduling algorithms on the same process set
4. View a full report (per-process waiting/turnaround/response times + averages) and switch between algorithms in the Gantt chart panel
5. Copy the output report to your clipboard for reports or submissions

### Input file format

```
5
10 10 1
0 12 1
3 8 1
5 4 1
12 6 1
```

- Line 1: number of processes
- Following lines: `arrival_time burst_time priority` for each process

## Installation

```bash
git clone https://github.com/yourusername/os-scheduler-simulator.git
cd os-scheduler-simulator
pip install numpy
python main.py
```

## Project Structure

```
├── main.py               # Tkinter GUI application
├── scheduler.py          # Scheduling algorithm implementations
├── process_generator.py  # Process class and random/file-based generation
└── output.txt             # Auto-generated process list (created at runtime)
```

## Author

Shahd Mohamed Galal 
