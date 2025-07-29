import os
import pandas as pd
import sys
sys.path.append('..')
from report_generator import generate_report
# Assuming your modified file is named custom_backtest_engine.py
from custom_backtest_engine import (
    BacktestEngine, 
    MovingAverageCrossoverStrategy, 
    RsiMomentumStrategy, 
    BreakoutStrategy,
    BreakoutVer2Strategy,
    TwoStdDevStrategy
)
from backtester import generate_summary_from_trades

# This list is now fully compatible with the modified engine
STRATEGIES = [
    ("Breakout_Simple", lambda: BreakoutStrategy(breakout_period=20, sl=0.95, tp=999999.9)),

    ("BreakoutV2_As_Simple", lambda: BreakoutVer2Strategy(
        use_trailing_stop=False,
        fixed_stop_perc=0.05,
        max_pyramids=1,
        entry_size_perc=1.0,
        pyramid_profit_perc=999,
        tp_long_perc=999999.9  # << NOW THIS PARAMETER WILL BE USED
    )),

    # Test Group 2: V2 with its trailing stop enabled
    ("BreakoutV2_TrailingStop", lambda: BreakoutVer2Strategy(
        use_trailing_stop=True,      # Use trailing stop
        trailing_stop_perc=0.05,     # 5% trailing stop
        max_pyramids=1,              # Pyramiding still off for a clean comparison
        entry_size_perc=1.0,         # Use 100% of equity
        pyramid_profit_perc=999,
        tp_long_perc=999
    )),
    
    # Test Group 3: V2 with all features enabled
    ("BreakoutV2_Full_Features", lambda: BreakoutVer2Strategy(
        use_trailing_stop=True,
        trailing_stop_perc=0.10,     # 10% trailing stop
        max_pyramids=5,              # Allow up to 5 entries
        entry_size_perc=0.20,        # Use 25% of equity per entry
        pyramid_profit_perc=0.10,    # Add to position if 5% in profit
        tp_long_perc=999
    )),
    ("BreakoutV2_20_Trailingstop", lambda: BreakoutVer2Strategy(
        use_trailing_stop=True,
        trailing_stop_perc=0.20,     # 20% trailing stop
        max_pyramids=5,              # Allow up to 5 entries
        entry_size_perc=0.20,        # Use 25% of equity per entry
        pyramid_profit_perc=0.10,    # Add to position if 5% in profit
        tp_long_perc=999
    )),
    
    # --- Two Standard Deviation Strategies ---
    ("TwoStdDev_MonthlyTrend_LowerBand_Trailing", lambda: TwoStdDevStrategy(
        buy_condition_option='Lower Band - Cross Above',
        use_trailing_stop=True,
        trailing_stop_perc=50.0,
        max_pyramids=0,
        entry_size_perc=1.0,
        tp_long_perc=10000,
        length=20
    )),
    ("TwoStdDev_YearlyTrend_LowerBand_Trailing", lambda: TwoStdDevStrategy(
        buy_condition_option='Lower Band - Cross Above',
        use_trailing_stop=True,
        trailing_stop_perc=50.0,
        max_pyramids=0,
        entry_size_perc=1.0,
        tp_long_perc=10000,
        length=260
    )),
    ("TwoStdDev_MonthlyTrend_LowerBand_Trailing", lambda: TwoStdDevStrategy(
        buy_condition_option='SMA - Cross Above',
        use_trailing_stop=True,
        trailing_stop_perc=50.0,
        max_pyramids=0,
        entry_size_perc=1.0,
        tp_long_perc=10000,
        length=20
    )),
    ("TwoStdDev_YearlyTrend_LowerBand_Trailing", lambda: TwoStdDevStrategy(
        buy_condition_option='SMA - Cross Above',
        use_trailing_stop=True,
        trailing_stop_perc=50.0,
        max_pyramids=0,
        entry_size_perc=1.0,
        tp_long_perc=10000,
        length=260
    )),
    ("TwoStdDev_MonthlyTrend_LowerBand_Trailing", lambda: TwoStdDevStrategy(
        buy_condition_option='SMA - Cross Above',
        use_trailing_stop=True,
        trailing_stop_perc=50.0,
        max_pyramids=0,
        entry_size_perc=1.0,
        tp_long_perc=10000,
        length=20
    )),
    ("TwoStdDev_UpperBand_Trailing", lambda: TwoStdDevStrategy(
        buy_condition_option='Upper Band - Cross Above',
        use_trailing_stop=True,
        trailing_stop_perc=1.0,
        max_pyramids=0,
        entry_size_perc=1.0,
        tp_long_perc=10000,
        length=260
    )),

    ("TwoStdDev_SMA_Trailing_Pyramid", lambda: TwoStdDevStrategy(
        buy_condition_option='SMA - Cross Above',
        use_trailing_stop=True,
        trailing_stop_perc=0.10,
        max_pyramids=5,
        pyramid_profit_perc=0.10, # <-- Add to position if 10% in profit
        entry_size_perc=0.20,
        tp_long_perc=1.20 # 20% TP
    )),
    ("TwoStdDev_SMA_Trailing_Pyramid_Hold_To_End", lambda: TwoStdDevStrategy(
        buy_condition_option='SMA - Cross Above',
        use_trailing_stop=True,
        trailing_stop_perc=0.50,
        max_pyramids=5,
        pyramid_profit_perc=0.20, # <-- Add to position if 10% in profit
        entry_size_perc=0.20,
        tp_long_perc=10000 
    )),
   
]


