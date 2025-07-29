That's an excellent and insightful question. You've correctly identified the crucial difference between the two concepts, and the answer gets to the very heart of investment strategy versus trading tactics.

The short answer is: **Yes, for the initial deployment of capital at the portfolio level, you would add the funds regardless of whether the previous additions were profitable.**

Let me explain why. We are talking about two distinct and separate actions:

1.  **Portfolio-Level Dollar-Cost Averaging (DCA):** This is a high-level *investment strategy* designed to manage the risk of deploying a large sum of capital.
2.  **Strategy-Level Pyramiding:** This is a lower-level *trading tactic* designed to maximize profit from a specific, confirmed trend in a single stock.

They should not be confused. Let's put them side-by-side:

| Feature | **Portfolio-Level DCA (Your Initial Investment)** | **Strategy-Level Pyramiding (Automated Tactic)** |
| :--- | :--- | :--- |
| **Purpose** | To get your initial capital invested over time, reducing the risk of a single bad entry point for the whole portfolio. | To add to an *existing, profitable trade* to maximize gains from a strong trend. |
| **Trigger** | **Time.** A pre-determined schedule (e.g., once a quarter). | **Performance.** A specific profit target being hit (e.g., the position is up 10%). |
| **Condition** | **Unconditional.** You invest the next chunk of money no matter what the market is doing. | **Conditional.** You *only* add to the position if it is already profitable. |
| **Psychology** | Removes emotion and the need to predict the market. It's a disciplined, automated process for capital deployment. | Capitalizes on the emotion of "letting your winners run" in a disciplined, automated way. |

### The Two-Phase Approach

The best way to think about this is as a two-phase process:

**Phase 1: Deploying Your Initial Capital (Using DCA)**

This is where you would invest your $100,000. You decide on a schedule—say, investing $25,000 every three months for a year.

*   **Quarter 1:** You invest the first $25,000. This capital is now "live" and being traded by your chosen automated strategy (e.g., "Buy and Hold" or one of the `TwoStdDev` strategies).
*   **Quarter 2:** The market might be down 10% from Q1. **It doesn't matter.** You invest the next $25,000 as planned. This is the discipline of DCA. Now you have $50,000 (plus or minus the gains/losses from the first chunk) being actively managed by your strategy.
*   **Quarter 3 & 4:** You repeat the process, investing the remaining chunks according to your schedule, *regardless of portfolio performance*.

By the end of the year, your full $100,000 is in the market. You didn't try to time the top or bottom; you simply averaged your entry price over a year.

**Phase 2: The Automated Strategy Takes Over (Using Pyramiding)**

*Throughout Phase 1 and for the next 20 years,* the automated trading strategy you've selected is running on the capital that has been deployed.

If you chose a strategy with pyramiding enabled (like `TwoStdDev_SMA_Trailing_Pyramid`), it will be looking for opportunities. When it enters a trade in, say, AAPL, it will *only* add to that specific AAPL position if the trade becomes profitable, according to the `pyramid_profit_perc` we set. It will not ask for new funds from your bank account; it will use the cash available within its own slice of the portfolio.

### Conclusion

So, you are correct on both counts:

1.  You should use a **time-based, unconditional** approach (DCA) to get your initial capital into the portfolio.
2.  Once the capital is in the portfolio, the **performance-based, conditional** pyramiding logic within the strategy takes over to manage individual trades.

This hybrid approach gives you the best of both worlds: a disciplined, risk-managed way to enter the market, and an aggressive, profit-maximizing tactic to manage your winning trades.