from dataclasses import dataclass
import pandas as pd
import numpy as np

# --- Data Classes ---

@dataclass
class Trade:
    entry_date: pd.Timestamp
    entry_price: float
    exit_date: pd.Timestamp
    exit_price: float
    size: float
    pnl: float
    return_pct: float
    duration: int
    exit_reason: str

@dataclass
class Position:
    entry_date: pd.Timestamp
    entry_price: float
    size: float
    stop_loss: float
    take_profit: float

# --- Base Strategy Class ---

class Strategy:
    def generate_signals(self, data, i, position):
        """
        User must override this method.
        Should return a tuple containing:
        (signal, sl_tp_info, trade_size_percentage)
        signal: 'buy', 'sell', 'hold', 'pyramid'
        sl_tp_info: A dictionary like {'sl': value, 'tp': value} or a string for exit reason.
        """
        raise NotImplementedError

# --- Strategy Implementations ---

class MovingAverageCrossoverStrategy(Strategy):
    def __init__(self, n1=10, n2=20, sl=0.95, tp=1.10):
        self.n1 = n1
        self.n2 = n2
        self.sl = sl
        self.tp = tp

    def generate_signals(self, data, i, position):
        if i < self.n2:
            return 'hold', None, None
        
        price = data['Close'].iloc[i]
        sma1 = data['Close'].iloc[i-self.n1+1:i+1].mean()
        sma2 = data['Close'].iloc[i-self.n2+1:i+1].mean()
        prev_sma1 = data['Close'].iloc[i-self.n1:i].mean()
        prev_sma2 = data['Close'].iloc[i-self.n2:i].mean()
        
        if not position:
            if prev_sma1 < prev_sma2 and sma1 > sma2:
                stop_loss = price * self.sl
                take_profit = price * self.tp
                return 'buy', {'sl': stop_loss, 'tp': take_profit}, 1.0 
        else:
            if price <= position.stop_loss:
                return 'sell', 'Stop Loss', None
            if position.take_profit and (price >= position.take_profit):
                return 'sell', 'Take Profit', None
        
        return 'hold', None, None

class RsiMomentumStrategy(Strategy):
    def __init__(self, rsi_period=14, rsi_upper=70, rsi_lower=30, sl=0.95, tp=1.10):
        self.rsi_period = rsi_period
        self.rsi_upper = rsi_upper
        self.rsi_lower = rsi_lower
        self.sl = sl
        self.tp = tp

    def generate_signals(self, data, i, position):
        if i < self.rsi_period:
            return 'hold', None, None
        
        close_prices = data['Close'].iloc[:i+1]
        delta = pd.Series(close_prices).diff()
        gain = delta.clip(lower=0).rolling(self.rsi_period, min_periods=self.rsi_period).mean()
        loss = -delta.clip(upper=0).rolling(self.rsi_period, min_periods=self.rsi_period).mean()
        rs = gain / loss
        rsi = (100 - (100 / (1 + rs))).iloc[-1]
        
        price = data['Close'].iloc[i]
        
        if not position:
            if rsi < self.rsi_lower:
                stop_loss = price * self.sl
                take_profit = price * self.tp
                return 'buy', {'sl': stop_loss, 'tp': take_profit}, 1.0
        else:
            if price <= position.stop_loss:
                return 'sell', 'Stop Loss', None
            if rsi > self.rsi_upper:
                return 'sell', 'RSI Overbought', None
            if position.take_profit and price >= position.take_profit:
                return 'sell', 'Take Profit', None

        return 'hold', None, None

class BreakoutStrategy(Strategy):
    def __init__(self, breakout_period=20, sl=0.95, tp=1.10):
        self.breakout_period = breakout_period
        self.sl = sl
        self.tp = tp

    def generate_signals(self, data, i, position):
        if i < self.breakout_period:
            return 'hold', None, None
            
        price = data['Close'].iloc[i]
        prev_high = data['High'].iloc[i-self.breakout_period:i].max()
        
        if not position:
            if price > prev_high:
                stop_loss = price * self.sl
                take_profit = price * self.tp
                return 'buy', {'sl': stop_loss, 'tp': take_profit}, 1.0
        else:
            if price <= position.stop_loss:
                return 'sell', 'Stop Loss', None
            if position.take_profit and price >= position.take_profit:
                return 'sell', 'Take Profit', None
                
        return 'hold', None, None

