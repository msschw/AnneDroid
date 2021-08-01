import numpy as np
import pandas
import matplotlib.pyplot as plt
import urllib.request


class RKINowCasting:

    def __init__(self):
        self.filename = "Nowcast_R_aktuell.csv"
        self.url = "https://raw.githubusercontent.com/robert-koch-institut/SARS-CoV-2-Nowcasting_und_-R-Schaetzung/main/"+ self.filename
        urllib.request.urlretrieve(self.url, self.filename)

    def PlotR(self, path, daysBack = 0):
        columns = pandas.read_csv(self.filename)
        dates = pandas.to_datetime(columns['Datum'])

        lower_four_days_r = columns['UG_PI_7_Tage_R_Wert']
        upper_four_days_r = columns['OG_PI_7_Tage_R_Wert']
        four_days_r = columns['PS_7_Tage_R_Wert']

        x = dates

        y = four_days_r
        y_lower = lower_four_days_r
        y_upper = upper_four_days_r
        if daysBack > 0:
            x = dates[-daysBack:]

            y = four_days_r[-daysBack:]
            y_lower = lower_four_days_r[-daysBack:]
            y_upper = upper_four_days_r[-daysBack:]

        fig, ax = plt.subplots()
        plot = ax.plot_date(x, y, '-')
        ax.fill_between(x, y_lower, y_upper, alpha=0.2)
        fig.autofmt_xdate()
        fig.savefig(path)

    def PlotCases(self, path, daysBack = 0):
        columns = pandas.read_csv(self.filename)
        dates = pandas.to_datetime(columns['Datum'])

        lower_covid_cases = columns['UG_PI_COVID_Faelle']
        upper_covid_cases = columns['OG_PI_COVID_Faelle']
        covid_cases = columns['PS_COVID_Faelle']

        x = dates

        y = covid_cases
        y_lower = lower_covid_cases
        y_upper = upper_covid_cases
        if daysBack > 0:
            x = dates[-daysBack:]

            y = covid_cases[-daysBack:]
            y_lower = lower_covid_cases[-daysBack:]
            y_upper = upper_covid_cases[-daysBack:]

        fig, ax = plt.subplots()
        plot = ax.plot_date(x, y, '-')
        ax.fill_between(x, y_lower, y_upper, alpha=0.2)
        fig.autofmt_xdate()
        fig.savefig(path)
