import numpy as np
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

class ComputeCET():

    def __init__(self, cet_type, cet_in_flag, use_prev, full_run):

        self.cet_type = cet_type
        self.cet_in_flag = cet_in_flag
        self.use_prev = use_prev
        self.full_run = full_run

    def compute_dates(self, runtime):

        if self.cet_in_flag and self.use_prev == 0:
            start_date = date.today()
            # Here, using full run means using the 00z run for today (since the 06z minimum is yet to occur)
            # If we use, later runs, the CET becomes biased. Also using today's 00z run, since yesterday's
            # CET data has arrived. 

            start_date = date.today()
            if runtime.endswith(("00:00")):
                pass
            else:
                print(f"Changing run {runtime} to 00:00 today, for consistency (06z has already passed)")
                runtime = datetime.strptime(runtime, "%Y-%m-%dT%H:%M").replace(hour=0, minute=0, 
                                                                        tzinfo=timezone.utc)
                runtime = runtime.strftime("%Y-%m-%dT%H:%M")


        if self.cet_in_flag is False:
            # If yesterday's CET isn't in yet, we want to use yesterday's forecast to fill the gap

            start_date = date.today() - timedelta(days=1)
            runtime = datetime.strptime(runtime, "%Y-%m-%dT%H:%M").replace(hour=12, minute=0, 
                                                                        tzinfo=timezone.utc) - timedelta(days=1)
            runtime = runtime.strftime("%Y-%m-%dT%H:%M")
            print(f"CET not populated, using start date {runtime}")

        if self.use_prev:
            # If using previous model runs to today

            start_date = date.today() - timedelta(days=self.use_prev)
            runtime = datetime.strptime(runtime, "%Y-%m-%dT%H:%M").replace(hour=12, minute=0,
                                                                        tzinfo=timezone.utc) - timedelta(days=self.use_prev)
            runtime = runtime.strftime("%Y-%m-%dT%H:%M")

        self.start_date = start_date
        self.runtime = runtime

        # get last day of month and the full date
        self.last_day = calendar.monthrange(start_date.year, start_date.month)[1]
        self.end_date = date(start_date.year, start_date.month, self.last_day)

        # how many days until the end of the month
        self.num_days_to_endmonth = (self.end_date - self.start_date).days + 1

        self.day_of_start = self.start_date.day-1
    
    def fetch_data(self, model, runtime):

        self.compute_dates(runtime)
        
        # empty arrays to store the CET data
        self.cet_daily = np.empty((self.num_days_to_endmonth, 3))
        self.cet = np.empty(self.num_days_to_endmonth)

        for i, site in enumerate(sites):
        
            print(f"Fetching data for site: {site} from {self.start_date} to {self.end_date} ({self.num_days_to_endmonth})")

            # API call to open-meteo to fetch NWP data

            params = {
                "latitude": sites[site]["latitude"],
                "longitude": sites[site]["longitude"],
                "daily": ["temperature_2m_max", "temperature_2m_min"],
                "models": model,
                "forecast_days": self.num_days_to_endmonth,
                "run": self.runtime
            }
            
            responses = openmeteo.weather_api(url, params=params)
            response = responses[0]

            max_temperature_2m = response.Daily().Variables(0).ValuesAsNumpy()
            min_temperature_2m = response.Daily().Variables(1).ValuesAsNumpy()

            # checking how many days we actually got NWP data for (not all models
            # have same leadtime). If not reaching end of month, adjust to fcst_days
            self.days_fcst = len(max_temperature_2m[~np.isnan(max_temperature_2m)])
            if self.days_fcst < self.num_days_to_endmonth:
                print(f"WARNING: Can't reach month end, using {self.days_fcst}")

            if self.cet_type=='max':
                self.cet_daily[:, i] = max_temperature_2m
            elif self.cet_type=='min':
                self.cet_daily[:, i] = min_temperature_2m
            else:
                self.cet_daily[:,i] = (max_temperature_2m + min_temperature_2m) / 2
        
        # computing mean across the three sites for each day
        self.cet = np.mean(self.cet_daily, axis=1)
        self.cet = self.cet[~np.isnan(self.cet)]

        print(f"Using start date {self.runtime} for model {model}")
        print(f"CET mean for fcst from {model}: {np.mean(self.cet)}")

        return self