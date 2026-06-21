from fetch_cet import fetch_cet
from compute_cet import compute_cet
import numpy as np
from months import days_in_month
import matplotlib.pyplot as plt
import smplotlib


def cet_all(month, models, cet_type, plot=False):
    """
    Docstring for cet_all
    
    month: month we are computing CET for
    models: which models we are computing fcst CET for
    cet_type: type of CET we are computing
    plot: do we want to plot the data
    """

    # TO DO: Having too many models on one plot is messy, so just limiting to one subset e.g. EC models
    if len(models.keys()) > 1:
        ValueError("Please use one model")

    if plot:
        fig, ax = plt.subplots(figsize=(10, 6))

    # group would be EC, and model_array is the subset of models available from EC
    for group, model_array in models.items():
        
        for model in model_array:

            # fetching this month's CET, and whether we have yesterday's data
            acc_cet = fetch_cet(month, cet_type)
            cet_in_flag = acc_cet[2]

            # fetchig and computing fcst CET, to month end (if available)
            fcst_cet = compute_cet(model, cet_type, cet_in_flag)
            print(f"Fetched CET for month {month}. {acc_cet[0]} for {acc_cet[1]} days.")
            print(f"Computed mean CET: {fcst_cet[0]}")

            # How many days in total do we (may not be number of days in the month)
            total_days = acc_cet[1] + fcst_cet[1]
            print(f"Total days: {total_days}")

            # final CET computation, using current CET and fcst CET
            cet_vals = np.sum(acc_cet[0]) + np.sum(fcst_cet[0])
            cet_vals = cet_vals / total_days

            print(f"Computed total CET: {cet_vals}.")

            # constructing date arrays for plot
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

    """
    TO DO: I would like to compute next month fcst CET too, but will need to separable out. Perhaps flag for either this month/next month
    where data allows?
    """