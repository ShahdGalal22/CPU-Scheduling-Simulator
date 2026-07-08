import copy
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

from process_generator import Process, generate_processes, generate_processes_from_file, save_processes
from scheduler import fcfs, sjf, priority_sched, round_robin, multilevel_queue, calculate_times


class App:
    def __init__(self, root):
        self.root = root
        self.root.title("OS Scheduler")
        self.root.geometry("1080x760")
        self.root.minsize(920, 680)
        self.root.configure(bg="#f3f4f6")

        self.project_dir = os.path.dirname(os.path.abspath(__file__))
        self.output_file_path = os.path.join(self.project_dir, "output.txt")
        self.input_file_path = ""

        self.processes = []
        self.gantt_data = {}
        self.table_editor = None
        self.table_editor_info = None
        self.input_mode_var = tk.StringVar(value="Random Generation")
        self.previous_input_mode = self.input_mode_var.get()
        self.process_count_var = tk.IntVar(value=5)
        self.quantum_var = tk.IntVar(value=2)
        self.gantt_algorithm_var = tk.StringVar(value="")
        self.status_var = tk.StringVar(value="Ready. Load an input file or generate random processes.")

        self.configure_style()
        self.build_menu()
        self.build_layout()
        self.clear_gantt_chart()

    def configure_style(self):
        self.style = ttk.Style()
        try:
            self.style.theme_use("clam")
        except tk.TclError:
            pass

        self.style.configure("App.TFrame", background="#f3f4f6")
        self.style.configure("Panel.TLabelframe", background="#ffffff", bordercolor="#d1d5db")
        self.style.configure(
            "Panel.TLabelframe.Label",
            background="#f3f4f6",
            foreground="#111827",
            font=("Segoe UI", 10, "bold"),
        )
        self.style.configure("Title.TLabel", background="#f3f4f6", foreground="#111827", font=("Segoe UI", 20, "bold"))
        self.style.configure("Subtitle.TLabel", background="#f3f4f6", foreground="#4b5563", font=("Segoe UI", 10))
        self.style.configure("Field.TLabel", background="#f3f4f6", foreground="#374151", font=("Segoe UI", 10))
        self.style.configure("Status.TLabel", background="#f3f4f6", foreground="#4b5563", font=("Segoe UI", 9))
        self.style.configure("TButton", font=("Segoe UI", 10), padding=(12, 7))
        self.style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"), foreground="#ffffff", background="#2563eb")
        self.style.map(
            "Accent.TButton",
            background=[("active", "#1d4ed8"), ("disabled", "#93c5fd")],
            foreground=[("disabled", "#eff6ff")],
        )
        self.style.configure("Treeview", rowheight=28, font=("Segoe UI", 10))
        self.style.configure("Treeview.Heading", font=("Segoe UI", 10, "bold"))

    def build_menu(self):
        menu_bar = tk.Menu(self.root)

        file_menu = tk.Menu(menu_bar, tearoff=False)
        file_menu.add_command(label="Load Input File", command=self.load_input_file, accelerator="Ctrl+O")
        menu_bar.add_cascade(label="File", menu=file_menu)

        edit_menu = tk.Menu(menu_bar, tearoff=False)
        edit_menu.add_command(label="Copy Output", command=self.copy_output, accelerator="Ctrl+Shift+C")
        edit_menu.add_command(label="Clear Output", command=self.clear_output)
        menu_bar.add_cascade(label="Edit", menu=edit_menu)

        self.root.config(menu=menu_bar)
        self.root.bind("<Control-o>", lambda event: self.load_input_file())
        self.root.bind("<Control-O>", lambda event: self.load_input_file())
        self.root.bind("<Control-Shift-C>", lambda event: self.copy_output())

    def build_layout(self):
        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)

        main = ttk.Frame(self.root, padding=22, style="App.TFrame")
        main.grid(row=0, column=0, sticky="nsew")
        main.columnconfigure(0, weight=1)
        main.rowconfigure(2, weight=1)

        header = ttk.Frame(main, style="App.TFrame")
        header.grid(row=0, column=0, sticky="ew", pady=(0, 14))
        header.columnconfigure(0, weight=1)

        ttk.Label(header, text="CPU Scheduling Simulator", style="Title.TLabel").grid(row=0, column=0, sticky="w")
        ttk.Label(
            header,
            text="Load parameters, generate processes, run scheduling algorithms, and copy results.",
            style="Subtitle.TLabel",
        ).grid(row=1, column=0, sticky="w", pady=(4, 0))

        controls = ttk.Frame(main, style="App.TFrame")
        controls.grid(row=1, column=0, sticky="ew", pady=(0, 16))
        controls.columnconfigure(9, weight=1)

        ttk.Label(controls, text="Processes", style="Field.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.process_count_spinbox = tk.Spinbox(
            controls,
            from_=1,
            to=50,
            width=5,
            textvariable=self.process_count_var,
            font=("Segoe UI", 10),
            relief="solid",
            bd=1,
            command=self.on_process_count_changed,
        )
        self.process_count_spinbox.grid(row=0, column=1, sticky="w", padx=(0, 18))
        self.process_count_spinbox.bind("<Return>", self.on_process_count_changed)
        self.process_count_spinbox.bind("<FocusOut>", self.on_process_count_changed)

        ttk.Label(controls, text="Quantum", style="Field.TLabel").grid(row=0, column=2, sticky="w", padx=(0, 8))
        self.quantum_spinbox = tk.Spinbox(
            controls,
            from_=1,
            to=20,
            width=5,
            textvariable=self.quantum_var,
            font=("Segoe UI", 10),
            relief="solid",
            bd=1,
        )
        self.quantum_spinbox.grid(row=0, column=3, sticky="w", padx=(0, 18))

        ttk.Label(controls, text="Mode", style="Field.TLabel").grid(row=1, column=0, sticky="w", padx=(0, 8), pady=(8, 0))
        self.input_mode_combo = ttk.Combobox(
            controls,
            textvariable=self.input_mode_var,
            values=("Random Generation", "Load from File", "Manual Input"),
            state="readonly",
            width=18,
        )
        self.input_mode_combo.grid(row=1, column=1, columnspan=3, sticky="w", pady=(8, 0))
        self.input_mode_combo.bind("<<ComboboxSelected>>", self.on_input_mode_changed)

        ttk.Button(controls, text="Load Input File", command=self.load_input_file, style="Accent.TButton").grid(
            row=0, column=4, sticky="w", padx=(0, 8)
        )
        ttk.Button(controls, text="Generate", command=self.generate).grid(row=0, column=5, sticky="w", padx=(0, 8))
        self.run_button = ttk.Button(controls, text="Run Algorithms", command=self.run, state=tk.DISABLED)
        self.run_button.grid(row=0, column=6, sticky="w", padx=(0, 8))
        self.copy_button = ttk.Button(controls, text="Copy Output", command=self.copy_output, state=tk.DISABLED)
        self.copy_button.grid(row=0, column=7, sticky="w", padx=(0, 8))
        ttk.Button(controls, text="Clear", command=self.clear_output).grid(row=0, column=8, sticky="w")

        content = ttk.Frame(main, style="App.TFrame")
        content.grid(row=2, column=0, sticky="nsew")
        content.columnconfigure(0, weight=1, minsize=300)
        content.columnconfigure(1, weight=3)
        content.rowconfigure(0, weight=1)

        process_panel = ttk.LabelFrame(content, text="Generated Processes", padding=12, style="Panel.TLabelframe")
        process_panel.grid(row=0, column=0, sticky="nsew", padx=(0, 12))
        process_panel.columnconfigure(0, weight=1)
        process_panel.rowconfigure(0, weight=1)

        table_frame = ttk.Frame(process_panel)
        table_frame.grid(row=0, column=0, sticky="nsew")
        table_frame.columnconfigure(0, weight=1)
        table_frame.rowconfigure(0, weight=1)

        columns = ("pid", "arrival", "burst", "priority")
        self.process_table = ttk.Treeview(table_frame, columns=columns, show="headings", height=15)
        self.process_table.heading("pid", text="PID")
        self.process_table.heading("arrival", text="Arrival")
        self.process_table.heading("burst", text="Burst")
        self.process_table.heading("priority", text="Priority")
        self.process_table.column("pid", width=70, anchor=tk.CENTER, stretch=False)
        self.process_table.column("arrival", width=90, anchor=tk.CENTER)
        self.process_table.column("burst", width=90, anchor=tk.CENTER)
        self.process_table.column("priority", width=90, anchor=tk.CENTER)
        self.process_table.grid(row=0, column=0, sticky="nsew")
        self.process_table.bind("<Double-1>", self.begin_table_edit)

        process_scroll = ttk.Scrollbar(table_frame, orient=tk.VERTICAL, command=self.process_table.yview)
        process_scroll.grid(row=0, column=1, sticky="ns")
        self.process_table.configure(yscrollcommand=process_scroll.set)

        results_panel = ttk.LabelFrame(content, text="Results", padding=12, style="Panel.TLabelframe")
        results_panel.grid(row=0, column=1, sticky="nsew")
        results_panel.columnconfigure(0, weight=1)
        results_panel.rowconfigure(0, weight=1)
        results_panel.rowconfigure(1, weight=0)

        output_frame = ttk.Frame(results_panel)
        output_frame.grid(row=0, column=0, sticky="nsew")
        output_frame.columnconfigure(0, weight=1)
        output_frame.rowconfigure(0, weight=1)

        self.output = tk.Text(
            output_frame,
            height=20,
            width=70,
            wrap="word",
            bg="#111827",
            fg="#e5e7eb",
            insertbackground="#e5e7eb",
            selectbackground="#2563eb",
            selectforeground="#ffffff",
            relief="flat",
            padx=14,
            pady=12,
            font=("Consolas", 10),
            state=tk.DISABLED,
        )
        self.output.grid(row=0, column=0, sticky="nsew")
        self.output.bind("<Button-3>", self.show_output_menu)
        self.output.bind("<Control-c>", self.copy_selected_output)
        self.output.bind("<Control-C>", self.copy_selected_output)

        output_scroll = ttk.Scrollbar(output_frame, orient=tk.VERTICAL, command=self.output.yview)
        output_scroll.grid(row=0, column=1, sticky="ns")
        self.output.configure(yscrollcommand=output_scroll.set)

        self.build_gantt_panel(results_panel)

        self.output_menu = tk.Menu(self.root, tearoff=False)
        self.output_menu.add_command(label="Copy Selection", command=self.copy_selected_text)
        self.output_menu.add_command(label="Copy All Output", command=self.copy_output)

        ttk.Label(main, textvariable=self.status_var, style="Status.TLabel").grid(row=3, column=0, sticky="w", pady=(12, 0))

    def build_gantt_panel(self, parent):
        gantt_panel = ttk.LabelFrame(parent, text="Gantt Chart", padding=12, style="Panel.TLabelframe")
        gantt_panel.grid(row=1, column=0, sticky="ew", pady=(12, 0))
        gantt_panel.columnconfigure(0, weight=1)

        toolbar = ttk.Frame(gantt_panel)
        toolbar.grid(row=0, column=0, sticky="ew", pady=(0, 8))
        toolbar.columnconfigure(1, weight=1)

        ttk.Label(toolbar, text="Algorithm", style="Field.TLabel").grid(row=0, column=0, sticky="w", padx=(0, 8))
        self.gantt_combo = ttk.Combobox(
            toolbar,
            textvariable=self.gantt_algorithm_var,
            state="disabled",
            width=26,
            values=[],
        )
        self.gantt_combo.grid(row=0, column=1, sticky="w")
        self.gantt_combo.bind("<<ComboboxSelected>>", lambda event: self.draw_selected_gantt())

        canvas_frame = ttk.Frame(gantt_panel)
        canvas_frame.grid(row=1, column=0, sticky="ew")
        canvas_frame.columnconfigure(0, weight=1)

        self.gantt_canvas = tk.Canvas(
            canvas_frame,
            height=145,
            bg="#ffffff",
            highlightthickness=1,
            highlightbackground="#d1d5db",
        )
        self.gantt_canvas.grid(row=0, column=0, sticky="ew")
        self.gantt_canvas.bind("<Configure>", lambda event: self.draw_selected_gantt())

    def read_int(self, variable, default, minimum, maximum, label):
        try:
            value = int(variable.get())
        except (tk.TclError, ValueError):
            value = default

        clamped = max(minimum, min(maximum, value))
        if clamped != value:
            self.status_var.set(f"{label} was adjusted to {clamped}.")
        variable.set(clamped)
        return clamped

    def on_input_mode_changed(self, event=None):
        self.close_table_editor()
        selected_mode = self.input_mode_var.get()

        if selected_mode == "Random Generation":
            if self.generate():
                self.previous_input_mode = selected_mode
            else:
                self.input_mode_var.set(self.previous_input_mode)
        elif selected_mode == "Load from File":
            if self.load_input_file():
                self.previous_input_mode = selected_mode
            else:
                self.input_mode_var.set(self.previous_input_mode)
        elif selected_mode == "Manual Input":
            self.ensure_manual_rows()
            self.run_button.configure(state=tk.NORMAL)
            self.previous_input_mode = selected_mode
            self.status_var.set("Manual input enabled. Double-click Arrival, Burst, or Priority to edit.")

    def ensure_manual_rows(self):
        count = self.read_int(self.process_count_var, default=5, minimum=1, maximum=50, label="Process count")
        existing_values = [
            self.process_table.item(item, "values")
            for item in self.process_table.get_children()
        ]

        self.clear_process_table()
        for index in range(count):
            if index < len(existing_values):
                values = list(existing_values[index])
                values[0] = f"P{index + 1}"
            else:
                values = (f"P{index + 1}", 0, 1, 1)

            self.process_table.insert("", tk.END, values=values)

    def on_process_count_changed(self, event=None):
        mode = self.input_mode_var.get()

        if mode == "Manual Input":
            self.close_table_editor()
            self.ensure_manual_rows()
            self.processes = []
            self.clear_gantt_chart()
            self.set_output("")
            self.run_button.configure(state=tk.NORMAL)
            self.status_var.set("Manual input rows updated.")
        elif mode == "Random Generation":
            self.generate()
        else:
            self.status_var.set("Process count is controlled by the loaded file.")

    def begin_table_edit(self, event):
        if self.input_mode_var.get() != "Manual Input":
            return

        item = self.process_table.identify_row(event.y)
        column = self.process_table.identify_column(event.x)
        editable_columns = {"#2", "#3", "#4"}

        if not item or column not in editable_columns:
            return

        bbox = self.process_table.bbox(item, column)
        if not bbox:
            return

        self.close_table_editor()

        x, y, width, height = bbox
        values = list(self.process_table.item(item, "values"))
        column_index = int(column[1:]) - 1

        self.table_editor = tk.Entry(self.process_table, font=("Segoe UI", 10), justify="center")
        self.table_editor.insert(0, values[column_index])
        self.table_editor.select_range(0, tk.END)
        self.table_editor.place(x=x, y=y, width=width, height=height)
        self.table_editor.focus_set()
        self.table_editor_info = (item, column_index)

        self.table_editor.bind("<Return>", self.save_table_edit)
        self.table_editor.bind("<FocusOut>", self.save_table_edit)
        self.table_editor.bind("<Escape>", self.close_table_editor)

    def save_table_edit(self, event=None):
        if not self.table_editor or not self.table_editor_info:
            return

        item, column_index = self.table_editor_info
        values = list(self.process_table.item(item, "values"))
        values[column_index] = self.table_editor.get().strip()
        self.process_table.item(item, values=values)
        self.close_table_editor()
        self.clear_gantt_chart()

    def close_table_editor(self, event=None):
        if self.table_editor is not None:
            self.table_editor.destroy()
        self.table_editor = None
        self.table_editor_info = None

    def read_manual_processes(self):
        processes = []

        for row_number, item in enumerate(self.process_table.get_children(), start=1):
            pid, arrival, burst, priority = self.process_table.item(item, "values")

            try:
                arrival = int(arrival)
                burst = int(burst)
                priority = int(priority)
            except ValueError as error:
                raise ValueError(f"Row {row_number} contains non-numeric values.") from error

            if arrival < 0:
                raise ValueError(f"{pid}: arrival must be greater than or equal to 0.")
            if burst < 1:
                raise ValueError(f"{pid}: burst must be greater than or equal to 1.")
            if priority < 1:
                raise ValueError(f"{pid}: priority must be greater than or equal to 1.")

            processes.append(Process(pid, arrival, burst, priority))

        if not processes:
            raise ValueError("Manual input requires at least one process.")

        return processes

    def load_input_file(self):
        self.close_table_editor()
        file_path = filedialog.askopenfilename(
            title="Select Input File",
            filetypes=[("Text files", "*.txt"), ("All files", "*.*")],
        )

        if not file_path:
            return False

        try:
            self.processes = generate_processes_from_file(file_path, self.output_file_path)
        except (OSError, ValueError) as error:
            self.root.bell()
            messagebox.showerror(
                "Invalid Input File",
                "Could not load the selected file.\n\n"
                "Expected format:\n"
                "5\n"
                "5 2\n"
                "8 2\n"
                "3\n\n"
                f"Details: {error}",
            )
            self.status_var.set("Input file was not loaded.")
            return False

        self.input_file_path = file_path
        self.input_mode_var.set("Load from File")
        self.previous_input_mode = "Load from File"
        self.process_count_var.set(len(self.processes))
        self.populate_process_table()
        self.clear_gantt_chart()
        self.set_output(self.format_generated_processes())
        self.run_button.configure(state=tk.NORMAL)
        self.status_var.set(f"Loaded {len(self.processes)} processes and saved output.txt.")
        return True

    def set_output(self, text):
        self.output.configure(state=tk.NORMAL)
        self.output.delete("1.0", tk.END)
        self.output.insert(tk.END, text)
        self.output.configure(state=tk.DISABLED)
        self.output.see(tk.END)
        self.copy_button.configure(state=tk.NORMAL if text.strip() else tk.DISABLED)

    def append_output(self, text):
        self.output.configure(state=tk.NORMAL)
        self.output.insert(tk.END, text)
        self.output.configure(state=tk.DISABLED)
        self.output.see(tk.END)
        self.copy_button.configure(state=tk.NORMAL)

    def clear_output(self):
        self.close_table_editor()
        self.processes = []
        self.input_file_path = ""
        self.clear_process_table()
        self.set_output("")
        self.clear_gantt_chart()
        self.run_button.configure(state=tk.DISABLED)
        self.status_var.set("Input and output cleared.")

    def clear_process_table(self):
        for item in self.process_table.get_children():
            self.process_table.delete(item)

    def populate_process_table(self):
        self.clear_process_table()

        for process in self.processes:
            self.process_table.insert(
                "",
                tk.END,
                values=(process.pid, process.arrival, process.burst, process.priority),
            )

    def generate(self):
        self.close_table_editor()
        count = self.read_int(self.process_count_var, default=5, minimum=1, maximum=50, label="Process count")

        try:
            self.processes = generate_processes(count)
            save_processes(self.processes, self.output_file_path)
        except (OSError, ValueError) as error:
            self.root.bell()
            messagebox.showerror("Generate Error", str(error))
            self.status_var.set("Could not generate processes.")
            return False

        self.input_file_path = ""
        self.input_mode_var.set("Random Generation")
        self.previous_input_mode = "Random Generation"
        self.populate_process_table()
        self.clear_gantt_chart()
        self.set_output(self.format_generated_processes())
        self.run_button.configure(state=tk.NORMAL)
        self.status_var.set(f"Generated {count} process{'es' if count != 1 else ''} and saved output.txt.")
        return True

    def format_generated_processes(self):
        lines = ["Generated Processes", ""]

        if self.input_mode_var.get() == "Manual Input":
            lines.append("Input file:  manual input")
        elif self.input_file_path:
            lines.append(f"Input file:  {self.input_file_path}")
        else:
            lines.append("Input file:  random defaults")

        lines.extend(
            [
                f"Output file: {self.output_file_path}",
                "",
                f"{'PID':<8}{'Arrival':>10}{'Burst':>10}{'Priority':>12}",
                "-" * 40,
            ]
        )

        for process in self.processes:
            lines.append(f"{process.pid:<8}{process.arrival:>10}{process.burst:>10}{process.priority:>12}")
        return "\n".join(lines) + "\n"

    def format_result(self, name, result):
        lines = [
            "",
            name,
            "-" * len(name),
            f"{'PID':<8}{'Waiting':>10}{'Turnaround':>14}{'Response':>12}",
        ]

        for process in result:
            lines.append(
                f"{process.pid:<8}"
                f"{process.waiting:>10}"
                f"{process.turnaround:>14}"
                f"{process.response:>12}"
            )

        avg_waiting, avg_turnaround, avg_response = calculate_times(result)
        lines.append("")
        lines.append(f"Average waiting time:    {avg_waiting:.2f}")
        lines.append(f"Average turnaround time: {avg_turnaround:.2f}")
        lines.append(f"Average response time:   {avg_response:.2f}")
        return "\n".join(lines) + "\n"

    def format_best_algorithm(self, algorithm_results):
        scores = []

        for name, result in algorithm_results:
            avg_waiting, avg_turnaround, avg_response = calculate_times(result)
            scores.append((avg_waiting, avg_turnaround, avg_response, name))

        avg_waiting, avg_turnaround, avg_response, best_name = min(scores)

        lines = [
            "",
            "Best Algorithm",
            "--------------",
            f"{best_name} is best for this input.",
            "Selection rule: lowest average waiting time, then turnaround time, then response time.",
            "",
            f"Average waiting time:    {avg_waiting:.2f}",
            f"Average turnaround time: {avg_turnaround:.2f}",
            f"Average response time:   {avg_response:.2f}",
        ]
        return "\n".join(lines) + "\n"

    def run(self):
        if self.input_mode_var.get() == "Manual Input":
            try:
                self.close_table_editor()
                self.processes = self.read_manual_processes()
                save_processes(self.processes, self.output_file_path)
                self.input_file_path = ""
            except (OSError, ValueError) as error:
                self.root.bell()
                messagebox.showerror("Manual Input Error", str(error))
                self.status_var.set("Manual input is invalid.")
                return

        if not self.processes:
            self.root.bell()
            self.status_var.set("Load or generate processes before running algorithms.")
            return

        quantum = self.read_int(self.quantum_var, default=2, minimum=1, maximum=20, label="Quantum")
        report = [
            self.format_generated_processes(),
            "\nAll Algorithms",
            "==============",
        ]

        try:
            algorithm_runs = [
                ("FCFS", fcfs(copy.deepcopy(self.processes), return_gantt=True)),
                ("SJF", sjf(copy.deepcopy(self.processes), return_gantt=True)),
                ("Priority", priority_sched(copy.deepcopy(self.processes), return_gantt=True)),
                (
                    f"Round Robin (q={quantum})",
                    round_robin(copy.deepcopy(self.processes), quantum, return_gantt=True),
                ),
                (
                    f"Multilevel Queue (q={quantum})",
                    multilevel_queue(copy.deepcopy(self.processes), quantum, return_gantt=True),
                ),
            ]
        except ValueError as error:
            self.root.bell()
            messagebox.showerror("Scheduling Error", str(error))
            self.status_var.set("Scheduling failed.")
            return

        self.gantt_data = {}
        algorithm_results = []
        for name, (result, gantt) in algorithm_runs:
            report.append(self.format_result(name, result))
            self.gantt_data[name] = gantt
            algorithm_results.append((name, result))

        report.append(self.format_best_algorithm(algorithm_results))

        self.refresh_gantt_options()
        self.set_output("\n".join(report))
        self.status_var.set("All algorithms completed.")

    def refresh_gantt_options(self):
        algorithm_names = list(self.gantt_data.keys())

        if not algorithm_names:
            self.clear_gantt_chart()
            return

        self.gantt_combo.configure(values=algorithm_names, state="readonly")
        self.gantt_algorithm_var.set(algorithm_names[0])
        self.draw_selected_gantt()

    def clear_gantt_chart(self):
        self.gantt_data = {}

        if hasattr(self, "gantt_combo"):
            self.gantt_combo.configure(values=[], state="disabled")
            self.gantt_algorithm_var.set("")

        if hasattr(self, "gantt_canvas"):
            self.gantt_canvas.delete("all")
            canvas_width = max(self.gantt_canvas.winfo_width(), 640)
            self.gantt_canvas.configure(scrollregion=(0, 0, canvas_width, 145))
            self.gantt_canvas.create_text(
                16,
                72,
                anchor="w",
                text="Run algorithms to display the Gantt chart.",
                fill="#6b7280",
                font=("Segoe UI", 10),
            )

    def get_gantt_color(self, pid):
        if pid == "IDLE":
            return "#e5e7eb", "#374151"

        colors = [
            "#2563eb",
            "#059669",
            "#dc2626",
            "#7c3aed",
            "#ea580c",
            "#0891b2",
            "#be123c",
            "#4f46e5",
            "#16a34a",
            "#9333ea",
        ]
        index = sum(ord(char) for char in str(pid)) % len(colors)
        return colors[index], "#ffffff"

    def draw_selected_gantt(self):
        if not hasattr(self, "gantt_canvas"):
            return

        algorithm_name = self.gantt_algorithm_var.get()
        segments = self.gantt_data.get(algorithm_name, [])
        self.draw_gantt_chart(algorithm_name, segments)

    def draw_gantt_chart(self, algorithm_name, segments):
        self.gantt_canvas.delete("all")

        canvas_width = max(self.gantt_canvas.winfo_width(), 640)
        canvas_height = 145
        left_padding = 28
        right_padding = 28
        top = 46
        bar_height = 44

        if not segments:
            self.gantt_canvas.configure(scrollregion=(0, 0, canvas_width, canvas_height))
            self.gantt_canvas.create_text(
                16,
                72,
                anchor="w",
                text="Run algorithms to display the Gantt chart.",
                fill="#6b7280",
                font=("Segoe UI", 10),
            )
            return

        start_time = min(start for _, start, _ in segments)
        end_time = max(end for _, _, end in segments)
        duration = max(1, end_time - start_time)
        available_width = canvas_width - left_padding - right_padding
        unit_width = available_width / duration

        def x_for_time(time_value):
            return left_padding + (time_value - start_time) * unit_width

        self.gantt_canvas.create_text(
            left_padding,
            20,
            anchor="w",
            text=algorithm_name,
            fill="#111827",
            font=("Segoe UI", 10, "bold"),
        )

        for pid, start, end in segments:
            x1 = x_for_time(start)
            x2 = x_for_time(end)
            fill, text_color = self.get_gantt_color(pid)

            self.gantt_canvas.create_rectangle(
                x1,
                top,
                x2,
                top + bar_height,
                fill=fill,
                outline="#ffffff",
                width=2,
            )

            if x2 - x1 >= 34:
                self.gantt_canvas.create_text(
                    (x1 + x2) / 2,
                    top + bar_height / 2,
                    text=pid,
                    fill=text_color,
                    font=("Segoe UI", 9, "bold"),
                )

        boundaries = sorted({start_time, end_time, *[start for _, start, _ in segments], *[end for _, _, end in segments]})
        last_label_x = -100

        for boundary in boundaries:
            x = x_for_time(boundary)
            self.gantt_canvas.create_line(x, top + bar_height, x, top + bar_height + 7, fill="#6b7280")

            if x - last_label_x >= 28 or boundary in (start_time, end_time):
                self.gantt_canvas.create_text(
                    x,
                    top + bar_height + 22,
                    text=str(boundary),
                    fill="#374151",
                    font=("Segoe UI", 8),
                )
                last_label_x = x

        self.gantt_canvas.configure(scrollregion=(0, 0, canvas_width, canvas_height))

    def copy_to_clipboard(self, text, status):
        text = text.strip()
        if not text:
            self.root.bell()
            self.status_var.set("There is no output to copy.")
            return

        self.root.clipboard_clear()
        self.root.clipboard_append(text)
        self.root.update()
        self.status_var.set(status)

    def copy_output(self):
        self.copy_to_clipboard(self.output.get("1.0", tk.END), "Output copied to clipboard.")

    def copy_selected_text(self):
        try:
            text = self.output.get(tk.SEL_FIRST, tk.SEL_LAST)
        except tk.TclError:
            self.copy_output()
            return
        self.copy_to_clipboard(text, "Selected text copied to clipboard.")

    def copy_selected_output(self, event=None):
        self.copy_selected_text()
        return "break"

    def show_output_menu(self, event):
        try:
            self.output.get(tk.SEL_FIRST, tk.SEL_LAST)
            has_selection = True
        except tk.TclError:
            has_selection = False

        self.output_menu.entryconfigure("Copy Selection", state=tk.NORMAL if has_selection else tk.DISABLED)
        try:
            self.output_menu.tk_popup(event.x_root, event.y_root)
        finally:
            self.output_menu.grab_release()


if __name__ == "__main__":
    root = tk.Tk()
    app = App(root)
    root.mainloop()
