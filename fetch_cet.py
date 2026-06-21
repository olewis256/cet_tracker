import os
import urllib.request
import pandas as pd
import numpy as np
from months import days_in_month

src_str = "https://www.metoffice.gov.uk/hadobs/hadcet/data/"

def api_call(cet_str, out_path):

    url_string = os.path.join(src_str, cet_str)
    

    with urllib.request.urlopen(url_string) as response, open(out_path, "wb") as f:
        data = response.read()  
        f.write(data)

def fetch_cet(month, cet_type, filter=True):

    cet_str = "cet_"+cet_type+"_2026.txt"
    out_path = os.path.join("tmp", cet_str)

    api_call(cet_str, out_path)

    df = pd.read_csv(out_path, skiprows=3, header=None, sep=r'\s+')
    vals = df.iloc[:, days_in_month[month]['num']].to_numpy()[1:]  
    vals = vals[vals != -99.9]
    num_days = len(vals)
    return vals, num_days
