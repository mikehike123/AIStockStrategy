
# Top 5 Swing Trading Strategies

This report details the top 5 swing trading strategies based on backtesting results.

## Strategy Comparison

| Strategy                                       |   # Trades |   Equity Final [$] |   Return [%] |   Win Rate [%] |   Best Trade [%] |   Worst Trade [%] |   Avg. Trade [%] |   Sharpe Ratio |
|:-----------------------------------------------|-----------:|-------------------:|-------------:|---------------:|-----------------:|------------------:|-----------------:|---------------:|
| AAPL_TwoStdDev_YearlyTrend_LowerBand_Trailing  |          1 |        8.7566e+07  |      87466   |          100   |      8.7466e+06  |       8.7466e+06  |      8.7466e+06  |           1.05 |
| TSLA_TwoStdDev_MonthlyTrend_LowerBand_Trailing |          1 |        3.11036e+07 |      31003.6 |          100   |      3.10036e+06 |       3.10036e+06 |      3.10036e+06 |           0.98 |
| AAPL_BreakoutV2_20_Trailingstop                |         26 |        1.67533e+07 |      16653.3 |           46.2 |  41133           |   -2057.9         |   2958.6         |           0.95 |
| TSLA_TwoStdDev_YearlyTrend_LowerBand_Trailing  |          1 |        1.92888e+07 |      19188.8 |          100   |      1.91888e+06 |       1.91888e+06 |      1.91888e+06 |           0.94 |
| AAPL_BreakoutV2_TrailingStop                   |        135 |        3.67842e+06 |       3578.4 |           53.3 |   4497.6         |   -1717.1         |    311.1         |           0.93 |

## Winning Strategy

The winning strategy is **AAPL_TwoStdDev_YearlyTrend_LowerBand_Trailing** with a Sharpe Ratio of 1.05.

### Strategy Description

The winning strategy is AAPL_TwoStdDev_YearlyTrend_LowerBand_Trailing. It is a TwoStdDev strategy applied to AAPL.

