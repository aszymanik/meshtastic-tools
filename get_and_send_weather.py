import requests
from bs4 import BeautifulSoup
import math
import paho.mqtt.publish as publish
import json

# Load config
with open('config.json', 'r') as f:
    config = json.load(f)

mqtt_host = config["mqtt_host"]
mqtt_port = config["mqtt_port"]
mqtt_username = config["mqtt_username"]
mqtt_password = config["mqtt_password"]
payload_from = config["payload_from"]
channel = config["channel"]
forecast_url = config["url"]

def get_top_two_forecasts():
    response = requests.get(forecast_url)
    response.raise_for_status()

    soup = BeautifulSoup(response.text, 'html.parser')

    table = soup.find_all('table', attrs={'width': '800'})[1]
    if not table:
        return "Forecast table not found."

    td = table.find('td')
    if not td:
        return "Forecast data not found."

    forecasts = []
    for bold in td.find_all('b'):
        period = bold.get_text(strip=True)
        forecast_text = ''
        
        for elem in bold.next_siblings:
            if elem.name == 'b' or elem.name == 'hr':
                break
            if isinstance(elem, str):
                forecast_text += elem.strip() + ' '
            elif elem.name == 'br':
                continue
        
        full_forecast = f"{period} {forecast_text.strip()}"
        forecasts.append(full_forecast)

        if len(forecasts) == 2:
            break

    return forecasts

def split_forecast(forecast, max_total_length=200):
    reserved_space = 6  # Space for (1/3) etc.
    max_chunk_length = max_total_length - reserved_space

    words = forecast.split()
    chunks = []
    current_chunk = ''

    for word in words:
        if len(current_chunk) + len(word) + 1 > max_chunk_length:
            chunks.append(current_chunk.strip())
            current_chunk = word
        else:
            if current_chunk:
                current_chunk += ' ' + word
            else:
                current_chunk = word

    if current_chunk:
        chunks.append(current_chunk.strip())

    return chunks

def process_forecasts(forecasts, max_total_length=200):
    all_chunks = []

    for forecast in forecasts:
        if len(forecast) + 6 <= max_total_length:
            all_chunks.append(forecast)
        else:
            chunks = split_forecast(forecast, max_total_length)
            all_chunks.extend(chunks)

    total = len(all_chunks)
    final_chunks = []
    for idx, chunk in enumerate(all_chunks, start=1):
        index_text = f" ({idx}/{total})"
        if len(chunk) + len(index_text) > max_total_length:
            chunk = chunk[:max_total_length - len(index_text)].rstrip()
        final_chunks.append(chunk + index_text)

    return final_chunks

def publish_forecasts(forecast_lines):
    auth = {'username': mqtt_username, 'password': mqtt_password}

    for line in forecast_lines:
        payload = {
            "from": payload_from,
            "channel": channel,
            "type": "sendtext",
            "payload": line
        }
        publish.single(
            topic="msh/US/2/json/mqtt/",
            payload=json.dumps(payload),
            hostname=mqtt_host,
            port=mqtt_port,
            auth=auth
        )
        print(f"Published: {payload}")

if __name__ == "__main__":
    forecasts = get_top_two_forecasts()
    split_chunks = process_forecasts(forecasts)
    publish_forecasts(split_chunks)
