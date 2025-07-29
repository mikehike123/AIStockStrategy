
# Top 5 Swing Trading Strategies

This report details the top 5 swing trading strategies based on backtesting results.

## Strategy Comparison

| Strategy                                        |   # Trades |   Equity Final [$] |   Return [%] |   Win Rate [%] |   Best Trade [%] |   Worst Trade [%] |   Avg. Trade [%] |   Sharpe Ratio |
|:------------------------------------------------|-----------:|-------------------:|-------------:|---------------:|-----------------:|------------------:|-----------------:|---------------:|
| AAPL_TwoStdDev_UpperBand_Trailing               |          1 |        8.7566e+07  |      87466   |          100   |      8.7466e+06  |       8.7466e+06  |      8.7466e+06  |           1.05 |
| AAPL_TwoStdDev_YearlyTrend_LowerBand_Trailing   |          1 |        8.37131e+07 |      83613.1 |          100   |      8.36131e+06 |       8.36131e+06 |      8.36131e+06 |           0.99 |
| AAPL_TwoStdDev_SMA_Trailing_Pyramid_Hold_To_End |          4 |        5.08067e+07 |      50706.7 |           50   | 602595           |   -5629.8         | 171978           |           0.98 |
| TSLA_TwoStdDev_MonthlyTrend_LowerBand_Trailing  |          1 |        3.11036e+07 |      31003.6 |          100   |      3.10036e+06 |       3.10036e+06 |      3.10036e+06 |           0.98 |
| NVDA_TwoStdDev_SMA_Trailing_Pyramid             |        173 |   586778           |        486.8 |           47.4 |   5541.8         |   -1590.9         |    409.5         |           0.98 |

## Winning Strategy

The winning strategy is **AAPL_TwoStdDev_UpperBand_Trailing** with a Sharpe Ratio of 1.05.

### Strategy Description

The winning strategy is AAPL_TwoStdDev_UpperBand_Trailing. It is a TwoStdDev strategy applied to AAPL.

