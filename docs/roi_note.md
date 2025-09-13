# ROI Analysis Note

This note provides a high-level framework for estimating the Return on Investment (ROI) of the telematics-based UBI program.

### ROI Formula

The basic formula for estimating the annual financial impact is:

`ROI = (Gross Savings from Reduced Claims) - (Total Operational Costs)`

A more detailed version is:

`(Δ Expected Loss Per User × Adoption Rate × Portfolio Size) - (Operational Cost Per User × Adoption Rate × Portfolio Size)`

Where:
*   **Δ Expected Loss Per User:** The average reduction in claim payouts per user per year due to safer driving.
*   **Adoption Rate:** The percentage of the customer base enrolled in the program.
*   **Portfolio Size:** The total number of customers.
*   **Operational Cost Per User:** The annual cost to support one user on the platform (e.g., data processing, customer support).

### Baseline Assumptions & Calculation

Let's assume a portfolio of **100,000** customers.

| Metric                      | Assumption | Notes                                                              |
|-----------------------------|------------|--------------------------------------------------------------------|
| Avg. Annual Premium         | $1,200     | Industry average for context.                                      |
| Baseline Claim Frequency    | 5%         | 5,000 claims per year in the portfolio.                            |
| Avg. Loss Per Claim         | $5,000     | Average cost to the insurer for a single claim.                    |
| **Δ Expected Loss Per User**| **$125**   | Assumes the program reduces overall claim frequency by 0.5% among adopters, leading to an average saving of $125/user/year across the portfolio of adopters. |
| **Adoption Rate**           | **30%**    | 30,000 users adopt the program.                                    |
| **Operational Cost Per User** | **$20**    | Annual cost for data, support, and platform maintenance per user.  |

**Calculation:**

*   **Gross Savings:** `$125 * 0.30 * 100,000 = $3,750,000`
*   **Total Operational Cost:** `$20 * 0.30 * 100,000 = $600,000`
*   **Estimated Annual ROI:** `$3,750,000 - $600,000 = $3,150,000`

### Sensitivity Analysis

The ROI is highly sensitive to the adoption rate and the actual reduction in loss. This table shows how the estimated ROI changes with these key variables.

| Adoption Rate | Δ Expected Loss Per User | Estimated Annual ROI |
|---------------|--------------------------|----------------------|
| 20%           | $100                     | $1,600,000           |
| **30%**       | **$125**                 | **$3,150,000**       |
| 40%           | $150                     | $5,200,000           |

This analysis, while high-level, demonstrates that the program has the potential for a significant positive ROI, driven by the dual benefit of improved driver safety and lower claim payouts.
