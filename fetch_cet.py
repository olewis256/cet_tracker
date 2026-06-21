import os
import urllib.request
import pandas as pd
import numpy as np

MONTH = 6

src_str = "https://www.metoffice.gov.uk/hadobs/hadcet/data/"



def api_call(cet_str, out_path):

    url_string = os.path.join(src_str, cet_str)
    

    with urllib.request.urlopen(url_string) as response, open(out_path, "wb") as f:
        data = response.read()  
        f.write(data)

def fetch_cet(month, cet_type, filter=True):


    if cet_type == 'max':
        cet_str =  "cet_max_2026.txt"
        out_path = "tmp/cet_max_2026.txt"
    elif cet_type == 'min':
        cet_str = "cet_min_2026.txt"
        out_path = "tmp/cet_min_2026.txt"
    else:
        cet_str = "cet_mean_2026.txt"
        out_path = "tmp/cet_mean_2026.txt"

    api_call(cet_str, out_path)

    df = pd.read_csv(out_path, skiprows=3, header=None, sep=r'\s+')
    vals = df.iloc[:, MONTH].to_numpy()[1:]  
    vals = vals[vals != -99.9]
    num_days = len(vals)
    return vals, num_days
