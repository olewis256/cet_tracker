from fetch_cet import cetDATA
from compute_cet import ComputeCET
from get_fcst_runtime import get_fcst_time
import numpy as np
from months import days_in_month
import matplotlib.pyplot as plt
import smplotlib

class ProcessCET():
    """
    Main script for processing both observed and forecast CET data.

    fetch_cet_data: Collects observed CET data, with flag to whether yesterday's CET data has
                    arrived yet.
    nwp_cet_data:   Collects and processes the forecasted CET data, while also splitting up
                    the dates to ensure the predicted CET is a blend of observed and forecasted
                    values (sometimes messy when using previous runs and there is significant
                    overlap). Optional tools for plotting.
    """

    def __init__(self, 
                 month, 
                 models, 
                 cet_type, 
                 plot=False, 
                 use_prev=0, 
                 full_run=True,
                 next_month=False
                 ):

        self.month = month
        self.models = models
        self.cet_type = cet_type
        self.use_prev = use_prev
        self.full_run = full_run
        self.next_month = next_month
        self.fcst_start = 0

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

        if self.next_month:

            self.cet_in_flag = False
        
        else:
            
            self.fetch_cet_data()

            print(f"Fetched CET for month {self.month}. {self.cet_vals} for {self.cet_days} days.")

        self.nwp_cet = ComputeCET(self.cet_type, 
                                  self.cet_in_flag, 
                                  self.use_prev, 
                                  self.full_run,
                                  self.next_month
                                  )
        
        save_str = f"plots/test_{self.month}_{self.cet_type}"

        self.fig, self.ax = plt.subplots(figsize=(12, 8))

        for group, model_array in self.models.items():
        
            for model in model_array:

                runtime=get_fcst_time(model)
                
                self.nwp_cet.fetch_data(model, runtime)
                
                print(f"Computed mean CET: {self.nwp_cet.cet}")

                model_runtime = self.nwp_cet.runtime

                # How many days in total do we (may not be number of days in the month)
                if self.next_month:
                    tot_days = self.nwp_cet.days_fcst + self.nwp_cet.day_of_start
                else:
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
                    elif days_ahead_of_cet < 0 and not self.use_prev:
                        # if no NWP data is ahead of CET data, we don't 
                        # use it in final prediction
                        nwp_cet_filter = 0
                        self.fcst_start = self.cet_days + 1 - self.use_prev
                    elif days_ahead_of_cet <= 0 and self.use_prev:
                        cet_filter = self.cet_vals[0:self.nwp_cet.day_of_start]
                        print("CET filter: ", cet_filter)
                        tot_days = len(cet_filter) + self.nwp_cet.days_fcst
                        nwp_cet_filter = self.nwp_cet.cet
                        print("NWP CET filter: ", nwp_cet_filter)
                        self.fcst_start = self.nwp_cet.day_of_start+1
                        print("total days: ", tot_days)
                elif self.next_month:
                    nwp_cet_filter = self.nwp_cet.cet
                    self.fcst_start = self.nwp_cet.day_of_start+1
                else:
                    nwp_cet_filter = self.nwp_cet.cet
                    self.fcst_start = self.cet_days+1

                # final CET computation, using current CET and fcst CET
                if self.next_month:
                    cet_vals_all = np.sum(nwp_cet_filter)
                elif self.use_prev and days_ahead_of_cet <= 0:
                    cet_vals_all = np.sum(cet_filter) + np.sum(nwp_cet_filter)
                else:
                    print(f"Current rolling CET: {np.sum(self.cet_vals)/self.cet_days}")
                    cet_vals_all = np.sum(self.cet_vals) + np.sum(nwp_cet_filter)
                cet_vals_all = cet_vals_all / tot_days

                
                print(f"Computed total CET {model}: {cet_vals_all}.")

                
                if self.plot:

                    dates_fcst = np.linspace(self.fcst_start, self.fcst_start + self.nwp_cet.days_fcst - 1, self.nwp_cet.days_fcst, endpoint=True)
                    print(dates_fcst)
                    self.ax.plot(dates_fcst, self.nwp_cet.cet, label=f"{model}, cet: {cet_vals_all:.1f} C to {tot_days} ({model_runtime})")
                    
            save_str += f"_{group}"

        if self.plot:

            self.ax.set_title(f"{self.month} 2026 {self.cet_type} daily CET")
            self.ax.set_ylabel(f"Daily {self.cet_type} CET (C)")
            save_str += "_15step.png"

            if not self.next_month:
                dates_cet = np.linspace(1, self.cet_days, self.cet_days, endpoint=True)
                self.ax.plot(dates_cet, self.cet_vals, color='black', linestyle='--', label=f'rolling cet: {np.sum(self.cet_vals)/self.cet_days:.1f} C')

            self.ax.set_xlabel("Day")
            self.ax.set_xlim(1, days_in_month[self.month]['days'])
            self.ax.set_xticks([1, 5, 10, 15, 20, 25, days_in_month[self.month]['days']])
            self.ax.grid(True, which="major", linestyle="--", linewidth=0.7, alpha=0.8)
            self.ax.legend()
            plt.savefig(save_str)
        

if __name__=="__main__":
    """
    Script to run to create predicted CETs:

    CET_TYPE: 'max', 'min', 'mean'
    MODELS: (TO DO, create separate class)
    plot: boolean, plot or not
    use_prev: how many days ago to use run (default 0 days)
    full_run: now defunct, was using with issues with smaller lead time 06/18z runs
    """

    CET_TYPE = 'mean'

    MONTH = 'June'
    MODELS = {'EC': ["ecmwf_aifs025_single"]}
    # MODELS = {'GFS': ["gfs_global", "ncep_aigfs025"]}
    # MODELS = {'MO': ["ukmo_global_deterministic_10km", "ukmo_uk_deterministic_2km"]}
    # MODELS = {'ICON': ["icon_global"]}

    # MODELS = ["ukmo_global_deterministic_10km", "ukmo_uk_deterministic_2km"]

    process_cet = ProcessCET(MONTH, MODELS, CET_TYPE, plot=True, use_prev=15, full_run=True)
    # process_cet = ProcessCET(MONTH, MODELS, CET_TYPE, next_month=True, plot=True)
    process_cet.nwp_cet_data()
    """
    TO DO: I would like to compute next month fcst CET too, but will need to separable out. Perhaps flag for either this month/next month
    where data allows?
    """