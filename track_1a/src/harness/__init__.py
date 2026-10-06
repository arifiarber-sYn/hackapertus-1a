"""Reusable red-teaming harness for Track 1A (stdlib only).

    python3 track_1a/src/harness/collect.py --battery track_1a/data/example_battery.json --dry-run
    python3 track_1a/src/harness/collect.py --battery my_battery.json --limit 20

See track_1a/docs/add-your-battery.md. The collector reuses the comparator of src/reproduce.py
(`krahaso`) so that collection and replay judge responses with the same logic.
"""
