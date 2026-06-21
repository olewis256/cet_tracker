from fetch_cet import fetch_cet
from compute_cet import compute_cet
import numpy as np
from months import days_in_month

import matplotlib.pyplot as plt
import matplotlib.dates as mdates
from datetime import date

import smplotlib



def cet_all(month, models, cet_type, plot=False):

    if plot:
        fig, ax = plt.subplots(figsize=(10, 6))

    for model in models:

        acc_cet = fetch_cet(month, cet_type)
        fcst_cet = compute_cet(model, cet_type)
        print(f"Fetched CET for month {month}. {acc_cet[0]} for {acc_cet[1]} days.")
        print(f"Computed mean CET: {fcst_cet[0]}")

        total_days = acc_cet[1] + fcst_cet[1]
        print(f"Total days: {total_days}")
        cet_vals = np.sum(acc_cet[0]) + np.sum(fcst_cet[0])
        cet_vals = cet_vals / total_days

        print(f"Computed total CET: {cet_vals}.")

        if plot:
    
            dates_cet = np.linspace(1, len(acc_cet[0]), len(acc_cet[0]), endpoint=True)
            dates_fcst = np.linspace(len(acc_cet[0])+1, total_days, total_days-len(acc_cet[0]), endpoint=True)
            
            ax.plot(dates_fcst, fcst_cet[0], label=f"{model}, cet: {cet_vals:.1f} C")
            ax.plot(dates_cet, acc_cet[0], color='black', linestyle='--')
        

    if cet_type=='max':
        ax.set_title(f"June 2026 maximum daily CET")
        ax.set_ylabel("Daily maximum CET (C)")
        save_str = f'plots/test_max_{model}.png'
    elif cet_type=='min':
        ax.set_title(f"June 2026 minimum daily CET")
        ax.set_ylabel("Daily minimum CET (C)")
        save_str = f'plots/test_min_{model}.png'
    else:
        ax.set_title(f"June 2026 daily CET")
        ax.set_ylabel("Daily CET (C)")
        save_str = f'plots/test_mean_{model}.png'
    ax.set_xlabel("Day")
    ax.set_xlim(1, days_in_month[month])
    ax.set_xticks([1, 5, 10, 15, 20, 25, days_in_month[month]])
    ax.legend()
    plt.savefig(save_str)

if __name__=="__main__":

    CET_TYPE = 'max'
    MONTH = 'June'
    # MODELS = ["ecmwf_ifs", "ecmwf_ifs025", "ecmwf_aifs025_single"]
    MODELS = ["ukmo_global_deterministic_10km", "ukmo_uk_deterministic_2km"]

    cet_all(MONTH, MODELS, CET_TYPE, plot=True)