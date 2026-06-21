import numpy as np
from openmeteo_sdk.Variable import Variable
import openmeteo_requests
import matplotlib.pyplot as plt
from datetime import date, timedelta, datetime, timezone
import calendar

# sites used in the CET caclulation
sites = {
    "stonyhurst": {"latitude": 53.85, "longitude": -1.53},
    "rothamsted": {"latitude": 51.81, "longitude": -0.36},
    "pershore": {"latitude": 52.15, "longitude": -2.04}
}

openmeteo = openmeteo_requests.Client()
url = "https://single-runs-api.open-meteo.com/v1/forecast"

def compute_cet(model, cet_type, cet_in_flag, runtime, use_prev, full_run):
    """
    Computing the CET from NWP fcst data
    
    model: NWP model to use
    cet_type: what type of CET are we computing
    cet_in_flag: flag to check if yesterday's CET data has arrived
    """ 

    # if yesertday's CET is in, use today's date
    if cet_in_flag:
        start_date = date.today()
        # 06 and 18z runs aren't full runs, so use previous 00z or 12z runs
        if full_run:
            if runtime.endswith(("06:00")):
                print(f"Changing run {runtime} to 00:00")
                runtime = datetime.strptime(runtime, "%Y-%m-%dT%H:%M").replace(hour=0, minute=0, 
                                                                        tzinfo=timezone.utc)
                runtime = runtime.strftime("%Y-%m-%dT%H:%M")
            elif runtime.endswith(("18:00")):
                print(f"Changing run {runtime} to 12:00")
                runtime = datetime.strptime(runtime, "%Y-%m-%dT%H:%M").replace(hour=12, minute=0, 
                                                                        tzinfo=timezone.utc)
                runtime = runtime.strftime("%Y-%m-%dT%H:%M")

    else:
        # if yesterday's CET isn't in yet, use yesterday's forecast
        start_date = date.today() - timedelta(days=1)
        runtime = datetime.strptime(runtime, "%Y-%m-%dT%H:%M").replace(hour=12, minute=0, 
                                                                       tzinfo=timezone.utc) - timedelta(days=1)
        runtime = runtime.strftime("%Y-%m-%dT%H:%M")
        print(f"CET not populated, using start date {runtime}")

    if use_prev:
        # use previous days 12z model runs
        start_date = date.today() - timedelta(days=use_prev)
        runtime = datetime.strptime(runtime, "%Y-%m-%dT%H:%M").replace(hour=12, minute=0,
                                                                       tzinfo=timezone.utc) - timedelta(days=use_prev)
        runtime = runtime.strftime("%Y-%m-%dT%H:%M")

    last_day = calendar.monthrange(start_date.year, start_date.month)[1]
    end_date = date(start_date.year, start_date.month, last_day)

    # determinging how many days there are until the end of the month,
    # then creating empty arrays to hold data
    num_days_to_endmonth = (end_date - start_date).days + 1
    cet_daily = np.empty((num_days_to_endmonth, 3))
    cet = np.empty(num_days_to_endmonth)

    for i, site in enumerate(sites):
        
        print(f"Fetching data for site: {site} from {start_date} to {end_date} ({num_days_to_endmonth})")

        # API call to open-meteo to fetch NWP data

        params = {
            "latitude": sites[site]["latitude"],
            "longitude": sites[site]["longitude"],
            "daily": ["temperature_2m_max", "temperature_2m_min"],
            "models": model,
            "forecast_days": num_days_to_endmonth,
            "run": runtime
        }
        
        responses = openmeteo.weather_api(url, params=params)
        response = responses[0]

        max_temperature_2m = response.Daily().Variables(0).ValuesAsNumpy()
        min_temperature_2m = response.Daily().Variables(1).ValuesAsNumpy()

        # checking how many days we actually got NWP data for (not all models
        # have same leadtime). If not reaching end of month, adjust to fcst_days
        days_fcst = len(max_temperature_2m[~np.isnan(max_temperature_2m)])
        if days_fcst < num_days_to_endmonth:
            print(f"WARNING: Can't reach month end, using {days_fcst}")

        if cet_type=='max':
            cet_daily[:, i] = max_temperature_2m
        elif cet_type=='min':
            cet_daily[:, i] = min_temperature_2m
        else:
            cet_daily[:,i] = (max_temperature_2m + min_temperature_2m) / 2
    
    # computing mean across the three sites for each day
    cet = np.mean(cet_daily, axis=1)
    cet = cet[~np.isnan(cet)]

    print(f"Using start date {runtime} for model {model}")
    print(f"CET mean for fcst from {model}: {np.mean(cet)}")

    return cet, days_fcst, runtime, start_date.day-1