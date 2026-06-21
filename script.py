from fetch_cet import fetch_cet
from compute_cet import compute_cet
import numpy as np
from months import days_in_month
import matplotlib.pyplot as plt
import smplotlib


def cet_all(month, models, cet_type, plot=False):

    if len(models.keys()) > 1:
        ValueError("Please use one model")

    if plot:
        fig, ax = plt.subplots(figsize=(10, 6))

    for group, model_id in models.items():
       
        for model in model_id:

            acc_cet = fetch_cet(month, cet_type)
            cet_in_flag = acc_cet[2]
            fcst_cet = compute_cet(model, cet_type, cet_in_flag)
            print(f"Fetched CET for month {month}. {acc_cet[0]} for {acc_cet[1]} days.")
            print(f"Computed mean CET: {fcst_cet[0]}")

            total_days = acc_cet[1] + fcst_cet[1]
            print(f"Total days: {total_days}")
            cet_vals = np.sum(acc_cet[0]) + np.sum(fcst_cet[0])
            cet_vals = cet_vals / total_days

            print(f"Computed total CET: {cet_vals}.")

            dates_cet = np.linspace(1, len(acc_cet[0]), len(acc_cet[0]), endpoint=True)
            dates_fcst = np.linspace(len(acc_cet[0])+1, total_days, total_days-len(acc_cet[0]), endpoint=True)
                
            if plot:
        
                ax.plot(dates_fcst, fcst_cet[0], label=f"{model}, cet: {cet_vals:.1f} C")
                ax.plot(dates_cet, acc_cet[0], color='black', linestyle='--')


    ax.set_title(f"June 2026 {cet_type} daily CET")
    ax.set_ylabel(f"Daily {cet_type} CET (C)")
    save_str = f'plots/test_{group}_{cet_type}.png'

    ax.set_xlabel("Day")
    ax.set_xlim(1, days_in_month[month]['days'])
    ax.set_xticks([1, 5, 10, 15, 20, 25, days_in_month[month]['days']])
    ax.grid(True, which="major", linestyle="--", linewidth=0.7, alpha=0.8)
    ax.legend()
    plt.savefig(save_str)

if __name__=="__main__":

    CET_TYPE = 'mean'
    MONTH = 'June'
    MODELS = {'EC': ["ecmwf_ifs", "ecmwf_ifs025", "ecmwf_aifs025_single"]}
    # MODELS = {'GFS': ["gfs_global"]}
    # MODELS = {'ICON': ["icon_global"]}

    # MODELS = ["ukmo_global_deterministic_10km", "ukmo_uk_deterministic_2km"]

    cet_all(MONTH, MODELS, CET_TYPE, plot=True)