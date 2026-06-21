import numpy as np
from openmeteo_sdk.Variable import Variable
import openmeteo_requests
import matplotlib.pyplot as plt
from datetime import date, timedelta
import calendar

sites = {
    "stonyhurst": {"latitude": 53.85, "longitude": -1.53},
    "rothamsted": {"latitude": 51.81, "longitude": -0.36},
    "pershore": {"latitude": 52.15, "longitude": -2.04}
}

openmeteo = openmeteo_requests.Client()
url = "https://api.open-meteo.com/v1/forecast"

def compute_cet(model, cet_type, cet_in_flag):

    if cet_in_flag:
        start_date = date.today()
    else:
        # if yesterday's CET isn't in yet, use yesterday's forecast
        start_date = date.today() - timedelta(days=1)
    last_day = calendar.monthrange(start_date.year, start_date.month)[1]
    end_date = date(start_date.year, start_date.month, last_day)

    num_days_to_endmonth = (end_date - start_date).days + 1
    cet_daily = np.zeros((num_days_to_endmonth, 3))
    cet = np.array(num_days_to_endmonth)

    for i, site in enumerate(sites):
        
        print(f"Fetching data for site: {site} from {start_date} to {end_date} ({num_days_to_endmonth})")
        params = {
            "latitude": sites[site]["latitude"],
            "longitude": sites[site]["longitude"],
            "daily": ["temperature_2m_max", "temperature_2m_min"],
            "models": model,
            "start_date": start_date.isoformat(),
            "end_date": end_date.isoformat()
        }
        responses = openmeteo.weather_api(url, params=params)

        response = responses[0]

        max_temperature_2m = response.Daily().Variables(0).ValuesAsNumpy()
        min_temperature_2m = response.Daily().Variables(1).ValuesAsNumpy()

        days_fcst = len(max_temperature_2m[~np.isnan(max_temperature_2m)])
        if days_fcst < num_days_to_endmonth:
            print(f"WARNING: Can't reach month end, using {days_fcst}")

        if cet_type=='max':
            cet_daily[:, i] = max_temperature_2m
        elif cet_type=='min':
            cet_daily[:, i] = min_temperature_2m
        else:
            cet_daily[:,i] = (max_temperature_2m + min_temperature_2m) / 2
         
    cet = np.mean(cet_daily, axis=1)
    cet = cet[~np.isnan(cet)]

    return cet, days_fcst