# In custom_backtest_engine.py

class BreakoutVer2Strategy(Strategy):
    def __init__(self, 
                 # --- Behavior Switches ---
                 use_trailing_stop=True,
                 fixed_stop_perc=0.05,
                 
                 # --- Strategy Parameters ---
                 breakout_period=20, 
                 trailing_stop_perc=0.05, 
                 max_pyramids=5, 
                 pyramid_profit_perc=0.20, 
                 entry_size_perc=0.2, 
                 tp_long_perc=1.10): # << Default to a reasonable 10% TP
        
        # --- Store all parameters ---
        self.use_trailing_stop = use_trailing_stop
        self.fixed_stop_perc = fixed_stop_perc
        self.breakout_period = breakout_period
        self.trailing_stop_perc = trailing_stop_perc
        self.max_pyramids = max_pyramids
        self.pyramid_profit_perc = pyramid_profit_perc
        self.entry_size_perc = entry_size_perc
        self.tp_long_perc = tp_long_perc # << NEW: Store the TP parameter
        
        # --- State Variables ---
        self.pyramid_count = 0
        self.long_stop_price = 0.0

    def generate_signals(self, data, i, position):
        if i < self.breakout_period:
            return 'hold', None, None

        price = data['Close'].iloc[i]
        high = data['High'].iloc[i]
        highest_high = data['High'].iloc[i-self.breakout_period:i].max()

        # --- EXIT LOGIC ---
        if position:
            # 1. Take Profit Check (works for both fixed and trailing stops)
            # << NEW: Added Take Profit check >>
            if position.take_profit and (price >= position.take_profit):
                return 'sell', 'Take Profit', None

            # 2. Stop Loss Check (conditional based on strategy mode)
            if self.use_trailing_stop:
                new_stop_candidate = high * (1 - self.trailing_stop_perc)
                self.long_stop_price = max(self.long_stop_price, new_stop_candidate)
                if price <= self.long_stop_price:
                    return 'sell', 'Trailing Stop', None
            else: # Using fixed stop
                if price <= position.stop_loss:
                    return 'sell', 'Fixed Stop', None

        # --- ENTRY LOGIC ---
        is_breakout = price > highest_high
        if is_breakout:
            if not position:
                self.pyramid_count = 1
                
                # << NEW: Add TP to the return dictionary >>
                sl_tp_dict = {}
                # Calculate the take profit price based on the entry price
                take_profit_price = price * self.tp_long_perc
                sl_tp_dict['tp'] = take_profit_price

                if self.use_trailing_stop:
                    self.long_stop_price = high * (1 - self.trailing_stop_perc)
                    sl_tp_dict['sl'] = self.long_stop_price
                else:
                    fixed_stop_price = price * (1 - self.fixed_stop_perc)
                    sl_tp_dict['sl'] = fixed_stop_price

                return 'buy', sl_tp_dict, self.entry_size_perc

            elif position and self.pyramid_count < self.max_pyramids:
                # (Pyramiding logic remains unchanged)
                profit_perc = (price - position.entry_price) / position.entry_price
                if profit_perc >= self.pyramid_profit_perc:
                    self.pyramid_count += 1
                    return 'pyramid', {'sl': self.long_stop_price}, self.entry_size_perc

        if position and self.use_trailing_stop:
            return 'hold', {'sl': self.long_stop_price}, None
        
        return 'hold', None, None
    
