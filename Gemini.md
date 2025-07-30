# Master Prompt

I'd like you to to come up with a list of the 5 most profitable swing trading strategies.  Feel free to explore the best stop loss and profit target for each of the strategies.
I'd then like you backtest each of these strategies and you may interate to improve the strategies.
The account size for all of the strategies will $100K.  You can trade the symbols for which you have stock data for.  You may size the positions for what ever you feel meets the objective and you can trade as many different symbols as you like.  
Create a report describing the strategies, comparing these strategies using your backtesting with standard types of metrics, ie  max draw down,CARG, STD, and other metrics you feel are necessary.  Select the winning strategy based this analysis and run an analysis on all of the stocks in the stockData directory using this strategy. Does the strategy do better than taking the $100K at the start date and creating a portfolio of these stocks where the initial equity values were equal and holding them to the end date?

Note- your backtesting will use Python.  

# Analysis of Backtesting Results and Codebase

This report identifies several unreasonable results from the backtesting process and proposes potential causes and areas for further investigation by GeminiPro.

## Unreasonable Results Identified

1.  **Strategies with 0 Trades:**
    *   **Examples:** `AAPL_RSI_Momentum`, `ADBE_MA_Crossover`, `GOOGL_Breakout`, `MSFT_MA_Crossover`, `NFLX_RSI_Momentum`, `NVDA_MA_Crossover`, `PYPL_RSI_Momentum`, `QQQ_RSI_Momentum`, `TSLA_RSI_Momentum`, and many others.
    *   **Unreasonable Aspect:** A trading strategy that generates no trades is effectively a "do nothing" strategy. While some strategies might genuinely not find opportunities, such a high frequency of 0-trade results across different symbols and strategies suggests an underlying issue preventing trade signals from being generated or executed.

2.  **Strategies with -100% Return and -100% Max Drawdown:**
    *   **Examples:** `GOOGL_MA_Crossover`, `META_Breakout`, `MSFT_Breakout`, `PYPL_MA_Crossover`, `PYPL_Breakout`, `QQQ_MA_Crossover`, `TSLA_MA_Crossover`, `TSLA_Breakout`.
    *   **Unreasonable Aspect:** Complete loss of initial capital is an extreme and undesirable outcome. This indicates a severe flaw in the strategy's logic or a complete lack of risk management.

3.  **Extremely High Returns (e.g., `AAPL_MA_Crossover` with 163,593% Return):**
    *   **Example:** `AAPL_MA_Crossover` shows an `Equity Final [$]` of over $163 million from an initial $100,000, with an `Exposure Time [%]` of only 4.07%.
    *   **Unreasonable Aspect:** While high returns are the goal, such astronomical figures, especially with very low market exposure, are highly suspicious and often indicative of a bug, data anomaly, or an unrealistic backtesting scenario.

4.  **Extremely High Volatility (e.g., `GOOGL_RSI_Momentum` with `Volatility (Ann.) [%]` of 422,184,659%):**
    *   **Example:** `GOOGL_RSI_Momentum` exhibits an absurdly high annualized volatility.
    *   **Unreasonable Aspect:** This is clearly a numerical error or an artifact of division by zero/very small numbers in the volatility calculation, likely due to 0 trades or an extremely flat equity curve.

## Possible Causes and Areas for Exploration

Based on the review of `backtest_results.txt`, `strategies.py`, and `main.py`, here are the potential causes for the unreasonable results:

1.  **Critical Bug in `MovingAverageCrossover` Strategy (Original State):**
    *   **Observation:** In the original `strategies.py`, the `MovingAverageCrossover` strategy uses `if crossover(self.data.Close, self.n1, self.n2):`.
    *   **Problem:** The `crossover` function from `backtesting.py` expects two series (e.g., two moving average series) as its primary arguments, not a price series and two integer periods. This line is likely preventing any actual moving average crossover signals from being generated. If `crossover` never returns `True`, then no trades will be placed.
    *   **Impact:** This bug is a strong candidate for explaining the high number of "0 trades" for MA Crossover strategies and could also contribute to the -100% returns if it causes unintended behavior or very few, very bad trades. It might also be related to the extremely high returns if it causes the strategy to accidentally "buy and hold" during a strong bull market for a short, opportune period.
    *   **Recommendation:** Change the line to `if crossover(self.sma1, self.sma2):` (which was the correct state after my initial fix attempts).

