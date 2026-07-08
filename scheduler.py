from collections import deque


def calculate_times(processes):
    if not processes:
        return 0, 0, 0

    total_waiting = sum(p.waiting for p in processes)
    total_turnaround = sum(p.turnaround for p in processes)
    total_response = sum(p.response for p in processes)
    return (
        total_waiting / len(processes),
        total_turnaround / len(processes),
        total_response / len(processes),
    )


def _validate_quantum(quantum):
    try:
        quantum = int(quantum)
    except (TypeError, ValueError) as error:
        raise ValueError("Quantum must be an integer.") from error

    if quantum <= 0:
        raise ValueError("Quantum must be greater than 0.")

    return quantum


def _reset_processes(processes):
    for process in processes:
        process.remaining = process.burst
        process.finish = 0
        process.waiting = 0
        process.turnaround = 0
        process.response = 0
        process.first_start = None


def _start_process(process, start_time):
    if process.first_start is None:
        process.first_start = start_time


def _finish_process(process, finish_time):
    if process.first_start is None:
        process.first_start = finish_time - process.burst

    process.finish = finish_time
    process.turnaround = process.finish - process.arrival
    process.waiting = process.turnaround - process.burst
    process.response = process.first_start - process.arrival


def _add_gantt_segment(gantt, pid, start, end):
    if end <= start:
        return

    if gantt and gantt[-1][0] == pid and gantt[-1][2] == start:
        previous_pid, previous_start, _ = gantt[-1]
        gantt[-1] = (previous_pid, previous_start, end)
    else:
        gantt.append((pid, start, end))


def _return_result(done, gantt, return_gantt):
    if return_gantt:
        return done, gantt
    return done


def fcfs(processes, return_gantt=False):
    if not processes:
        return _return_result([], [], return_gantt)

    _reset_processes(processes)
    processes = sorted(processes, key=lambda p: (p.arrival, p.pid))
    gantt = []
    time = 0

    for process in processes:
        if time < process.arrival:
            _add_gantt_segment(gantt, "IDLE", time, process.arrival)
            time = process.arrival

        start = time
        _start_process(process, start)
        time += process.burst
        _add_gantt_segment(gantt, process.pid, start, time)
        _finish_process(process, time)

    return _return_result(processes, gantt, return_gantt)


def sjf(processes, return_gantt=False):
    if not processes:
        return _return_result([], [], return_gantt)

    _reset_processes(processes)
    pending = sorted(processes, key=lambda p: (p.arrival, p.pid))
    ready = []
    done = []
    gantt = []
    time = 0
    index = 0

    while index < len(pending) or ready:
        while index < len(pending) and pending[index].arrival <= time:
            ready.append(pending[index])
            index += 1

        if not ready:
            next_time = pending[index].arrival
            _add_gantt_segment(gantt, "IDLE", time, next_time)
            time = next_time
            continue

        process = min(ready, key=lambda p: (p.burst, p.arrival, p.pid))
        ready.remove(process)

        start = time
        _start_process(process, start)
        time += process.burst
        _add_gantt_segment(gantt, process.pid, start, time)
        _finish_process(process, time)
        done.append(process)

    return _return_result(done, gantt, return_gantt)


def priority_sched(processes, return_gantt=False):
    if not processes:
        return _return_result([], [], return_gantt)

    _reset_processes(processes)
    pending = sorted(processes, key=lambda p: (p.arrival, p.priority, p.pid))
    ready = []
    done = []
    gantt = []
    time = 0
    index = 0

    while index < len(pending) or ready:
        while index < len(pending) and pending[index].arrival <= time:
            ready.append(pending[index])
            index += 1

        if not ready:
            next_time = pending[index].arrival
            _add_gantt_segment(gantt, "IDLE", time, next_time)
            time = next_time
            continue

        process = min(ready, key=lambda p: (p.priority, p.arrival, p.pid))
        ready.remove(process)

        start = time
        _start_process(process, start)
        time += process.burst
        _add_gantt_segment(gantt, process.pid, start, time)
        _finish_process(process, time)
        done.append(process)

    return _return_result(done, gantt, return_gantt)


def round_robin(processes, quantum=2, return_gantt=False):
    quantum = _validate_quantum(quantum)

    if not processes:
        return _return_result([], [], return_gantt)

    _reset_processes(processes)
    pending = sorted(processes, key=lambda p: (p.arrival, p.pid))
    queue = deque()
    done = []
    gantt = []
    time = 0
    index = 0

    while index < len(pending) or queue:
        while index < len(pending) and pending[index].arrival <= time:
            queue.append(pending[index])
            index += 1

        if not queue:
            next_time = pending[index].arrival
            _add_gantt_segment(gantt, "IDLE", time, next_time)
            time = next_time
            continue

        process = queue.popleft()
        start = time
        _start_process(process, start)
        # لو باقي اقل من الكوانت تشتغل كله لو عكس كده الكوانت بس
        run_time = min(quantum, process.remaining)
        time += run_time
        process.remaining -= run_time
        _add_gantt_segment(gantt, process.pid, start, time)

        while index < len(pending) and pending[index].arrival <= time:
            queue.append(pending[index])
            index += 1

        if process.remaining > 0:
            queue.append(process)
        else:
            _finish_process(process, time)
            done.append(process)

    return _return_result(done, gantt, return_gantt)


def multilevel_queue(processes, quantum=2, return_gantt=False):
    quantum = _validate_quantum(quantum)

    if not processes:
        return _return_result([], [], return_gantt)

    _reset_processes(processes)
    pending = sorted(processes, key=lambda p: (p.arrival, p.pid))
    high_queue = []
    low_queue = deque()
    done = []
    gantt = []
    time = 0
    index = 0

    while index < len(pending) or high_queue or low_queue:
        while index < len(pending) and pending[index].arrival <= time:
            process = pending[index]
            if process.priority <= 2:
                high_queue.append(process)
            else:
                low_queue.append(process)
            index += 1

        if high_queue:
            process = min(high_queue, key=lambda p: (p.priority, p.arrival, p.pid))
            high_queue.remove(process)

            start = time
            _start_process(process, start)
            time += process.remaining
            _add_gantt_segment(gantt, process.pid, start, time)
            process.remaining = 0
            _finish_process(process, time)
            done.append(process)
            continue

        if low_queue:
            process = low_queue.popleft()
            start = time
            _start_process(process, start)
            run_time = min(quantum, process.remaining)
            time += run_time
            process.remaining -= run_time
            _add_gantt_segment(gantt, process.pid, start, time)

            while index < len(pending) and pending[index].arrival <= time:
                arrived = pending[index]
                if arrived.priority <= 2:
                    high_queue.append(arrived)
                else:
                    low_queue.append(arrived)
                index += 1

            if process.remaining > 0:
                low_queue.append(process)
            else:
                _finish_process(process, time)
                done.append(process)
            continue

        next_time = pending[index].arrival
        _add_gantt_segment(gantt, "IDLE", time, next_time)
        time = next_time

    return _return_result(done, gantt, return_gantt)
