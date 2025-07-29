# This script performs a portfolio-level backtest analysis.
# It evaluates each strategy defined in `main.py` across all stock data files.
#
# How Different Date Spans Are Handled:
# 1.  Create a Universal Timeline: Before running any backtests, the script first
#     loops through every stock data file to create a single, "master" date index.
#     This master index contains every unique trading day from the earliest start
#     date to the latest end date across all files.
#
# 2.  Run Backtests Individually: The backtest for a given strategy is run on each
#     stock one by one. The result of each backtest is an equity curve that only
#     has dates corresponding to that specific stock's data.
#
# 3.  Align to the Universal Timeline: After generating an equity curve for a single
#     stock, it is re-indexed to align with the master timeline from Step 1. This
#     expands the individual equity curve so that it has a value for every single
#     day in the universal timeline.
#
# 4.  Fill in the Gaps (Forward-Filling): Re-indexing creates gaps (NaN values) for
#     dates where a specific stock didn't have data. These are handled by "forward-filling":
#     - Before a stock's first trading day, its value is held constant at its
#       initial allocated capital.
#     - If a stock stops trading before others, its last known equity value is
#       carried forward to the end of the analysis period.
#
# 5.  Sum the Aligned Curves: Once every stock's equity curve is aligned to the same
#     universal timeline, the script sums the equity values for each day across all
#     stocks. This produces the total portfolio value for every day of the entire
#     period, allowing for an accurate final return calculation.

import os
import pandas as pd
import sys
from datetime import date

# Add the project root to the Python path to allow for absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from swing_trading_strategies.custom_backtest_engine import BacktestEngine
from swing_trading_strategies.main import STRATEGIES

def run_portfolio_analysis(initial_capital=100000):
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    data_dir = os.path.join(project_root, 'stockData')
    stock_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
    stock_symbols = [f.split('_')[0] for f in stock_files]
    num_stocks = len(stock_files)
    capital_per_stock = initial_capital / num_stocks

    portfolio_results = {}

    # Determine a common date index from all datasets first
    common_index = None
    all_stock_data = {}
    for filename in stock_files:
        data = pd.read_csv(os.path.join(data_dir, filename), index_col='Date', parse_dates=True)
        data.index = pd.to_datetime(data.index, utc=True).tz_localize(None)
        start_date = pd.to_datetime('2000-01-01')
        end_date = pd.to_datetime('2024-12-31')
        data = data[(data.index >= start_date) & (data.index <= end_date)]
        all_stock_data[filename] = data
        if common_index is None:
            common_index = data.index
        else:
            common_index = common_index.union(data.index)

    analysis_start_date = common_index.min().strftime('%Y-%m-%d')
    analysis_end_date = common_index.max().strftime('%Y-%m-%d')

    # --- Buy and Hold Calculation ---
    buy_and_hold_curves = []
    for filename, data in all_stock_data.items():
        initial_price = data['Close'].iloc[0]
        shares = capital_per_stock / initial_price
        equity_curve = shares * data['Close']
        reindexed_curve = equity_curve.reindex(common_index, method='ffill').fillna(capital_per_stock)
        buy_and_hold_curves.append(reindexed_curve)
    
    if buy_and_hold_curves:
        portfolio_equity = pd.concat(buy_and_hold_curves, axis=1).sum(axis=1)
        initial_portfolio_value = portfolio_equity.iloc[0]
        final_portfolio_value = portfolio_equity.iloc[-1]
        portfolio_return_pct = (final_portfolio_value - initial_portfolio_value) / initial_portfolio_value * 100
        running_max = portfolio_equity.cummax()
        drawdown = (portfolio_equity - running_max) / running_max
        max_drawdown_pct = drawdown.min() * 100

        portfolio_results['Buy and Hold'] = {
            'Final Portfolio Value [$]': final_portfolio_value,
            'Portfolio Return [%]': portfolio_return_pct,
            'Max Drawdown [%]': max_drawdown_pct
        }

    for strat_name, strat_class_lambda in STRATEGIES:
        print(f"Analyzing portfolio for strategy: {strat_name}...")
        all_equity_curves = []

        for filename, data in all_stock_data.items():
            strategy_instance = strat_class_lambda()
            engine = BacktestEngine(data, strategy_instance, initial_cash=capital_per_stock)
            _, equity_curve_raw = engine.run()

            # Align the equity curve (N+1 points) with the data index (N points)
            equity_curve = pd.Series(equity_curve_raw.values[1:], index=data.index)

            # Reindex the equity curve to the common index
            reindexed_curve = equity_curve.reindex(common_index, method='ffill').fillna(capital_per_stock)
            all_equity_curves.append(reindexed_curve)

        # Combine equity curves
        if all_equity_curves:
            portfolio_equity = pd.concat(all_equity_curves, axis=1).sum(axis=1)
            
            # --- CALCULATE METRICS ---
            initial_portfolio_value = portfolio_equity.iloc[0]
            final_portfolio_value = portfolio_equity.iloc[-1]
            portfolio_return_pct = (final_portfolio_value - initial_portfolio_value) / initial_portfolio_value * 100

            # Calculate Max Drawdown
            running_max = portfolio_equity.cummax()
            drawdown = (portfolio_equity - running_max) / running_max
            max_drawdown_pct = drawdown.min() * 100

            portfolio_results[strat_name] = {
                'Final Portfolio Value [$]': final_portfolio_value,
                'Portfolio Return [%]': portfolio_return_pct,
                'Max Drawdown [%]': max_drawdown_pct
            }
        else:
            portfolio_results[strat_name] = {
                'Final Portfolio Value [$]': 0,
                'Portfolio Return [%]': 0,
                'Max Drawdown [%]': 0
            }

    # --- Generate and Save Report ---
    print("\n--- Portfolio Analysis Results ---")
    results_df = pd.DataFrame.from_dict(portfolio_results, orient='index')
    # Custom sort: Buy and Hold first, then by return
    if 'Buy and Hold' in results_df.index:
        buy_and_hold_row = results_df.loc[['Buy and Hold']]
        other_strategies = results_df.drop('Buy and Hold').sort_values(by='Portfolio Return [%]', ascending=False)
        results_df = pd.concat([buy_and_hold_row, other_strategies])
    else:
        results_df = results_df.sort_values(by='Portfolio Return [%]', ascending=False)

    report_content = results_df.to_markdown()

    # Print to console
    print(report_content)

    # Save to file
    report_path = os.path.join(os.path.dirname(__file__), 'portfolio_report.md')
    today_str = date.today().strftime('%Y-%m-%d')

    with open(report_path, 'w') as f:
        f.write("# Portfolio Analysis Report\n\n")
        f.write(f"**Analysis Date:** {today_str}\n\n")
        f.write(f"**Data Span:** {analysis_start_date} to {analysis_end_date}\n\n")
        f.write(f"**Portfolio Stocks:** {', '.join(stock_symbols)}\n\n")
        f.write("This report shows the performance of each strategy when applied across the entire portfolio of stocks.\n\n")
        f.write(report_content)
    print(f"\nReport saved to {report_path}")


if __name__ == '__main__':
    run_portfolio_analysis()
