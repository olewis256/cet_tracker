import os
import urllib.request
import pandas as pd
import numpy as np
from months import days_in_month
from datetime import date, timedelta

src_str = "https://www.metoffice.gov.uk/hadobs/hadcet/data/"

def api_call(cet_str, out_path):
    """
    Docstring for api_call
    
    cet_str: specific CET file
    out_path: where to output the downloaded file
    """

    url_string = os.path.join(src_str, cet_str)
    
    with urllib.request.urlopen(url_string) as response, open(out_path, "wb") as f:
        data = response.read()  
        f.write(data)

def fetch_cet(month, cet_type):
    """
    Docstring for fetch_cet
    
    month: what month we are getting CET for
    cet_type: what kind of CET are we processing
    """

    cet_str = "cet_"+cet_type+"_2026.txt"
    out_path = os.path.join("tmp", cet_str)

    api_call(cet_str, out_path)

    # creating a dataframe and filtering out the placeholder -99.9 for this month
    df = pd.read_csv(out_path, skiprows=3, header=None, sep=r'\s+')
    vals = df.iloc[:, days_in_month[month]['num']].to_numpy()[1:]  
    vals = vals[vals != -99.9]
    num_days = len(vals)

    # flag in case CET for yesterday hasn't arrived yet
    cet_in_flag = False
    if num_days == (date.today() - timedelta(days=1)).day:
        cet_in_flag = True

    print(f"CET data in today: {cet_in_flag}")
    return vals, num_days, cet_in_flag