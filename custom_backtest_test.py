from custom_backtest_engine import BacktestEngine, MovingAverageCrossoverStrategy
import pandas as pd

# Test 1: Trade count matches expected (no pyramiding, no margin)
def test_trade_count():
    df = pd.read_csv('stockData/AAPL_1d.csv', index_col='Date', parse_dates=True)
    df.index = pd.to_datetime(df.index, utc=True).tz_localize(None)
    df = df[(df.index >= pd.Timestamp('2000-01-01')) & (df.index <= pd.Timestamp('2024-12-31'))]
    df = df.reset_index()
    strat = MovingAverageCrossoverStrategy(n1=10, n2=20, sl=0.95, tp=1.10)
    engine = BacktestEngine(df, strat)
    trades, equity = engine.run()
    expected_trades = 155  # From backtest_results.txt
    result = 'PASS' if len(trades) == expected_trades else f'FAIL (got {len(trades)})'
    print(f"Test 1 - Trade count: {result}")

# Test 2: No negative cash balance (no margin)
def test_no_negative_balance():
    df = pd.read_csv('stockData/AAPL_1d.csv', index_col='Date', parse_dates=True)
    df.index = pd.to_datetime(df.index, utc=True).tz_localize(None)
    df = df[(df.index >= pd.Timestamp('2000-01-01')) & (df.index <= pd.Timestamp('2024-12-31'))]
    df = df.reset_index()
    strat = MovingAverageCrossoverStrategy(n1=10, n2=20, sl=0.95, tp=1.10)
    engine = BacktestEngine(df, strat)
    trades, equity = engine.run()
    # Re-run logic to check cash
    cash = 100000
    size = 0.1
    for t in trades.itertuples():
        cost = t.entry_price * t.size
        if cost > cash + 1e-6:  # Allow for floating point tolerance
            print(f"Test 2 - Negative balance: FAIL (trade on {t.entry_date} exceeds cash)")
            return
        cash -= cost
        cash += t.exit_price * t.size
    print("Test 2 - Negative balance: PASS")

# Test 3: Number of buy signals matches number of trades (no pyramiding)
def test_buy_signals_vs_trades():
    df = pd.read_csv('stockData/AAPL_1d.csv', index_col='Date', parse_dates=True)
    df.index = pd.to_datetime(df.index, utc=True).tz_localize(None)
    df = df[(df.index >= pd.Timestamp('2000-01-01')) & (df.index <= pd.Timestamp('2024-12-31'))]
    df = df.reset_index()
    strat = MovingAverageCrossoverStrategy(n1=10, n2=20, sl=0.95, tp=1.10)
    engine = BacktestEngine(df, strat)
    # Count buy signals
    buy_signals = 0
    position = None
    from types import SimpleNamespace
    for i in range(len(df)):
        signal, sl, tp = strat.generate_signals(df, i, position)
        if not position and signal == 'buy':
            buy_signals += 1
            # Simulate opening a position (no pyramiding)
            # Use a mock Position object with required attributes
            position = SimpleNamespace(stop_loss=sl, take_profit=tp)
        elif position and signal == 'sell':
            position = None
    trades, equity = engine.run()
    result = 'PASS' if buy_signals == len(trades) else f'FAIL (buy_signals={buy_signals}, trades={len(trades)})'
    print(f"Test 3 - Buy signals vs trades: {result}")

if __name__ == '__main__':
    test_trade_count()
    test_no_negative_balance()
    test_buy_signals_vs_trades()
