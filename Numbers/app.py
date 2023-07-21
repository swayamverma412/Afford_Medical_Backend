from flask import Flask, request, jsonify
import requests
import concurrent.futures

app = Flask(__name__)

def fetch_numbers(url):
    try:
        response = requests.get(url)
        response.raise_for_status()
        data = response.json()
        if "numbers" in data and isinstance(data["numbers"], list):
            return data["numbers"]
    except (requests.exceptions.RequestException, ValueError):
        pass
    return []

@app.route('/numbers')
def get_numbers():
    urls = request.args.getlist("url")
    unique_numbers = set()

    with concurrent.futures.ThreadPoolExecutor() as executor:
        future_to_url = {executor.submit(fetch_numbers, url): url for url in urls}
        for future in concurrent.futures.as_completed(future_to_url):
            url = future_to_url[future]
            numbers = future.result()
            unique_numbers.update(numbers)

    sorted_numbers = sorted(unique_numbers)
    response = {"numbers": sorted_numbers}
    return jsonify(response)

if __name__ == '__main__':
    app.run(port=3000)
