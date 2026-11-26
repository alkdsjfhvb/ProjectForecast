import yfinance as yf
import pandas_datareader.data as web
import pandas as pd
import datetime as  dt
from datetime import datetime, timedelta
import numpy as np
import matplotlib.pyplot as plt
from matplotlib import style

style.use('ggplot')
def forecast(ticker : str):
    end_date = datetime.today().strftime('%Y-%m-%d')
    start_date = (datetime.today() - timedelta(days=365)).strftime('%Y-%m-%d')
    prices = yf.download(ticker, start_date, end_date,['Close'])

    # pct change is used to determine with how many percent from the starting price has it risen
    # F.E starting = 80 ending = 100, how many percent is the change?
    # 80 + x%.80 = 100  do the math, and we get ->    x = (100-80/80)*100
    # formula for pct change = 100 * (P_new - P_old)/P_old
    # When pct_change is positive -> growth and vice versa when it's negative

    returns = prices.pct_change().dropna()
    daily_stdev = float(returns.std())
    last_price = float(prices.iloc[-1])

    # standard deviation shows how clustered all possible points are. The higher it is the worse it is for us because
    # stdev works this way: there is a mean value and the further we go from the center, the bigger the spread is
    # meaning the bigger the stdev the bigger the possibility is for the computer to choose an inaccurate value
    # therefore making the prediction of the price less reliable
    # its formula is calculating the means of the prices basically and gives a range for the computer to choose from.
    # number of simulations

    num_simulations = 800

    num_days = 100

    current_prices = np.full(num_simulations, last_price)  # row with 500 of the same last prices of the appl stock

    # creates a table for the end points assigned to each day: rows = Day 0..num_days, cols = simulations ( filled with zeros)
    price_paths = np.zeros((num_days + 1, num_simulations))
    price_paths[0] = current_prices  # the first day is always the last price of the appl stock

    # Store the median price at the end of each day (Day 0..252)
    median_at_each_day = np.zeros(
        num_days + 1)  # creates a premade list of 0 for all the days +1 reserved for the first day
    median_at_each_day[0] = np.median(current_prices)  # sets the first day to be the last price of the appl stock

    for day in range(num_days):  # does this for each of the days to return a table with end points for each of the days
        median_price = np.median(current_prices)  # gets the median end price for the day
        shocks = np.random.normal(0, daily_stdev, num_simulations)
        # chooses a random percentage for each simulation

        current_prices = median_price * (1 + shocks)  # returns a list of the upgraded current price for the day

        price_paths[day + 1] = current_prices  # puts the current price assigned for the enxt days
        median_at_each_day[day + 1] = np.median(
            current_prices)  # gets the median of prices for this specific day to use for the next days

    # ========= plotting =========

    plt.plot(median_at_each_day, color="black", linewidth=2, label="Daily median")
    plt.xlabel("Trading Days")
    plt.ylabel("Price ($)")
    plt.legend()
    plt.show()

    # so to summarize: standard deviation creates a "radius" of points filled with the percentage return.
    # Then, we set the starting price to be the last of the appl stock.
    # After that we create a new shock for each day, filling a 2d array with: rows =  number of days + 1 for the first reserved
    # cols = reserved zeroes to fill in later
    # For each day we update the median end price and set it to be the new current price for the next day


