import os
import urllib.request
import pandas as pd
import numpy as np
from months import days_in_month
from datetime import date, timedelta

src_str = "https://www.metoffice.gov.uk/hadobs/hadcet/data/"


class cetDATA:

    cet_vals: pd.DataFrame
    cet_days: int
    cet_in_flag: bool

    def api_call(self, cet_str, out_path):
    
        url_str = os.path.join(src_str, cet_str)
        
        with urllib.request.urlopen(url_str) as response, open(out_path, "wb") as f:
            data = response.read()  
            f.write(data)

    def fetch_data(self, month, cet_type):

        cet_str = "cet_"+cet_type+"_2026.txt"
        out_path = os.path.join("tmp", cet_str)

        self.api_call(cet_str, out_path)

        # creating a dataframe and filtering out the placeholder -99.9 for this month
        df = pd.read_csv(out_path, skiprows=3, header=None, sep=r'\s+')
        vals = df.iloc[:, days_in_month[month]['num']].to_numpy()[1:]  
        vals = vals[vals != -99.9]
        num_days = len(vals)

        # flag in case CET for yesterday hasn't arrived yet
        cet_in_flag = False
        if num_days == (date.today() - timedelta(days=1)).day:
            cet_in_flag = True

        self.cet_vals = vals
        self.cet_days = num_days
        self.cet_in_flag = cet_in_flag

        print(f"CET data in today: {cet_in_flag}")

        return self