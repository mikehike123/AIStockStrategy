import os
import pandas as pd
import sys
from datetime import date
import matplotlib.pyplot as plt

# Add the project root to the Python path to allow for absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- Import the new flags from your config file ---
from swing_trading_strategies.config import (
    START_DATE, END_DATE, Use_Log_Plots_Portfolio,
    Percent_Cash_Portfolio, Cash_Yearly_Rtn, Rebalance_Portfolio_Yearly
)
from swing_trading_strategies.custom_backtest_engine import BacktestEngine
from swing_trading_strategies.main import STRATEGIES

def plot_portfolio_equity(portfolio_equity, strat_name, strat_params, plots_dir, initial_capital, buy_and_hold_equity=None, pure_buy_and_hold_equity=None):
    """
    Generates and saves a plot of the portfolio equity curve.
    Includes the Buy and Hold curve (with cash allocation) and a 100% Equity B&H curve.
    """
    plt.style.use('seaborn-v0_8-darkgrid')
    fig, ax = plt.subplots(figsize=(15, 8))

    ax.plot(portfolio_equity.index, portfolio_equity.values, label=f'{strat_name} Equity', color='royalblue', linewidth=2, zorder=10)

    if buy_and_hold_equity is not None:
        label = f'B&H with {Percent_Cash_Portfolio:.0%} Cash'
        ax.plot(buy_and_hold_equity.index, buy_and_hold_equity.values, label=label, color='gray', linestyle='-', linewidth=1.5, alpha=0.9, zorder=5)

    if pure_buy_and_hold_equity is not None:
        ax.plot(pure_buy_and_hold_equity.index, pure_buy_and_hold_equity.values, label='100% Equity B&H', color='darkorange', linestyle=':', linewidth=1.5, zorder=7)

    ax.axhline(y=initial_capital, color='red', linestyle='--', linewidth=1.5, label=f'Initial Capital (${initial_capital:,.0f})')

    if Use_Log_Plots_Portfolio:
        ax.set_yscale('log')
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        ax.set_ylabel('Portfolio Value ($) - Log Scale')
    else:
        ax.yaxis.set_major_formatter(plt.FuncFormatter(lambda x, p: f'${x:,.0f}'))
        ax.set_ylabel('Portfolio Value ($)')

    fig.suptitle(f'Portfolio Equity: {strat_name}', fontsize=16, fontweight='bold')
    
    param_list = [f'{k}={v}' for k, v in strat_params.items() if not k.startswith('_')]
    if param_list:
        midpoint = len(param_list) // 2 + (len(param_list) % 2)
        line1 = ', '.join(param_list[:midpoint])
        line2 = ', '.join(param_list[midpoint:])
        param_str = f"Parameters: {line1}"
        if line2:
            param_str += f"\n{line2}"
        ax.set_title(param_str, fontsize=10)

    ax.set_xlabel('Date', fontsize=12)
    ax.legend(loc='upper left')
    ax.minorticks_on()
    ax.grid(which='major', linestyle='-', linewidth='0.5', color='gray')
    ax.grid(which='minor', linestyle=':', linewidth='0.5', color='lightgray')
    
    safe_strat_name = strat_name.replace(" ", "_").replace("/", "_")
    plot_filename = os.path.join(plots_dir, f'portfolio_{safe_strat_name}.png')
    
    fig.tight_layout(rect=[0, 0.03, 1, 0.95])
    
    plt.savefig(plot_filename, dpi=150)
    plt.close(fig)
    print(f"Saved plot for {strat_name} to {plot_filename}")


def run_rebalancing_simulation(invested_equity_curve, initial_invested, initial_cash, daily_cash_return):
    """
    Performs a day-by-day simulation of a portfolio with annual rebalancing.
    """
    invested_returns = invested_equity_curve.pct_change().fillna(0)
    
    sim = pd.DataFrame(index=invested_equity_curve.index)
    sim['invested'] = 0.0
    sim['cash'] = 0.0
    sim.loc[sim.index[0], ['invested', 'cash']] = [initial_invested, initial_cash]

    prev_year = sim.index[0].year

    for i in range(1, len(sim)):
        current_index = sim.index[i]
        prev_index = sim.index[i-1]
        
        current_year = current_index.year
        if current_year != prev_year:
            total_value = sim.loc[prev_index, 'invested'] + sim.loc[prev_index, 'cash']
            sim.loc[current_index, 'invested'] = total_value * (1 - Percent_Cash_Portfolio)
            sim.loc[current_index, 'cash'] = total_value * Percent_Cash_Portfolio
        else:
            sim.loc[current_index, 'invested'] = sim.loc[prev_index, 'invested'] * (1 + invested_returns.iloc[i])
            sim.loc[current_index, 'cash'] = sim.loc[prev_index, 'cash'] * (1 + daily_cash_return)
        
        prev_year = current_year

    sim['total'] = sim['invested'] + sim['cash']
    return sim['total']


