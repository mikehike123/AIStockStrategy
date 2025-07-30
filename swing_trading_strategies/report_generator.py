import pandas as pd
from datetime import date
from config import START_DATE, END_DATE

def generate_report(results_file):


    import os
    # Always use the subdirectory for results
    summary_csv_path = os.path.join(os.path.dirname(__file__), 'backtest_summary.csv')
    if not os.path.exists(summary_csv_path):
        raise FileNotFoundError('backtest_summary.csv not found. Please run the backtester first.')
    df = pd.read_csv(summary_csv_path)
    df = df.set_index('Strategy')


    # Convert relevant columns to numeric first
    numeric_cols = ['Equity Final [$]', 'Equity Peak [$]', 'Return [%]', 'Buy & Hold Return [%]', 'Max. Drawdown [%]', 'Avg. Drawdown [%]', 'Sharpe Ratio', 'Sortino Ratio', 'Calmar Ratio', 'Win Rate [%]', 'Avg. Trade [%]', 'Profit Factor', '# Trades', 'Best Trade [%]', 'Worst Trade [%]']
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors='coerce')


    # Print and log strategies with zero trades, but do not set 'N/A'
    zero_trade_strategies = []
    if '# Trades' in df.columns:
        zero_trade_mask = (df['# Trades'] == 0)
        zero_trade_strategies = df.index[zero_trade_mask].tolist()
        if zero_trade_strategies:
            print("Warning: The following strategies have zero trades:")
            for strat in zero_trade_strategies:
                print(f"  - {strat}")

            # Write warning to trade_logs.txt
            trade_log_path = os.path.join(os.path.dirname(__file__), 'trade_logs.txt')
            with open(trade_log_path, 'a') as logf:
                logf.write("Warning: The following strategies have zero trades:\n")
                for strat in zero_trade_strategies:
                    logf.write(f"  - {strat}\n")

    

    # Now format columns for display (only for non-N/A values)
    money_cols = ['Equity Final [$]']
    percent_cols = ['Return [%]', 'Win Rate [%]', 'Best Trade [%]', 'Worst Trade [%]', 'Avg. Trade [%]']
    sharpe_cols = ['Sharpe Ratio']
    for col in money_cols:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: f'{float(x):.2f}' if not pd.isna(x) else 'N/A')
    for col in percent_cols:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: f'{float(x):.1f}' if not pd.isna(x) else 'N/A')
    for col in sharpe_cols:
        if col in df.columns:
            df[col] = df[col].apply(lambda x: f'{float(x):.2f}' if not pd.isna(x) else 'N/A')

    # Sort by Sharpe Ratio (treat 'N/A' as 0 for sorting)
    def sharpe_sort(x):
        try:
            return float(x)
        except:
            return 0
    df_sorted = df.copy()
    if 'Sharpe Ratio' in df.columns:
        df_sorted = df_sorted.copy()
        df_sorted['Sharpe Ratio Sort'] = df_sorted['Sharpe Ratio'].apply(sharpe_sort)
        df_sorted = df_sorted.sort_values(by='Sharpe Ratio Sort', ascending=False)
        df_sorted = df_sorted.drop(columns=['Sharpe Ratio Sort'])
    top_5_strategies = df_sorted.head(5)

    report = """# Top 5 Swing Trading Strategies

**Report Generated:** {report_date}  
**Analysis Period:** {start_date} to {end_date}

This report details the top 5 swing trading strategies based on backtesting results.

## Strategy Comparison

{table}

## Winning Strategy

The winning strategy is **{winner}** with a Sharpe Ratio of {winner_sharpe}.

### Strategy Description

{winner_description}

"""

    if not top_5_strategies.empty:
        winner = top_5_strategies.index[0]
        # Use .get to avoid KeyError if column is missing
        winner_sharpe = top_5_strategies.loc[winner].get('Sharpe Ratio', 'N/A')
        winner_description = f"The winning strategy is {winner}. It is a {winner.split('_')[1]} strategy applied to {winner.split('_')[0]}."

        report = report.format(
            report_date=date.today().strftime('%Y-%m-%d'),
            start_date=START_DATE.strftime('%Y-%m-%d'),
            end_date=END_DATE.strftime('%Y-%m-%d'),
            table=top_5_strategies.to_markdown(),
            winner=winner,
            winner_sharpe=winner_sharpe,
            winner_description=winner_description
        )
    else:
        report = report.format(
            report_date=date.today().strftime('%Y-%m-%d'),
            start_date=START_DATE.strftime('%Y-%m-%d'),
            end_date=END_DATE.strftime('%Y-%m-%d'),
            table="No strategies to display.",
            winner="N/A",
            winner_sharpe="N/A",
            winner_description="No winning strategy found."
        )

    report_path = os.path.join(os.path.dirname(__file__), '..', 'swing_trading_report.md')
    with open(report_path, 'w') as f:
        f.write(report)

if __name__ == '__main__':
    generate_report('backtest_results.txt')