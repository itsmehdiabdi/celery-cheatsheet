"""
Playground.

Run this module after starting the worker to try examples, or copy snippets
into a shell. All examples assume a result backend is configured.

Calling (official docs: userguide/calling.html):
- delay(*args, **kwargs) — shortcut for apply_async((args), {kwargs})
- apply_async(args=(), kwargs={}, countdown=..., eta=..., expires=..., queue=..., link=...)
- Calling the task (e.g. add(2, 2)) runs it in the current process (no broker).

Canvas (official docs: userguide/canvas.html):
- signature / .s() / .si(): wrap (args, kwargs, options) for a single invocation
- chain: task1 -> task2 -> ... (each gets previous return as first arg)
- group: run tasks in parallel; result is list of results
- chord: group + callback; callback gets list of group results
- map / starmap: one task per element (map: f(a), f(b); starmap: f(*a), f(*b))
- chunks: split iterable into chunks, one task per chunk
"""

import os
from celery import chain, chord, group, result
from typing import Any
from proj.tasks import add, mul, xsum


# -----------------------------------------------------------------------------
# Calling: delay vs apply_async
# -----------------------------------------------------------------------------


def example_delay_and_apply_async():
    """
    delay(4, 5) is equivalent to apply_async((4, 5)).
    apply_async supports: countdown, eta, expires, queue, link, link_error, etc.
    """
    r1 = add.delay(4, 5)
    _assert_task_result(r1, 9)

    r2 = add.apply_async((4, 5), countdown=0)  # run as soon as worker picks it up
    _assert_task_result(r2, 9)

    # ETA: run at a specific time (datetime, UTC). Prefer countdown for short delays.
    # from datetime import datetime, timedelta, timezone
    # add.apply_async((1, 2), eta=datetime.now(timezone.utc) + timedelta(seconds=5))

    # Expires: task is revoked if not run before expiry (seconds or datetime).
    # add.apply_async((1, 2), expires=60)


# -----------------------------------------------------------------------------
# Signatures: .s() (partial) and .si() (immutable, no args from parent)
# -----------------------------------------------------------------------------


def example_signatures():
    """
    add.s(2, 2) creates a signature: task + args + optional options.
    .delay() or .apply_async() on a signature sends it to the broker.
    .s(2) is a partial: add(?, 2); when used as callback, parent result is prepended.
    .si(2, 2) is immutable: callback won't receive parent result (use for side-effect only).
    """
    sig = add.s(2, 2)
    r = sig.delay()
    _assert_task_result(r, 4)

    # Partial: add.s(10) -> add(result, 10) when used as link
    partial = add.s(10)
    r = add.apply_async((2, 2), link=partial)  # first 2+2=4, then 4+10=14
    _assert_task_result(r, 4)
    _assert_task_result(r.children[0], 14)


# -----------------------------------------------------------------------------
# Chain: task1 | task2 | task3 — each gets previous return as first arg
# -----------------------------------------------------------------------------


def example_chain():
    """
    chain(add.s(2, 2), mul.s(8), mul.s(10)) => add(2,2)=4 -> mul(4,8)=32 -> mul(32,10)=320.
    Pipe form: (add.s(2, 2) | mul.s(8) | mul.s(10)).apply_async()
    """
    c = chain(add.s(2, 2), mul.s(8), mul.s(10))
    result = c.apply_async()
    _assert_task_result(result, 320)
    _assert_task_result(result.parent, 32)
    _assert_task_result(result.parent.parent, 4)


# -----------------------------------------------------------------------------
# Group: run many tasks in parallel; result is GroupResult, .get() -> list
# -----------------------------------------------------------------------------


def example_group():
    """
    group(add.s(i, i) for i in range(5)) runs 5 tasks in parallel.
    .get() returns [0, 2, 4, 6, 8] in order.
    """
    g = group(add.s(i, i) for i in range(5))
    result = g.apply_async()
    _assert_task_result(result, [0, 2, 4, 6, 8])


# -----------------------------------------------------------------------------
# Chord: group + callback; callback receives list of group results
# -----------------------------------------------------------------------------


