import requests

def get_answer(question: str, dataset: str):
    url = "http://127.0.0.1:8000"
    response = requests.get(url, params={"question":question, "dataset":dataset})
    return response.json()

question = input()
dataset = input()

quries = get_answer(question, dataset)
for i in quries:
    print(i)