def run_backtest(strategy_class, data, cash=100000):
    strat = strategy_class()
    engine = BacktestEngine(data, strat, initial_cash=cash)
    trades, equity_curve = engine.run()
    # Rename columns for compatibility with reporting functions
    trades = trades.rename(columns={
        'pnl': 'PnL',
        'return_pct': 'ReturnPct',
        'exit_reason': 'Tag',
    })
    return {'_trades': trades, '_equity_curve': equity_curve}

def main():
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'stockData')
    summary_results = {}
    trade_logs_path = os.path.join(os.path.dirname(__file__), 'trade_logs.txt')
    results_path = os.path.join(os.path.dirname(__file__), 'backtest_results.txt')

    with open(trade_logs_path, 'w') as trade_log_file:
        for filename in os.listdir(data_dir):
            if filename.endswith('.csv'):
                ticker = filename.split('_')[0]
                data = pd.read_csv(f'{data_dir}/{filename}', index_col='Date', parse_dates=True)
                data.index = pd.to_datetime(data.index, utc=True).tz_localize(None)
                start_date = pd.to_datetime('2000-01-01')
                end_date = pd.to_datetime('2024-12-31')
                data = data[(data.index >= start_date) & (data.index <= end_date)]

                for strat_name, strat_class in STRATEGIES:
                    print(f"Running {strat_name} on {ticker}...")
                    stats = run_backtest(strat_class, data)
                    key = f'{ticker}_{strat_name}'
                    trades = stats['_trades']
                    equity_curve = stats['_equity_curve']
                    
                    trade_log_file.write(f'{key} TRADES:\n')
                    trade_log_file.write(trades.to_string(index=False))
                    trade_log_file.write('\n\n')
                    
                    summary = generate_summary_from_trades(trades, equity_curve)
                    summary_results[key] = summary

    # (The rest of your file for formatting and writing results is fine and needs no changes)
    def format_value(metric, value):
        if value == 'N/A': return value
        try:
            if metric == 'Equity Final [$]': return f'{float(value):.2f}'
            elif metric in ['Return [%]', 'Win Rate [%]', 'Best Trade [%]', 'Worst Trade [%]', 'Avg. Trade [%]']: return f'{float(value):.1f}'
            elif metric == 'Sharpe Ratio': return f'{float(value):.2f}'
            else: return value
        except: return value

    with open(results_path, 'w') as f:
        for key, summary in summary_results.items():
            f.write(f'{key}:\n')
            for metric, value in summary.items():
                f.write(f'{metric}: {format_value(metric, value)}\n')
            f.write('\n')

    summary_df = pd.DataFrame.from_dict({k: {m: format_value(m, v) for m, v in s.items()} for k, s in summary_results.items()}, orient='index')
    summary_df.index.name = 'Strategy'
    summary_csv_path = os.path.join(os.path.dirname(__file__), 'backtest_summary.csv')
    summary_df.to_csv(summary_csv_path)

    generate_report(results_path)

if __name__ == '__main__':
    main()