def example_chord():
    """
    chord(header_tasks, callback): run header tasks in parallel, then run
    callback with the list of their results. Requires result backend.
    Tasks in chord must not use ignore_result=True.
    """
    header = [add.s(i, i) for i in range(10)]  # [0,2,4,...,18]
    callback = xsum.s()  # sum([0,2,...,18]) = 90
    result = chord(header)(callback)
    _assert_task_result(result, 90)


# -----------------------------------------------------------------------------
# Chain + group: group chained to a task becomes a chord
# -----------------------------------------------------------------------------


def example_chain_group_becomes_chord():
    """
    (group(...) | task.s()) is automatically a chord: group results -> task.
    """
    result = (group(add.s(i, i) for i in range(10)) | xsum.s()).apply_async()
    _assert_task_result(result, 90)


# -----------------------------------------------------------------------------
# Map and starmap (single task message; runs in one worker)
# -----------------------------------------------------------------------------


def example_starmap():
    """
    add.starmap([(1,1), (2,2), (3,3)]) => one task that runs add(1,1), add(2,2), add(3,3)
    and returns [2, 4, 6]. Different from group: sequential in one process, one message.
    """
    result = add.starmap(zip(range(5), range(5))).apply_async()
    _assert_task_result(result, [0, 2, 4, 6, 8])


# -----------------------------------------------------------------------------
# Chunks: split work into chunks (e.g. 1000 items -> 10 tasks of 100)
# -----------------------------------------------------------------------------


def example_chunks():
    """
    add.chunks(zip(range(10), range(10)), 3) => 4 chunks (3+3+3+1).
    Each chunk task runs add on 3 pairs and returns a list. Result is list of lists.
    """
    result = add.chunks(zip(range(10), range(10)), 3).apply_async()
    _assert_task_result(result, [[0, 2, 4], [6, 8, 10], [12, 14, 16], [18]])


def _clear_screen():
    if os.name == "nt":
        os.system("cls")
    else:
        os.system("clear")


def _exit():
    print("Exiting...")
    exit(0)


def _assert_task_result(result: result.AsyncResult, expected: Any):
    print("\n" + "=" * 80)
    print(f"🔍 TASK CREATED:")
    _print_task_summary(result)
    print(f"⏳ Waiting for task completion (timeout: 10s)...")
    got = result.get(timeout=10)
    assert got == expected, f"Assertion failed: expected {expected}, got {got}"
    print(f"✅ Task completed successfully:")
    _print_task_summary(result)
    print("=" * 80 + "\n")


def _print_task_summary(result: result.AsyncResult):
    children = getattr(result, "children") or []
    parent = getattr(result, "parent", "N/A")
    summary = {
        "id": getattr(result, "id", "N/A"),
        "name": getattr(result, "name", "N/A"),
        "args": getattr(result, "args", "N/A"),
        "kwargs": getattr(result, "kwargs", "N/A"),
        "retries": getattr(result, "retries", "N/A"),
        "queue": getattr(result, "queue", "N/A"),
        "status": getattr(result, "state", "N/A"),
        "result": getattr(result, "result", "N/A"),
        "children": [child.id for child in children],
        "parent": getattr(parent, "id", "N/A"),
    }
    print(summary)


# -----------------------------------------------------------------------------
# Run all examples (worker must be up and result backend configured)
# -----------------------------------------------------------------------------

if __name__ == "__main__":
    choices = {
        "1": example_delay_and_apply_async,
        "2": example_signatures,
        "3": example_chain,
        "4": example_group,
        "5": example_chord,
        "6": example_chain_group_becomes_chord,
        "7": example_starmap,
        "8": example_chunks,
        "c": _clear_screen,
        "exit": _exit,
    }
    while True:
        print("Enter the choice:")
        for choice_name, fn in choices.items():
            print(f"{choice_name}: {fn.__name__}")
        choice = input()
        if not choice in choices:
            print(f"Invalid choice: {choice}")
            continue
        choices[choice]()
