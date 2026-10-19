
import random

# Simulation configuration
DEFECT_PROBABILITY = 0.05  # 5% expected defect rate


def inspect_workpiece():
    """Simulate quality inspection using a configurable defect probability."""
    if random.random() < DEFECT_PROBABILITY:
        return "DEFECT"

    return "OK"
