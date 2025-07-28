from backtesting import Strategy
from backtesting.lib import crossover
import pandas as pd

# --- BreakoutVer2: Long-only, with selectable stop loss, pyramiding ---
class BreakoutVer2(Strategy):
    # --- CONTROL PARAMETERS ---
    use_trailing_stop = True  # << NEW: Set to False to use a fixed stop loss
    sl_long = 0.95            # << NEW: Used only if use_trailing_stop is False
    
    # --- STRATEGY PARAMETERS ---
    breakout_period = 20
    max_pyramids = 1
    entry_size_perc = 1.0
    tp_long = 100.0
    trailing_stop_perc = 0.5

    def init(self):
        self.high = self.I(lambda x: pd.Series(x).rolling(self.breakout_period).max(), self.data.High)
        # These state variables are used for both stop loss types
        self.pyramid_count = 0
        self.entry_prices = []
        # This state variable is now ONLY for the trailing stop
        self.stop_price = None

    def next(self):
        price = self.data.Close[-1]

        # --- ENTRY LOGIC ---
        if self.pyramid_count < self.max_pyramids and price > self.high[-2]:
            
            # --- CONDITIONAL STOP LOSS ---
            if self.use_trailing_stop:
                # 1. Trailing Stop: Don't set a stop on the order, we will manage it manually.
                self.buy(size=self.entry_size_perc)
                # Set initial trailing stop price based on the high of the entry bar
                new_stop = self.data.High[-1] * (1 - self.trailing_stop_perc)
                self.stop_price = max(self.stop_price or 0, new_stop)
            else:
                # 2. Fixed Stop: Calculate the stop price and let the framework manage it.
                stop_loss_price = price * self.sl_long
                self.buy(size=self.entry_size_perc, sl=stop_loss_price)

            # Logic common to both entry types
            self.entry_prices.append(price)
            self.pyramid_count += 1
        
        # --- TRAILING STOP MANAGEMENT (This block is now conditional) ---
        # It only runs if we are using a trailing stop AND are in a position.
        if self.use_trailing_stop and self.pyramid_count > 0:
            # Update trailing stop on every bar
            new_stop = self.data.High[-1] * (1 - self.trailing_stop_perc)
            self.stop_price = max(self.stop_price, new_stop)
            
            # Check for our manually managed stop loss exit
            if self.data.Low[-1] < self.stop_price:
                self.position.close()

        # --- POSITION MANAGEMENT AND STATE RESET ---
        # If the position was closed by any means (fixed SL, trailing SL, TP, etc.), reset state.
        if self.position.is_long == False and self.pyramid_count > 0:
             self.pyramid_count = 0
             self.stop_price = None
             self.entry_prices = []

        # Check for profit target exit (this works for both stop types)
        if self.pyramid_count > 0 and self.entry_prices:
            avg_entry = sum(self.entry_prices) / len(self.entry_prices)
            target_price = avg_entry * (1 + self.tp_long)
            if self.data.High[-1] > target_price:
                self.position.close()
def SMA(array, n):
    """Return simple moving average of `array` of length `n`."""
    return pd.Series(array).rolling(n).mean()

def RSI(array, n=14):
    """Relative strength index"""
    # Approximate; can't calculate real RSI without full history
    gain = pd.Series(array).diff()
    loss = gain.copy()
    gain[gain < 0] = 0
    loss[loss > 0] = 0
    rs = gain.ewm(n).mean() / loss.abs().ewm(n).mean()
    return 100 - 100 / (1 + rs)

class MovingAverageCrossover(Strategy):
    n1 = 10
    n2 = 20
    sl_long = 0.95  # 5% stop loss for long positions
    tp_long = 1.10  # 10% take profit for long positions
    sl_short = 1.05 # 5% stop loss for short positions
    tp_short = 0.90 # 10% take profit for short positions

    def init(self):
        self.sma1 = self.I(SMA, self.data.Close, self.n1)
        self.sma2 = self.I(SMA, self.data.Close, self.n2)

    def next(self):
        # All-in: use 100% of available equity per trade (default behavior)
        price = self.data.Close[-1]
        if crossover(self.sma1, self.sma2):
            sl = price * self.sl_long
            tp = price * self.tp_long
            self.buy(sl=sl, tp=tp)


class RsiMomentum(Strategy):
    rsi_period = 14
    rsi_upper = 70
    rsi_lower = 30
    sl_long = 0.95  # 5% stop loss for long positions
    tp_long = 1.10  # 10% take profit for long positions
    sl_short = 1.05 # 5% stop loss for short positions
    tp_short = 0.90 # 10% take profit for short positions

    def init(self):
        self.rsi = self.I(RSI, self.data.Close, self.rsi_period)

    def next(self):
        # All-in: use 100% of available equity per trade (default behavior)
        price = self.data.Close[-1]
        if self.rsi < self.rsi_lower:
            sl = price * self.sl_long
            tp = price * self.tp_long
            self.buy(sl=sl, tp=tp)


class Breakout(Strategy):
    breakout_period = 20
    sl_long = 0.95  # 5% stop loss for long positions
    tp_long = 1.10  # 10% take profit for long positions
    sl_short = 1.05 # 5% stop loss for short positions
    tp_short = 0.90 # 10% take profit for short positions

    def init(self):
        self.high = self.I(lambda x: pd.Series(x).rolling(self.breakout_period).max(), self.data.High)
        self.low = self.I(lambda x: pd.Series(x).rolling(self.breakout_period).min(), self.data.Low)

    def next(self):
        # All-in: use 100% of available equity per trade (default behavior)
        price = self.data.Close[-1]
        if price > self.high[-2]:
            sl = price * self.sl_long
            tp = price * self.tp_long
            self.buy(sl=sl, tp=tp)