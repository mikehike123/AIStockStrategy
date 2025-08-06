import os
import pandas as pd
import sys
import matplotlib.pyplot as plt

sys.path.append('..')
from custom_backtest_engine import (
    BacktestEngine,
    MovingAverageCrossoverStrategy,
    RsiMomentumStrategy,
    BreakoutStrategy,
    BreakoutVer2Strategy,
    TwoStdDevStrategy
)
from backtester import generate_summary_from_trades
# --- Import config variables, including the new flag ---
from config import START_DATE, END_DATE, Use_Log_Plots_Equities

# This list is now fully compatible with the modified engine
STRATEGIES = [
    ("Breakout_Simple", lambda: BreakoutStrategy(breakout_period=20, sl=0.95, tp=999999.9)),

    ("BreakoutV2_As_Simple", lambda: BreakoutVer2Strategy(
        use_trailing_stop=False,
        fixed_stop_perc=0.05,
        max_pyramids=1,
        entry_size_perc=1.0,
        pyramid_profit_perc=999,
        tp_long_perc=999999.9
    )),

    # Test Group 2: V2 with its trailing stop enabled
    ("BreakoutV2_TrailingStop", lambda: BreakoutVer2Strategy(
        use_trailing_stop=True,
        trailing_stop_perc=0.05,
        max_pyramids=1,
        entry_size_perc=1.0,
        pyramid_profit_perc=999,
        tp_long_perc=999
    )),

    # Test Group 3: V2 with all features enabled
    ("BreakoutV2_Full_Features", lambda: BreakoutVer2Strategy(
        use_trailing_stop=True,
        trailing_stop_perc=0.10,
        max_pyramids=5,
        entry_size_perc=0.20,
        pyramid_profit_perc=0.10,
        tp_long_perc=999
    )),
    ("BreakoutV2_25_NoStop_Pyramid", lambda: BreakoutVer2Strategy(
        use_trailing_stop=False,
        trailing_stop_perc=0.20,
        max_pyramids=4,
        entry_size_perc=0.25,
        pyramid_profit_perc=0.50,
        fixed_stop_perc=1.0,
        tp_long_perc=99999
    )),
    ("BreakoutV2_20_Trailingstop", lambda: BreakoutVer2Strategy(
        use_trailing_stop=True,
        trailing_stop_perc=0.20,
        max_pyramids=1,
        entry_size_perc=1.0,
        pyramid_profit_perc=0.10,
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
    ("TwoStdDev_MonthlyTrend_LowerBand_Trailing_pyramiding50g_4", lambda: TwoStdDevStrategy(
        buy_condition_option='SMA - Cross Above',
        use_trailing_stop=True,
        trailing_stop_perc=50.0,
        max_pyramids=4,
        entry_size_perc=0.25,
        tp_long_perc=10000,
        length=20
    )),
    ("TwoStdDev_YearlyTrend_SMABand_Trailing", lambda: TwoStdDevStrategy(
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
        pyramid_profit_perc=0.10,
        entry_size_perc=0.20,
        tp_long_perc=1.20
    )),
    ("TwoStdDev_SMA_Trailing_Pyramid_Hold_To_End", lambda: TwoStdDevStrategy(
        buy_condition_option='SMA - Cross Above',
        use_trailing_stop=True,
        trailing_stop_perc=0.50,
        max_pyramids=5,
        pyramid_profit_perc=0.20,
        entry_size_perc=0.20,
        tp_long_perc=10000
    )),

]

def plot_equity_curve(strategy_equity, buy_and_hold_equity, ticker, strat_name, strat_instance, plot_dir, initial_cash):
    """
    Generates and saves a plot of an individual equity curve against its Buy & Hold benchmark.
    """
    plt.style.use('seaborn-v0_8-darkgrid')
    fig, ax = plt.subplots(figsize=(15, 8))

    ax.plot(strategy_equity.index, strategy_equity.values, label=f'{strat_name} Equity', color='royalblue', linewidth=2, zorder=10)
    ax.plot(buy_and_hold_equity.index, buy_and_hold_equity.values, label='Buy & Hold Equity', color='gray', linestyle='-', linewidth=1.5, alpha=0.9, zorder=5)
    ax.axhline(y=initial_cash, color='red', linestyle='--', linewidth=1.5, label=f'Initial Capital (${initial_cash:,.0f})')

    if Use_Log_Plots_Equities:
        ax.set_yscale('log')
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        ax.set_ylabel('Equity ($) - Log Scale')
    else:
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        ax.set_ylabel('Equity ($)')

    fig.suptitle(f'Equity Curve for {ticker}', fontsize=16, fontweight='bold')
    
    # --- This is the corrected title logic ---
    # Make a copy of params to format for display without altering the original object
    params = strat_instance.__dict__.copy()

    # If long_stop_price exists and is a number, format it to two decimal places
    if 'long_stop_price' in params and isinstance(params['long_stop_price'], (int, float)):
        params['long_stop_price'] = f"{params['long_stop_price']:.2f}"
    
    param_list = [f'{k}={v}' for k, v in params.items() if not k.startswith('_')]

    subtitle = f"Strategy: {strat_name}"
    if param_list:
        midpoint = len(param_list) // 2 + (len(param_list) % 2)
        param_line1 = ', '.join(param_list[:midpoint])
        param_line2 = ', '.join(param_list[midpoint:])
        
        subtitle += f"\nParameters: {param_line1}"
        if param_line2:
            subtitle += f", {param_line2}"
            
    ax.set_title(subtitle, fontsize=10)
    # --- End of corrected logic ---

    ax.set_xlabel('Date', fontsize=12)
    ax.legend(loc='upper left')
    ax.minorticks_on()
    ax.grid(which='major', linestyle='-', linewidth='0.5', color='gray')
    ax.grid(which='minor', linestyle=':', linewidth='0.5', color='lightgray')
    
    safe_ticker = ticker.replace(" ", "_")
    plot_filename = os.path.join(plot_dir, f'{safe_ticker}.png')
    fig.tight_layout(rect=[0, 0.03, 1, 0.93])
    plt.savefig(plot_filename, dpi=150)
    plt.close(fig)

def run_backtest(strategy_class, data, cash=100000):
    strat = strategy_class()
    engine = BacktestEngine(data, strat, initial_cash=cash)
    trades, equity_curve = engine.run()
    trades = trades.rename(columns={'pnl': 'PnL', 'return_pct': 'ReturnPct', 'exit_reason': 'Tag'})
    return {'_trades': trades, '_equity_curve': equity_curve, '_strat_instance': strat}

def main():
    data_dir = os.path.join(os.path.dirname(__file__), '..', 'stockData')
    summary_results = {}
    trade_logs_path = os.path.join(os.path.dirname(__file__), 'trade_logs.txt')
    results_path = os.path.join(os.path.dirname(__file__), 'backtest_results.txt')

    base_plots_dir = os.path.join(os.path.dirname(__file__), 'plots', 'strategies_equities')
    os.makedirs(base_plots_dir, exist_ok=True)
    for strat_name, _ in STRATEGIES:
        strat_plot_dir = os.path.join(base_plots_dir, strat_name)
        os.makedirs(strat_plot_dir, exist_ok=True)
        
    initial_cash = 100000

    with open(trade_logs_path, 'w') as trade_log_file:
        for filename in os.listdir(data_dir):
            if filename.endswith('.csv'):
                ticker = filename.split('_')[0]
                data = pd.read_csv(f'{data_dir}/{filename}', index_col='Date', parse_dates=True)
                data.index = pd.to_datetime(data.index, utc=True).tz_localize(None)
                start_date = START_DATE
                end_date = END_DATE
                data = data[(data.index >= start_date) & (data.index <= end_date)]

                if data.empty:
                    print(f"Skipping {ticker} due to no data in the date range.")
                    continue
                buy_and_hold_equity = (initial_cash / data['Close'].iloc[0]) * data['Close']

                for strat_name, strat_class in STRATEGIES:
                    print(f"Running {strat_name} on {ticker}...")
                    stats = run_backtest(strat_class, data, cash=initial_cash)
                    key = f'{ticker}_{strat_name}'
                    trades = stats['_trades']
                    equity_curve_raw = stats['_equity_curve']
                    strat_instance = stats['_strat_instance']

                    strategy_equity = pd.Series(equity_curve_raw.values[1:], index=data.index)

                    strat_plot_dir = os.path.join(base_plots_dir, strat_name)
                    plot_equity_curve(
                        strategy_equity, 
                        buy_and_hold_equity, 
                        ticker, 
                        strat_name, 
                        strat_instance, 
                        strat_plot_dir, 
                        initial_cash
                    )
                    
                    trade_log_file.write(f'{key} TRADES:\n')
                    trade_log_file.write(trades.to_string(index=False))
                    trade_log_file.write('\n\n')
                    
                    summary = generate_summary_from_trades(trades, equity_curve_raw)
                    summary_results[key] = summary

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

    from report_generator import generate_report
    generate_report(results_path)

if __name__ == '__main__':
    main()