import requests

url = "https://j01.app.n8n.cloud/webhook-test/Production-result"

data = {
    "result": "OK",
    "timestamp": "test"
}

response = requests.post(url, json=data, timeout=10)

print(response.status_code)
print(response.text)