2.  **Lack of Explicit Risk Management (Stop-Loss/Take-Profit):**
    *   **Observation:** None of the implemented strategies (`MovingAverageCrossover`, `RsiMomentum`, `Breakout`) in their original state include explicit stop-loss or take-profit mechanisms in their `buy()` or `sell()` calls.
    *   **Problem:** Without defined exit points for limiting losses or securing gains, strategies are highly vulnerable to large drawdowns, potentially leading to the -100% capital loss observed in several cases. The `backtesting.py` library, by default, uses all available cash for a trade, which can be very aggressive without risk controls.
    *   **Impact:** Directly contributes to the -100% return scenarios.
    *   **Recommendation:** Implement `stop_loss` and `take_profit` parameters within the `buy()` and `sell()` calls of each strategy. Ensure correct logic for long and short positions (e.g., `sl_long`, `tp_long`, `sl_short`, `tp_short`).

3.  **Initial `NaN` Values from Indicators Preventing Trades:**
    *   **Observation:** Indicators like `RSI` and `rolling().max()/min()` (used in `Breakout`) produce `NaN` values for an initial period corresponding to their lookback window.
    *   **Problem:** If the historical data for a given stock is too short, or if the strategy's lookback parameters (`n_rsi`, `n_lookback`) are large, the entire data series might consist of `NaN` values for the indicator, preventing any trade signals from being generated.
    *   **Impact:** Contributes to the "0 trades" issue, especially for `RsiMomentum` and `Breakout` strategies on shorter data sets.
    *   **Recommendation:** While `data.dropna(inplace=True)` in `main.py` helps, ensure that the data provided to the strategies after dropping NaNs is sufficient for the indicator calculations to produce valid signals. Consider adjusting strategy parameters or filtering out symbols with insufficient data.

4.  **Potential for Numerical Instability in Metrics:**
    *   **Observation:** The extremely high `Volatility (Ann.) [%]` for `GOOGL_RSI_Momentum` is a clear example.
    *   **Problem:** When strategies generate 0 trades, or the equity curve is very flat, certain performance metrics (like volatility, Sharpe Ratio, etc.) can become numerically unstable, leading to absurdly large or small values.
    *   **Impact:** Skews the interpretation of results and makes comparison difficult.
    *   **Recommendation:** After addressing the 0-trade issue, re-evaluate these metrics. For strategies with genuinely 0 trades, it might be better to explicitly state "N/A" for certain metrics rather than displaying `NaN` or erroneous numerical values.

5.  **Aggressive Default Position Sizing:**
    *   **Observation:** The `backtesting.py` library, by default, uses all available `cash` to open a position.
    *   **Problem:** While not a bug, this can lead to very large positions and amplified losses if the strategy is wrong, contributing to the -100% drawdown scenarios.
    *   **Impact:** Increases risk significantly.
    *   **Recommendation:** Explore implementing more sophisticated position sizing techniques (e.g., fixed fractional, fixed dollar amount per trade) within the strategies to manage risk more effectively.

## Important Note on `backtesting.py` Trade Handling

It's important to understand how `backtesting.py` handles open positions at the end of a backtest. All open positions are automatically closed at the very end of the backtest period. These forced closures are registered as trades, and their profit/loss is realized and included in the final statistics. Therefore, if a strategy shows "0 trades," it means that no entry signals were ever triggered throughout the entire backtest duration, not that positions were left open indefinitely.

## Next Steps for GeminiPro

1.  **Address the `crossover` function usage in `MovingAverageCrossover` in `strategies.py`:**
    *   Ensure `self.buy()` and `self.sell()` calls include appropriate `sl` and `tp` parameters for both long and short positions.
2.  **Implement Stop-Loss and Take-Profit to all strategies in `strategies.py`:**
    *   This is critical for realistic risk management.
3.  **Re-run all backtests using `main.py`** after making the above changes.
4.  **Re-generate the report using `report_generator.py`**.
5.  **Re-evaluate the results:** The extreme returns and -100% drawdowns should become more reasonable. If 0-trade strategies persist, further investigation into data length and strategy entry conditions will be needed.
6.  
# Tasks For GeminiPro  in today's session 7/26/2025

# --- GeminiPro Progress Log (as of 2025-07-26) ---

