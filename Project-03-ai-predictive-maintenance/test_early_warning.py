
METRICS = {
    "Temperature": {
        "unit": "°C",
        "warning": 70.0,
        "critical": 85.0,
        "minimum_rise": 5.0,
    },
    "Vibration": {
        "unit": "mm/s RMS",
        "warning": 4.5,
        "critical": 7.1,
        "minimum_rise": 0.5,
    },
    "Current": {
        "unit": "A",
        "warning": 4.0,
        "critical": 5.0,
        "minimum_rise": 0.3,
    },
}


def check_trend(metric, earlier_values, recent_values):
    config = METRICS[metric]
    earlier_mean = sum(earlier_values) / len(earlier_values)
    recent_mean = sum(recent_values) / len(recent_values)
    change = recent_mean - earlier_mean

    unit = config["unit"]
    warning = config["warning"]
    critical = config["critical"]

    print(f"\n{metric}")
    print(f"Earlier average: {earlier_mean:.2f} {unit}")
    print(f"Recent average:  {recent_mean:.2f} {unit}")
    print(f"Change:          {change:+.2f} {unit}")

    if recent_mean >= critical:
        print("RESULT: CRITICAL LEVEL REACHED")
    elif recent_mean >= warning:
        print("RESULT: WARNING THRESHOLD REACHED")
    elif (
        change >= config["minimum_rise"]
        and recent_mean >= warning * 0.70
    ):
        print("RESULT: EARLY WARNING - rising trend")
    else:
        print("RESULT: NORMAL - no early warning")


def main():
    print("=" * 60)
    print("JAY01 EARLY-WARNING TEST SUITE")
    print("Synthetic data only - database unchanged")
    print("=" * 60)

    scenarios = [
        (
            "TEST 1: Normal readings",
            {
                "Temperature": ([25, 26, 25, 26], [26, 27, 26, 27]),
                "Vibration": ([1.5, 1.6, 1.7], [1.7, 1.8, 1.9]),
                "Current": ([2.0, 2.1, 2.0], [2.1, 2.2, 2.1]),
            },
        ),
        (
            "TEST 2: Rising trends below warning thresholds",
            {
                "Temperature": ([40, 41, 42], [49, 50, 51]),
                "Vibration": ([2.0, 2.1, 2.2], [3.0, 3.2, 3.4]),
                "Current": ([2.0, 2.1, 2.2], [3.0, 3.2, 3.4]),
            },
        ),
        (
            "TEST 3: Warning thresholds reached",
            {
                "Temperature": ([60, 61, 62], [70, 71, 72]),
                "Vibration": ([3.0, 3.1, 3.2], [4.5, 4.6, 4.7]),
                "Current": ([3.0, 3.1, 3.2], [4.0, 4.1, 4.2]),
            },
        ),
        (
            "TEST 4: Critical thresholds reached",
            {
                "Temperature": ([70, 72, 74], [85, 86, 87]),
                "Vibration": ([4.0, 4.2, 4.4], [7.1, 7.2, 7.3]),
                "Current": ([3.5, 3.6, 3.7], [5.0, 5.1, 5.2]),
            },
        ),
    ]

    for title, readings in scenarios:
        print(f"\n{'=' * 60}\n{title}\n{'=' * 60}")
        for metric, (earlier, recent) in readings.items():
            check_trend(metric, earlier, recent)


if __name__ == "__main__":
    main()
