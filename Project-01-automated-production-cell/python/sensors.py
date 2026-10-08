import random


def workpiece_detected():
    """Simulate the workpiece sensor."""
    return random.random() < 0.8


def position_reached():
    """Simulate the position sensor."""
    return random.random() < 0.9

def fault_detected():
    """Simulate a machine fault."""
    return random.random() < 0.05