## What Has Been Fixed
- Fixed timezone handling in all data loading to ensure robust, error-free date filtering.
- Added code to export the full trade log for GOOGL Moving Average Crossover to CSV for transparency and debugging.
- Investigated the -100% loss anomaly for GOOGL_MA_Crossover: confirmed via trade log that the summary is incorrect and no catastrophic loss occurred.
- Patched backtester.py to use the trade log and equity curve for summary stats, bypassing the unreliable stats object.
- Implemented a summary generator that computes all key metrics (trades, final equity, return, etc.) directly from the trade log and equity curve for each strategy/symbol.
- Ensured that the summary in backtest_results.txt always matches the actual trades in the log for all strategies.
- Cleaned up debug print statements and updated swing_trading_report.md with accurate results and observations.
- Centralized `start_date` and `end_date` in `config.py` and updated `main.py` and `portfolio_analyzer.py` to use them, resolving date inconsistencies.
- Added and then removed debug statements for max drawdown calculation in `portfolio_analyzer.py` for verification.
- Added generation date and analysis date span to `swing_trading_report.md`.
- Fixed `report_generator.py` import error in `main.py` by moving the import statement to after `backtest_summary.csv` is created.
- Fixed `SyntaxError` in `report_generator.py` caused by nested triple-quoted string literal.
- Corrected `ValueError` in `report_generator.py` by properly handling `NaN` values during formatting.
- Ensured "Report Generated" and "Analysis Period" are on separate lines in `swing_trading_report.md` using explicit Markdown line breaks.

## What Is Left To Do
- (Optional) Refactor report generation to include additional metrics (e.g., max drawdown, Sharpe ratio) using only trade log and equity curve.
- (Optional) Add buy-and-hold comparison for each symbol in the summary and report.
- (Optional) Parameter optimization and further strategy improvements.
- (Optional) Replicate what we need from Backtest.  Before coding define what functions/classes need to be done with sudo code.  Add the plan to this document.  Write code and testharness to verify correctness.    

## How To Continue
- For further improvements, add more robust metrics and comparisons to the summary and report.
- Consider optimizing strategy parameters and exploring additional risk management techniques.

--- End GeminiPro Progress Log ---

## Plan to Replicate Core Backtest Functionality (Replacing Backtest Library)

### 1. Core Requirements
- Simulate trading a single stock with a given strategy, using OHLCV data.
- Support for:
  - Position management (open/close, size, entry/exit price)
  - Stop-loss and take-profit exits
  - Equity curve tracking
  - Trade log (entry/exit, PnL, return, duration)
  - Custom strategy logic (entry/exit signals)
  - Commission/slippage (optional)

### 2. Proposed Classes/Functions (Pseudocode)

#### a. `Trade`
- Holds info for a single trade: entry date/price, exit date/price, size, PnL, return, duration, reason for exit (tp/sl/close)

#### b. `Position`
- Tracks an open position: entry price, size, stop-loss, take-profit, open date

#### c. `BacktestEngine`
- Main class to run a backtest on a DataFrame and a strategy function/class
- Methods:
    - `run()`: iterates over data, applies strategy logic, manages positions, records trades, updates equity
    - Handles stop-loss/take-profit logic
    - Handles forced close at end
    - Returns trade log and equity curve

#### d. `Strategy` (Base Class)
- Interface for user strategies: must implement `generate_signals(data, state)`
- Can be subclassed for MA Crossover, RSI, Breakout, etc.

#### e. Utility Functions
- Performance metrics: total return, max drawdown, Sharpe, etc.
- Data loading helpers

### 3. Implementation Steps
1. Implement `Trade` and `Position` dataclasses.
2. Implement `BacktestEngine` with run loop, position management, and trade logging.
3. Implement a simple `Strategy` interface and one example (e.g., MA Crossover).
4. Write a test harness to:
    - Load a CSV
    - Run the engine with a sample strategy
    - Print trade log and equity curve
    - Compare results to Backtest library for validation

### 4. Next Steps
- After core is working, add more strategies and metrics.
- Refine for speed, flexibility, and multi-asset support if needed.
#### Implement the 2 Standard Deviation Strategy based on the logic in the "2 Standard Deviation Strategy.txt" pinescript file.
- This will use similar risk management as breakoutVer2; specfically profit target, trailing or fix stop loss.  
- It should also like breakoutVer2 allow pyramiding.
- It will be designed to only take long trades.
- It will be configurable to buy at the lower band, the sma, or upper band in the same way as the pinescript version can.
- When creating the object User should be able to configure these above features.  
