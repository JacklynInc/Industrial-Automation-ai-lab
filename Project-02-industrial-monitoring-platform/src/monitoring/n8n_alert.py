import requests


N8N_WEBHOOK_URL = "https://j01.app.n8n.cloud/webhook/industrial-monitoring-alert"


def send_alert(measurement):
    if measurement["status"] not in ("WARNING", "CRITICAL"):
        return

    response = requests.post(
        N8N_WEBHOOK_URL,
        json=measurement,
        timeout=10
    )

    response.raise_for_status()

    print("Alert sent to n8n")