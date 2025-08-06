import pandas as pd

# Centralized configuration for backtesting and analysis dates
START_DATE = pd.to_datetime('2000-01-01')
END_DATE = pd.to_datetime('2023-12-31')
#The percentage of the total portfolio to hold in cash. (e.g., 0.20 = 20%)
Percent_Cash_Portfolio = 0.80

# The annual risk-free return on the cash portion. (e.g., 0.03 = 3%)
Cash_Yearly_Rtn = 0.03

# Set to True to rebalance the portfolio annually back to the target cash percentage.
# Set to False to let the cash and invested portions grow independently.
Rebalance_Portfolio_Yearly = False
Use_Log_Plots_Portfolio = True
Use_Log_Plots_Equities = True