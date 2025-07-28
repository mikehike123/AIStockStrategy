import os
import pandas as pd

# Settings
initial_cash = 100000
stock_dir = 'stockData'

# Get all stock files
stock_files = [f for f in os.listdir(stock_dir) if f.endswith('.csv')]
num_stocks = len(stock_files)
if num_stocks == 0:
    raise Exception('No stock files found!')

# Equal allocation per stock
cash_per_stock = initial_cash / num_stocks

results = []
for filename in stock_files:
    ticker = filename.split('_')[0]
    df = pd.read_csv(os.path.join(stock_dir, filename), index_col='Date', parse_dates=True)
    df.index = pd.to_datetime(df.index, utc=True).tz_localize(None)
    df = df[(df.index >= pd.Timestamp('2000-01-01')) & (df.index <= pd.Timestamp('2024-12-31'))]
    if df.empty:
        continue
    first_price = df['Close'].iloc[0]
    last_price = df['Close'].iloc[-1]
    shares = cash_per_stock / first_price
    final_value = shares * last_price
    pct_return = (final_value - cash_per_stock) / cash_per_stock * 100
    results.append({
        'Symbol': ticker,
        'Start Price': first_price,
        'End Price': last_price,
        'Shares': shares,
        'Final Value': final_value,
        'Return [%]': pct_return
    })

total_final = sum(r['Final Value'] for r in results)
total_return = (total_final - initial_cash) / initial_cash * 100

# Print per-stock and portfolio results
print('Buy & Hold Results:')
for r in results:
    print(f"{r['Symbol']}: Start={r['Start Price']:.2f}, End={r['End Price']:.2f}, Return={r['Return [%]']:.2f}%")
print(f"\nPortfolio Final Value: ${total_final:,.2f}")
print(f"Portfolio Return: {total_return:.2f}%")

# Save to CSV
pd.DataFrame(results).to_csv('buy_and_hold_results.csv', index=False)
