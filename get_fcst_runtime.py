import requests
from datetime import datetime, timezone

def get_fcst_time(model):

    url = f"https://api.open-meteo.com/data/{model}/static/meta.json"

    data = requests.get(url).json()
    ts = data["last_run_initialisation_time"]
    latest_run = datetime.fromtimestamp(ts, tz=timezone.utc)
    run_str = latest_run.strftime("%Y-%m-%dT%H:%M")

    print(f"Using fcst time: {run_str}")

    return run_str