def generate_summary_from_trades(trades, equity_curve, initial_cash=100000):
    summary = {}
    summary['# Trades'] = len(trades)
    if equity_curve is not None and len(equity_curve) > 0:
        try:
            # If equity_curve is a DataFrame, look for the right column
            if hasattr(equity_curve, 'columns'):
                col = None
                for candidate in ['Equity', 'equity', 'Equity Final [$]']:
                    if candidate in equity_curve.columns:
                        col = candidate
                        break
                if col is not None:
                    final_equity = float(equity_curve[col].iloc[-1])
                else:
                    # fallback: use the last value of the last column
                    final_equity = float(equity_curve.iloc[-1, -1])
            else:
                final_equity = float(equity_curve.iloc[-1])
        except Exception as e:
            print(f"Error extracting final equity: {e}")
            final_equity = 'N/A'
        summary['Equity Final [$]'] = final_equity
        if isinstance(final_equity, float):
            summary['Return [%]'] = ((final_equity - initial_cash) / initial_cash) * 100
        else:
            summary['Return [%]'] = 'N/A'
    else:
        summary['Equity Final [$]'] = 'N/A'
        summary['Return [%]'] = 'N/A'
    if len(trades) > 0:
        summary['Win Rate [%]'] = 100 * sum(trades['PnL'] > 0) / len(trades)
        summary['Best Trade [%]'] = trades['ReturnPct'].max() * 100 if 'ReturnPct' in trades else 'N/A'
        summary['Worst Trade [%]'] = trades['ReturnPct'].min() * 100 if 'ReturnPct' in trades else 'N/A'
        summary['Avg. Trade [%]'] = trades['ReturnPct'].mean() * 100 if 'ReturnPct' in trades else 'N/A'
        # Calculate Sharpe Ratio (annualized, risk-free rate = 0)
        if equity_curve is not None and len(equity_curve) > 1:
            returns = pd.Series(equity_curve).pct_change().dropna()
            if len(returns) > 1:
                sharpe = (returns.mean() / returns.std()) * (252 ** 0.5)
                summary['Sharpe Ratio'] = sharpe
            else:
                summary['Sharpe Ratio'] = 'N/A'
        else:
            summary['Sharpe Ratio'] = 'N/A'
    else:
        summary['Win Rate [%]'] = 'N/A'
        summary['Best Trade [%]'] = 'N/A'
        summary['Worst Trade [%]'] = 'N/A'
        summary['Avg. Trade [%]'] = 'N/A'
        summary['Sharpe Ratio'] = 'N/A'
    return summary



import pandas as pd
import os
import sys
sys.path.append('..')  # Ensure parent dir is in path for import
from custom_backtest_engine import BacktestEngine, MovingAverageCrossoverStrategy

def run_backtest(strategy_class, data, cash=100000):
    strat = strategy_class()
    engine = BacktestEngine(data, strat, initial_cash=cash)
    trades, equity_curve = engine.run()
    # Rename columns for compatibility
    trades = trades.rename(columns={
        'pnl': 'PnL',
        'return_pct': 'ReturnPct',
        'exit_reason': 'Tag',
    })
    return {'_trades': trades, '_equity_curve': equity_curve}

if __name__ == '__main__':
    data_dir = 'stockData'
    results = {}
    for filename in os.listdir(data_dir):
        if filename.endswith('.csv'):
            ticker = filename.split('_')[0]
            data = pd.read_csv(f'{data_dir}/{filename}', index_col='Date', parse_dates=True)
            data.index = pd.to_datetime(data.index, utc=True).tz_localize(None)
            data = data[(data.index >= pd.Timestamp('2000-01-01')) & (data.index <= pd.Timestamp('2024-12-31'))]

            # Moving Average Crossover
            stats_ma = run_backtest(MovingAverageCrossoverStrategy, data)
            trades_ma = stats_ma['_trades']
            equity_curve_ma = stats_ma['_equity_curve'] if stats_ma['_equity_curve'] is not None and len(stats_ma['_equity_curve']) > 0 else None
            if equity_curve_ma is None:
                print(f"Warning: Equity curve missing or empty for {ticker} MA_Crossover")
            summary_ma = generate_summary_from_trades(trades_ma, equity_curve_ma)
            if ticker == 'GOOGL':
                trades_ma.to_csv('GOOGL_MA_Crossover_trades.csv')
            results[f'{ticker}_MA_Crossover'] = summary_ma

            # RSI Momentum (not implemented in custom engine, placeholder)
            # stats_rsi = run_backtest(RsiMomentumStrategy, data)
            # trades_rsi = stats_rsi['_trades']
            # equity_curve_rsi = stats_rsi['_equity_curve'] if stats_rsi['_equity_curve'] is not None and len(stats_rsi['_equity_curve']) > 0 else None
            # if equity_curve_rsi is None:
            #     print(f"Warning: Equity curve missing or empty for {ticker} RSI_Momentum")
            # summary_rsi = generate_summary_from_trades(trades_rsi, equity_curve_rsi)
            # results[f'{ticker}_RSI_Momentum'] = summary_rsi

            # Breakout (not implemented in custom engine, placeholder)
            # stats_breakout = run_backtest(BreakoutStrategy, data)
            # trades_breakout = stats_breakout['_trades']
            # equity_curve_breakout = stats_breakout['_equity_curve'] if stats_breakout['_equity_curve'] is not None and len(stats_breakout['_equity_curve']) > 0 else None
            # if equity_curve_breakout is None:
            #     print(f"Warning: Equity curve missing or empty for {ticker} Breakout")
            # summary_breakout = generate_summary_from_trades(trades_breakout, equity_curve_breakout)
            # results[f'{ticker}_Breakout'] = summary_breakout

    # Save only trade-log-based summary results to a file
    output_path = os.path.abspath('backtest_results.txt')
    print(f'Writing summary to: {output_path}')
    with open(output_path, 'w') as f:
        for key, value in results.items():
            summary_fields = ['# Trades', 'Equity Final [$]', 'Return [%]', 'Win Rate [%]', 'Best Trade [%]', 'Worst Trade [%]', 'Avg. Trade [%]', 'Sharpe Ratio']
            f.write(f'{key}:' + '\n')
            for field in summary_fields:
                if field in value:
                    f.write(f'{field:28}{value[field]}\n')
            f.write('\n')

