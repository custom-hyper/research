import numpy as np
import pandas as pd
import seaborn as sns
import matplotlib.pyplot as plt
from pycoingecko import CoinGeckoAPI
from datetime import datetime, timedelta

# Initialize CoinGecko API client
cg = CoinGeckoAPI()

# Fetch the Top 25 Tokens
top_tokens = cg.get_coins_markets(vs_currency='usd', order='market_cap_desc', per_page=25, page=1)
tokens = [{"id": token["id"], "symbol": token["symbol"], "name": token["name"]} for token in top_tokens]

# Select last 10 tokens from top 25 for the portfolio
portfolio_tokens = tokens[-10:]
portfolio_weights = [1 / len(portfolio_tokens)] * len(portfolio_tokens)

# Fetch historical prices
def get_historical_prices(token_id, days=365):
    data = cg.get_coin_market_chart_range_by_id(
        id=token_id,
        vs_currency='usd',
        from_timestamp=int((datetime.now() - timedelta(days=days)).timestamp()),
        to_timestamp=int(datetime.now().timestamp())
    )
    prices = data["prices"]
    return pd.DataFrame(prices, columns=["timestamp", "price"]).assign(
        date=lambda x: pd.to_datetime(x["timestamp"], unit='ms').dt.date
    )

# Fetch historical prices for the portfolio tokens
historical_data = {token['id']: get_historical_prices(token['id'], days=365) for token in portfolio_tokens}

# Combine all token data into a single DataFrame
price_df = pd.DataFrame({
    token['id']: data.set_index("date")["price"] for token, data in zip(portfolio_tokens, historical_data.values())
})

# Calculate daily percentage returns
returns_df = price_df.pct_change().dropna()

# Calculate weighted portfolio returns
weighted_returns = returns_df @ portfolio_weights

# Monte Carlo Simulation
def monte_carlo_simulation(returns, num_simulations=1000, days=365, initial_value=10000):
    simulated_portfolios = []
    for _ in range(num_simulations):
        daily_returns = np.random.choice(returns, size=days, replace=True)
        cumulative_return = np.cumprod(1 + daily_returns)  # Simulate daily compounding
        simulated_portfolios.append(initial_value * cumulative_return[-1])
    return simulated_portfolios

# Run Monte Carlo simulation
num_simulations = 1000
simulated_values = monte_carlo_simulation(weighted_returns.values, num_simulations)

# Prepare results
mean_value = np.mean(simulated_values)
median_value = np.median(simulated_values)
percentile_5 = np.percentile(simulated_values, 5)
percentile_95 = np.percentile(simulated_values, 95)

# Print Monte Carlo results
print(f"Mean Portfolio Value: ${mean_value:,.2f}")
print(f"Median Portfolio Value: ${median_value:,.2f}")
print(f"5th Percentile Value: ${percentile_5:,.2f}")
print(f"95th Percentile Value: ${percentile_95:,.2f}")

# Calculate the correlation matrix of the returns
correlation_matrix = returns_df.corr()

# Calculate the average pairwise correlation
avg_pairwise_corr = correlation_matrix.where(np.triu(np.ones(correlation_matrix.shape), k=1).astype(bool)).mean().mean()

print(f"Average Pairwise Correlation: {avg_pairwise_corr:.2f}")

# Correlation Heat Map
plt.figure(figsize=(10, 8))
sns.heatmap(correlation_matrix, annot=True, cmap="coolwarm", fmt=".2f", cbar=True)
plt.title("Correlation Heat Map of Portfolio Tokens")
plt.show()

# Plot the Monte Carlo simulation results
plt.figure(figsize=(10, 6))
plt.hist(simulated_values, bins=50, color='g', alpha=0.75)
plt.title("Monte Carlo Simulation of Portfolio Value")
plt.xlabel("Portfolio Value ($)")
plt.ylabel("Frequency")
plt.axvline(mean_value, color='r', linestyle='--', label=f'Mean: ${mean_value:,.2f}')
plt.axvline(median_value, color='b', linestyle='--', label=f'Median: ${median_value:,.2f}')
plt.legend()
plt.show()