# --- BacktestEngine ---
class BacktestEngine:
    def __init__(self, data, strategy, initial_cash=100000):
        self.data = data.reset_index()
        self.strategy = strategy
        self.initial_cash = initial_cash
        self.equity_curve = []
        self.trades = []

    def run(self):
        cash = self.initial_cash
        position = None

        if hasattr(self.strategy, 'pyramid_count'):
            self.strategy.pyramid_count = 0
        if hasattr(self.strategy, 'long_stop_price'):
            self.strategy.long_stop_price = 0.0

        for i in range(len(self.data)):
            date = self.data['Date'].iloc[i]
            price = self.data['Close'].iloc[i]
            current_equity = cash + (position.size * price) if position else cash
            self.equity_curve.append(current_equity)

            signal, sl_tp_info, size_perc = self.strategy.generate_signals(self.data, i, position)
            
            if position and isinstance(sl_tp_info, dict):
                if 'sl' in sl_tp_info:
                    position.stop_loss = sl_tp_info['sl']
                if 'tp' in sl_tp_info:
                    position.take_profit = sl_tp_info['tp']

            if not position and signal == 'buy':
                trade_value = current_equity * (size_perc or 1.0)
                shares = trade_value / price
                position = Position(
                    entry_date=date, entry_price=price, size=shares,
                    stop_loss=sl_tp_info.get('sl'), 
                    take_profit=sl_tp_info.get('tp')
                )
                cash -= shares * price

            elif position and signal == 'pyramid':
                trade_value = current_equity * (size_perc or 1.0)
                new_shares = trade_value / price
                new_total_shares = position.size + new_shares
                new_avg_price = ((position.entry_price * position.size) + (price * new_shares)) / new_total_shares
                
                position.entry_price = new_avg_price
                position.size = new_total_shares
                cash -= new_shares * price

            elif position and signal == 'sell':
                exit_price = price
                pnl = (exit_price - position.entry_price) * position.size
                cash += position.size * exit_price
                
                return_pct = pnl / (position.entry_price * position.size) * 100
                duration = (date - position.entry_date).days
                
                self.trades.append(Trade(
                    entry_date=position.entry_date, entry_price=position.entry_price,
                    exit_date=date, exit_price=exit_price, size=position.size,
                    pnl=pnl, return_pct=return_pct, duration=duration,
                    exit_reason=sl_tp_info
                ))
                position = None
                if hasattr(self.strategy, 'pyramid_count'): self.strategy.pyramid_count = 0
                if hasattr(self.strategy, 'long_stop_price'): self.strategy.long_stop_price = 0.0

        if position:
            price = self.data['Close'].iloc[-1]
            date = self.data['Date'].iloc[-1]
            pnl = (price - position.entry_price) * position.size
            cash += position.size * price
            self.trades.append(Trade(
                entry_date=position.entry_date, entry_price=position.entry_price,
                exit_date=date, exit_price=price, size=position.size, pnl=pnl,
                return_pct=pnl / (position.entry_price * position.size) * 100,
                duration=(date - position.entry_date).days, exit_reason='forced_close'
            ))
        
        self.equity_curve.append(cash)
        return pd.DataFrame([t.__dict__ for t in self.trades]), pd.Series(self.equity_curve)

# --- Test Harness ---
if __name__ == '__main__':
    try:
        df = pd.read_csv('stockData/AAPL_1d.csv', index_col='Date', parse_dates=True)
    except FileNotFoundError:
        print("Error: 'stockData/AAPL_1d.csv' not found.")
        exit()

    df.index = pd.to_datetime(df.index, utc=True).tz_localize(None)
    df = df[(df.index >= pd.Timestamp('2020-01-01')) & (df.index <= pd.Timestamp('2023-12-31'))]
    
    print("--- Testing BreakoutVer2Strategy ---")
    strat_v2 = BreakoutVer2Strategy(
        breakout_period=20, trailing_stop_perc=0.10, max_pyramids=5, 
        pyramid_profit_perc=0.05, entry_size_perc=0.25, tp_long_perc=100.0
    )
    engine_v2 = BacktestEngine(df.copy(), strat_v2)
    trades_v2, equity_v2 = engine_v2.run()
    print(trades_v2.tail())
    print(f'Final Equity: ${equity_v2.iloc[-1]:,.2f}\n')

    print("--- Testing MovingAverageCrossoverStrategy ---")
    strat_ma = MovingAverageCrossoverStrategy(n1=10, n2=20)
    engine_ma = BacktestEngine(df.copy(), strat_ma)
    trades_ma, equity_ma = engine_ma.run()
    print(trades_ma.tail())
    print(f'Final Equity: ${equity_ma.iloc[-1]:,.2f}\n')