def run_portfolio_analysis(initial_capital=100000):
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    data_dir = os.path.join(project_root, 'stockData')
    
    plots_dir = os.path.join(os.path.dirname(__file__), 'plots', 'portfolios')
    os.makedirs(plots_dir, exist_ok=True)
    
    stock_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
    stock_symbols = [f.split('_')[0] for f in stock_files]
    num_stocks = len(stock_files)
    
    invested_capital = initial_capital * (1 - Percent_Cash_Portfolio)
    initial_cash_position = initial_capital * Percent_Cash_Portfolio
    capital_per_stock = invested_capital / num_stocks if num_stocks > 0 else 0

    portfolio_results = {}

    common_index = None
    all_stock_data = {}
    for filename in stock_files:
        data = pd.read_csv(os.path.join(data_dir, filename), index_col='Date', parse_dates=True)
        data.index = pd.to_datetime(data.index, utc=True).tz_localize(None)
        start_date = START_DATE
        end_date = END_DATE
        data = data[(data.index >= start_date) & (data.index <= end_date)]
        all_stock_data[filename] = data
        if common_index is None:
            common_index = data.index
        else:
            common_index = common_index.union(data.index)

    analysis_start_date = common_index.min().strftime('%Y-%m-%d')
    analysis_end_date = common_index.max().strftime('%Y-%m-%d')
    
    num_years = (common_index.max() - common_index.min()).days / 365.25
    
    daily_cash_return = (1 + Cash_Yearly_Rtn)**(1/252) - 1

    pure_buy_and_hold_equity = None
    if num_stocks > 0:
        pure_capital_per_stock = initial_capital / num_stocks
        pure_buy_and_hold_curves = []
        for filename, data in all_stock_data.items():
            if data.empty: continue
            initial_price = data['Close'].iloc[0]
            shares = pure_capital_per_stock / initial_price
            equity_curve = shares * data['Close']
            reindexed_curve = equity_curve.reindex(common_index, method='ffill').fillna(pure_capital_per_stock)
            pure_buy_and_hold_curves.append(reindexed_curve)
        if pure_buy_and_hold_curves:
            pure_buy_and_hold_equity = pd.concat(pure_buy_and_hold_curves, axis=1).sum(axis=1)

            final_val = pure_buy_and_hold_equity.iloc[-1]
            cagr = ((final_val / initial_capital)**(1/num_years) - 1) * 100
            running_max = pure_buy_and_hold_equity.cummax()
            drawdown = (pure_buy_and_hold_equity - running_max) / running_max
            max_dd = drawdown.min() * 100
            portfolio_results['100% Equity B&H'] = {
                'Final Portfolio Value [$]': final_val,
                'CAGR [%]': cagr,
                'Max Drawdown [%]': max_dd
            }

    buy_and_hold_portfolio_equity = None
    if num_stocks > 0:
        buy_and_hold_curves = []
        for filename, data in all_stock_data.items():
            if data.empty: continue
            initial_price = data['Close'].iloc[0]
            shares = capital_per_stock / initial_price
            equity_curve = shares * data['Close']
            reindexed_curve = equity_curve.reindex(common_index, method='ffill').fillna(capital_per_stock)
            buy_and_hold_curves.append(reindexed_curve)
        
        if buy_and_hold_curves:
            buy_and_hold_invested_equity = pd.concat(buy_and_hold_curves, axis=1).sum(axis=1)
            
            if Rebalance_Portfolio_Yearly and Percent_Cash_Portfolio > 0:
                buy_and_hold_portfolio_equity = run_rebalancing_simulation(
                    buy_and_hold_invested_equity, invested_capital, initial_cash_position, daily_cash_return
                )
            else:
                cash_equity_curve = pd.Series(daily_cash_return, index=common_index).add(1).cumprod() * initial_cash_position
                buy_and_hold_portfolio_equity = buy_and_hold_invested_equity.add(cash_equity_curve, fill_value=initial_cash_position)

            plot_portfolio_equity(
                portfolio_equity=buy_and_hold_portfolio_equity, 
                strat_name='Buy and Hold', strat_params={}, plots_dir=plots_dir, initial_capital=initial_capital,
                pure_buy_and_hold_equity=pure_buy_and_hold_equity
            )

            final_val = buy_and_hold_portfolio_equity.iloc[-1]
            cagr = ((final_val / initial_capital)**(1/num_years) - 1) * 100
            running_max = buy_and_hold_portfolio_equity.cummax()
            drawdown = (buy_and_hold_portfolio_equity - running_max) / running_max
            max_dd = drawdown.min() * 100
            
            b_and_h_key = f'B&H with {Percent_Cash_Portfolio:.0%} Cash'
            portfolio_results[b_and_h_key] = {
                'Final Portfolio Value [$]': final_val,
                'CAGR [%]': cagr,
                'Max Drawdown [%]': max_dd
            }

    for strat_name, strat_class_lambda in STRATEGIES:
        print(f"Analyzing portfolio for strategy: {strat_name}...")
        all_equity_curves = []
        
        temp_strat_instance = strat_class_lambda()
        strat_params = temp_strat_instance.__dict__

        for filename, data in all_stock_data.items():
            if data.empty: continue
            strategy_instance = strat_class_lambda()
            engine = BacktestEngine(data, strategy_instance, initial_cash=capital_per_stock)
            _, equity_curve_raw = engine.run()
            equity_curve = pd.Series(equity_curve_raw.values[1:], index=data.index)
            reindexed_curve = equity_curve.reindex(common_index, method='ffill').fillna(capital_per_stock)
            all_equity_curves.append(reindexed_curve)

        if all_equity_curves:
            invested_portfolio_equity = pd.concat(all_equity_curves, axis=1).sum(axis=1)
            
            if Rebalance_Portfolio_Yearly and Percent_Cash_Portfolio > 0:
                total_portfolio_equity = run_rebalancing_simulation(
                    invested_portfolio_equity, invested_capital, initial_cash_position, daily_cash_return
                )
            else:
                cash_equity_curve = pd.Series(daily_cash_return, index=common_index).add(1).cumprod() * initial_cash_position
                total_portfolio_equity = invested_portfolio_equity.add(cash_equity_curve, fill_value=initial_cash_position)
            
            plot_portfolio_equity(
                portfolio_equity=total_portfolio_equity, strat_name=strat_name, strat_params=strat_params, plots_dir=plots_dir, initial_capital=initial_capital,
                buy_and_hold_equity=buy_and_hold_portfolio_equity,
                pure_buy_and_hold_equity=pure_buy_and_hold_equity
            )

            final_val = total_portfolio_equity.iloc[-1]
            cagr = ((final_val / initial_capital)**(1/num_years) - 1) * 100
            running_max = total_portfolio_equity.cummax()
            drawdown = (total_portfolio_equity - running_max) / running_max
            max_dd = drawdown.min() * 100
            portfolio_results[strat_name] = {
                'Final Portfolio Value [$]': final_val,
                'CAGR [%]': cagr,
                'Max Drawdown [%]': max_dd
            }
        else:
            final_val = initial_cash_position if Percent_Cash_Portfolio > 0 else 0
            cagr = ((final_val / initial_capital)**(1/num_years) - 1) * 100 if final_val > 0 else 0
            portfolio_results[strat_name] = {
                'Final Portfolio Value [$]': final_val,
                'CAGR [%]': cagr,
                'Max Drawdown [%]': 0
            }

    # --- Generate and Save Report ---
    print("\n--- Portfolio Analysis Results ---")
    results_df = pd.DataFrame.from_dict(portfolio_results, orient='index')

    benchmarks = []
    b_and_h_cash_key = f'B&H with {Percent_Cash_Portfolio:.0%} Cash'
    if '100% Equity B&H' in results_df.index:
        benchmarks.append(results_df.loc[['100% Equity B&H']])
    if b_and_h_cash_key in results_df.index:
        benchmarks.append(results_df.loc[[b_and_h_cash_key]])
    
    benchmark_keys = [b.index[0] for b in benchmarks] if benchmarks else []
    other_strategies = results_df.drop(benchmark_keys).sort_values(by='CAGR [%]', ascending=False)
    
    sorted_df = pd.concat(benchmarks + [other_strategies])

    for col in sorted_df.columns:
        if col == 'Final Portfolio Value [$]':
            sorted_df[col] = sorted_df[col].apply(lambda x: f"${x:,.1f}")
        elif col in ['CAGR [%]', 'Max Drawdown [%]']:
            sorted_df[col] = sorted_df[col].apply(lambda x: f"{x:,.1f}")

    report_content = sorted_df.to_markdown()

    print(report_content)

    report_path = os.path.join(os.path.dirname(__file__), 'portfolio_report.md')
    today_str = date.today().strftime('%Y-%m-%d')

    # --- Robust file writing with error handling ---
    try:
        with open(report_path, 'w') as f:
            f.write("# Portfolio Analysis Report\n\n")
            f.write(f"**Analysis Date:** {today_str}\n\n")
            f.write(f"**Data Span:** {analysis_start_date} to {analysis_end_date} ({num_years:.1f} years)\n\n")
            f.write(f"**Initial Capital:** ${initial_capital:,.2f}\n\n")
            f.write("### Portfolio Allocation Strategy\n")
            f.write(f"- **Target Cash Allocation:** {Percent_Cash_Portfolio:.1%}\n")
            f.write(f"- **Assumed Cash Annual Return:** {Cash_Yearly_Rtn:.1%}\n")
            f.write(f"- **Annual Rebalancing:** {'Yes' if Rebalance_Portfolio_Yearly and Percent_Cash_Portfolio > 0 else 'No (Static Allocation)'}\n\n")
            f.write(f"**Portfolio Stocks ({num_stocks} total):** {', '.join(stock_symbols)}\n\n")
            f.write(report_content)
        print(f"\nReport successfully saved to {report_path}")
    except IOError as e:
        print(f"\n--- ERROR: Could not write report to file! ---")
        print(f"Path: {report_path}")
        print(f"Reason: {e}")
        print("\nPlease check file permissions or if the file is locked by another program.")


if __name__ == '__main__':
    run_portfolio_analysis()