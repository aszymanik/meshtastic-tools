
# installation

python3 -m venv .
bin/pip install beautifulsoup4 requests paho-mqtt
source bin/activate

# usage
configure config.json file. the payload_from field is your node ID in decimal
python3 get_and_send_weather.py


