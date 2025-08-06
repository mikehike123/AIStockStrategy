import os
import pandas as pd
import sys
from datetime import date
import matplotlib.pyplot as plt

# Add the project root to the Python path to allow for absolute imports
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

# --- Import the new flag from your config file ---
from swing_trading_strategies.config import START_DATE, END_DATE, Use_Log_Plots_Portfolio
from swing_trading_strategies.custom_backtest_engine import BacktestEngine
from swing_trading_strategies.main import STRATEGIES

def plot_portfolio_equity(portfolio_equity, strat_name, strat_params, plots_dir, initial_capital, buy_and_hold_equity=None):
    """
    Generates and saves a plot of the portfolio equity curve.
    Includes the Buy and Hold curve as a benchmark for comparison.
    """
    plt.style.use('seaborn-v0_8-darkgrid')
    fig, ax = plt.subplots(figsize=(15, 8))

    # Plot the primary strategy curve
    ax.plot(portfolio_equity.index, portfolio_equity.values, label=f'{strat_name} Equity', color='royalblue', linewidth=2, zorder=10)

    # --- New: Plot Buy and Hold on the same chart if provided ---
    if buy_and_hold_equity is not None:
        ax.plot(buy_and_hold_equity.index, buy_and_hold_equity.values, label='Buy and Hold Equity', color='gray', linestyle='-', linewidth=1.5, alpha=0.9, zorder=5)

    # Add a horizontal line for the initial capital
    ax.axhline(y=initial_capital, color='red', linestyle='--', linewidth=1.5, label=f'Initial Capital (${initial_capital:,.0f})')

    # Logic to switch between Linear and Log scale
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


def run_portfolio_analysis(initial_capital=100000):
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))
    data_dir = os.path.join(project_root, 'stockData')
    
    plots_dir = os.path.join(os.path.dirname(__file__), 'plots', 'portfolios')
    os.makedirs(plots_dir, exist_ok=True)
    
    stock_files = [f for f in os.listdir(data_dir) if f.endswith('.csv')]
    stock_symbols = [f.split('_')[0] for f in stock_files]
    num_stocks = len(stock_files)
    capital_per_stock = initial_capital / num_stocks

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

    # --- Buy and Hold Calculation ---
    buy_and_hold_portfolio_equity = None # Initialize
    buy_and_hold_curves = []
    for filename, data in all_stock_data.items():
        initial_price = data['Close'].iloc[0]
        shares = capital_per_stock / initial_price
        equity_curve = shares * data['Close']
        reindexed_curve = equity_curve.reindex(common_index, method='ffill').fillna(capital_per_stock)
        buy_and_hold_curves.append(reindexed_curve)
    
    if buy_and_hold_curves:
        buy_and_hold_portfolio_equity = pd.concat(buy_and_hold_curves, axis=1).sum(axis=1)
        
        # Plot Buy and Hold on its own (no comparison line needed)
        plot_portfolio_equity(
            portfolio_equity=buy_and_hold_portfolio_equity, 
            strat_name='Buy and Hold', 
            strat_params={}, 
            plots_dir=plots_dir, 
            initial_capital=initial_capital,
            buy_and_hold_equity=None # Explicitly set to None
        )

        initial_portfolio_value = buy_and_hold_portfolio_equity.iloc[0]
        final_portfolio_value = buy_and_hold_portfolio_equity.iloc[-1]
        portfolio_return_pct = (final_portfolio_value - initial_portfolio_value) / initial_portfolio_value * 100
        running_max = buy_and_hold_portfolio_equity.cummax()
        drawdown = (buy_and_hold_portfolio_equity - running_max) / running_max
        max_drawdown_pct = drawdown.min() * 100

        portfolio_results['Buy and Hold'] = {
            'Final Portfolio Value [$]': final_portfolio_value,
            'Portfolio Return [%]': portfolio_return_pct,
            'Max Drawdown [%]': max_drawdown_pct
        }

    for strat_name, strat_class_lambda in STRATEGIES:
        print(f"Analyzing portfolio for strategy: {strat_name}...")
        all_equity_curves = []
        
        temp_strat_instance = strat_class_lambda()
        strat_params = temp_strat_instance.__dict__

        for filename, data in all_stock_data.items():
            strategy_instance = strat_class_lambda()
            engine = BacktestEngine(data, strategy_instance, initial_cash=capital_per_stock)
            _, equity_curve_raw = engine.run()

            equity_curve = pd.Series(equity_curve_raw.values[1:], index=data.index)
            
            reindexed_curve = equity_curve.reindex(common_index, method='ffill').fillna(capital_per_stock)
            all_equity_curves.append(reindexed_curve)

        if all_equity_curves:
            portfolio_equity = pd.concat(all_equity_curves, axis=1).sum(axis=1)
            
            # --- Updated call: Pass the B&H data for comparison ---
            plot_portfolio_equity(
                portfolio_equity=portfolio_equity, 
                strat_name=strat_name, 
                strat_params=strat_params, 
                plots_dir=plots_dir, 
                initial_capital=initial_capital,
                buy_and_hold_equity=buy_and_hold_portfolio_equity
            )

            initial_portfolio_value = portfolio_equity.iloc[0]
            final_portfolio_value = portfolio_equity.iloc[-1]
            portfolio_return_pct = (final_portfolio_value - initial_portfolio_value) / initial_portfolio_value * 100

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

    if 'Buy and Hold' in results_df.index:
        buy_and_hold_row = results_df.loc[['Buy and Hold']]
        other_strategies = results_df.drop('Buy and Hold').sort_values(by='Portfolio Return [%]', ascending=False)
        results_df = pd.concat([buy_and_hold_row, other_strategies])
    else:
        results_df = results_df.sort_values(by='Portfolio Return [%]', ascending=False)

    results_df['Final Portfolio Value [$]'] = results_df['Final Portfolio Value [$]'].apply(lambda x: f"{x:,.1f}")
    results_df['Portfolio Return [%]'] = results_df['Portfolio Return [%]'].apply(lambda x: f"{x:,.1f}")
    results_df['Max Drawdown [%]'] = results_df['Max Drawdown [%]'].apply(lambda x: f"{x:,.1f}")

    report_content = results_df.to_markdown()

    print(report_content)

    report_path = os.path.join(os.path.dirname(__file__), 'portfolio_report.md')
    today_str = date.today().strftime('%Y-%m-%d')

    with open(report_path, 'w') as f:
        f.write("# Portfolio Analysis Report\n\n")
        f.write(f"**Analysis Date:** {today_str}\n\n")
        f.write(f"**Data Span:** {analysis_start_date} to {analysis_end_date}\n\n")
        f.write(f"**Initial Capital:** ${initial_capital:,.2f}\n\n")
        f.write(f"**Portfolio Stocks ({num_stocks} total):** {', '.join(stock_symbols)}\n\n")
        f.write(f"*Capital was distributed equally among all stocks at the beginning of the analysis period.*\n\n")
        f.write("This report shows the performance of each strategy when applied across the entire portfolio of stocks.\n\n")
        f.write(report_content)
    print(f"\nReport saved to {report_path}")


if __name__ == '__main__':
    run_portfolio_analysis()