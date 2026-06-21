from fetch_cet import cetDATA
from compute_cet import ComputeCET
from get_fcst_runtime import get_fcst_time
import numpy as np
from months import days_in_month
import matplotlib.pyplot as plt
import smplotlib

class ProcessCET():

    def __init__(self, month, models, cet_type, plot=False, use_prev=0, full_run=False):

        self.month = month
        self.models = models
        self.cet_type = cet_type
        self.use_prev = use_prev
        self.full_run = full_run

        self.plot = plot
        if self.plot:
            self.fig, self.ax = plt.subplots(figsize=(12, 8))


    def fetch_cet_data(self):

        cet_data = cetDATA()

        cet_data.fetch_data(self.month, self.cet_type)

        self.cet_in_flag = cet_data.cet_in_flag
        self.cet_vals = cet_data.cet_vals
        self.cet_days = cet_data.cet_days

    def nwp_cet_data(self):

        self.fetch_cet_data()

        self.nwp_cet = ComputeCET(self.cet_type, self.cet_in_flag, 
                                        self.use_prev, self.full_run)

        for group, model_array in self.models.items():
        
            for model in model_array:

                self.fetch_cet_data()
                runtime=get_fcst_time(model)
                
                self.nwp_cet.fetch_data(model, runtime)
                
                print(f"Fetched CET for month {self.month}. {self.cet_vals} for {self.cet_days} days.")
                print(f"Computed mean CET: {self.nwp_cet.cet}")

                
                model_runtime = self.nwp_cet.runtime

                # How many days in total do we (may not be number of days in the month)
                tot_days = self.cet_days + (self.nwp_cet.days_fcst - self.cet_days) + self.nwp_cet.day_of_start
                if tot_days < self.cet_days:
                    tot_days = self.cet_days
                
                days_ahead_of_cet = self.nwp_cet.days_fcst + self.nwp_cet.day_of_start - self.cet_days
                print(f"Total days of data: {tot_days}")
                print(f"Forecast days ahead of CET date: {days_ahead_of_cet}")
            
                assert tot_days <= days_in_month[self.month]['days'], (
                    f"total_days={tot_days} exceeds days in month "
                    f"({days_in_month[self.month]['days']})"
                )

                nwp_cet_filter = self.nwp_cet.cet

                if self.use_prev and self.cet_in_flag:
                    if days_ahead_of_cet > 0:
                        nwp_cet_filter = self.nwp_cet.cet[self.use_prev:]
                        self.fcst_start = self.cet_days + 1 - self.use_prev
                    else:
                        nwp_cet_filter = 0
                        self.fcst_start = self.cet_days + 1 - self.use_prev
                else:
                    nwp_cet_filter = self.nwp_cet.cet
                    self.fcst_start = self.cet_days+1

                # final CET computation, using current CET and fcst CET
                cet_vals = np.sum(self.cet_vals) + np.sum(nwp_cet_filter)
                cet_vals = cet_vals / tot_days

                print(f"Computed total CET {model}: {cet_vals}.")

                
                if self.plot:

                    dates_cet = np.linspace(1, self.cet_days, self.cet_days, endpoint=True)
                    dates_fcst = np.linspace(self.fcst_start, self.fcst_start + self.nwp_cet.days_fcst, self.nwp_cet.days_fcst, endpoint=True)


                    self.ax.plot(dates_fcst, self.nwp_cet.cet, label=f"{model}, cet: {cet_vals:.1f} C to {tot_days} ({model_runtime})")
                    self.ax.plot(dates_cet, self.cet_vals, color='black', linestyle='--')

        self.ax.set_title(f"June 2026 {self.cet_type} daily CET")
        self.ax.set_ylabel(f"Daily {self.cet_type} CET (C)")
        save_str = f'plots/test_{group}_{self.cet_type}.png'

        self.ax.set_xlabel("Day")
        self.ax.set_xlim(1, days_in_month[self.month]['days'])
        self.ax.set_xticks([1, 5, 10, 15, 20, 25, days_in_month[self.month]['days']])
        self.ax.grid(True, which="major", linestyle="--", linewidth=0.7, alpha=0.8)
        self.ax.legend()
        plt.savefig(save_str)
        

if __name__=="__main__":

    CET_TYPE = 'mean'

    MONTH = 'June'
    MODELS = {'EC': ["ecmwf_ifs", "ecmwf_ifs025", "ecmwf_aifs025_single"]}
    # MODELS = {'GFS': ["gfs_global", "ncep_aigfs025"]}
    # MODELS = {'MO': ["ukmo_global_deterministic_10km", "ukmo_uk_deterministic_2km"]}
    # MODELS = {'ICON': ["icon_global"]}

    # MODELS = ["ukmo_global_deterministic_10km", "ukmo_uk_deterministic_2km"]

    process_cet = ProcessCET(MONTH, MODELS, CET_TYPE, plot=True, use_prev=0, full_run=True)
    process_cet.nwp_cet_data()
    """
    TO DO: I would like to compute next month fcst CET too, but will need to separable out. Perhaps flag for either this month/next month
    where data allows?
    """