# HFT Trading Platform - TUI Guide

## Terminal User Interface (TUI)

The HFT Trading Platform includes a rich, interactive Terminal User Interface (TUI) built with [Rich](https://rich.readthedocs.io/).

### Features

The TUI provides an easy-to-use command-line interface for:
- **User Authentication**: Login with email and password
- **Order Management**: Place market and limit orders
- **Position Tracking**: View all open positions with P&L
- **Portfolio Monitoring**: Track overall portfolio performance
- **Order History**: View all placed orders and their status

### Quick Start

#### 1. Start the Full Platform

```bash
cd /Users/taylor/Library/CloudStorage/Dropbox/_GitHub/hft-trading-app

# Start all services
docker-compose up -d

# Wait for services to be ready
sleep 5

# Check status
docker-compose ps
```

#### 2. Run the TUI

Open a new terminal and run:

```bash
cd /Users/taylor/Library/CloudStorage/Dropbox/_GitHub/ml-trading-app-py

python -m frontend.tui
```

The TUI will:
1. Check backend health (http://localhost:8000)
2. Display the main menu
3. Guide you through trading operations

### Menu Options

```
Trading Platform Menu
1. Login
2. Place Market Order
3. Place Limit Order
4. View Positions
5. View Portfolio
6. View Orders
7. Exit
```

### Example Workflow

#### Login
```
Select option (1-7): 1
Email: trader@example.com
Password: password123
```

#### Place Market Order
```
Select option (1-7): 2
Symbol (e.g., AAPL): AAPL
Side (BUY/SELL): BUY
Quantity: 100.0
```

#### View Positions
```
Select option (1-7): 4
```

Displays a table with:
- Symbol
- Quantity held
- Entry Price
- Current Price
- Unrealized P&L (color-coded: green for profit, red for loss)

#### View Portfolio Summary
```
Select option (1-7): 5
```

Shows:
- Total number of positions
- Realized P&L (completed trades)
- Unrealized P&L (open positions)
- Total P&L (all positions combined)

### Running TUI Inside Docker

If you want to run the TUI inside a container instead:

```bash
cd /Users/taylor/Library/CloudStorage/Dropbox/_GitHub/hft-trading-app

# Create a container with the TUI
docker run -it --network hft-trading-app_hft-network \
  -e BACKEND_URL=http://hft-backend:8000 \
  hft-backend:latest \
  python -m frontend.tui
```

### Troubleshooting

#### TUI can't connect to backend

**Error**: `[red]Backend unavailable: Connection refused[/red]`

**Solution**:
1. Check backend is running: `docker-compose ps`
2. Verify backend URL (default: http://localhost:8000)
3. Try accessing directly: `curl http://localhost:8000/health`

#### Login fails

**Error**: `Login failed: Invalid credentials`

**Solution**:
1. Ensure backend is healthy: `docker logs hft-backend`
2. Check database is initialized: `docker exec hft-postgres psql -U trading_user -d trading_db -c "SELECT COUNT(*) FROM users;"`
3. Verify user account exists

#### Orders not placing

**Error**: `Order failed: Invalid symbol`

**Solution**:
1. Check symbol is valid (AAPL, GOOG, BTC/USD, etc.)
2. Verify market is open (in production)
3. Check risk limits aren't exceeded
4. View backend logs: `docker-compose logs hft-backend`

### Code Structure

The TUI is located in `ml-trading-app-py/frontend/tui.py` and includes:

```python
TradingTUI
├── login()              # Authenticate user
├── place_market_order() # Execute market order
├── place_limit_order()  # Execute limit order
├── show_positions()     # Display open positions
├── show_portfolio()     # Display portfolio summary
├── show_orders()        # Display order history
└── interactive_menu()   # Main menu loop
```

### Colors & Styling

The TUI uses Rich's styling:
- **Blue**: Headers and panels
- **Green**: Success messages and profitable P&L
- **Red**: Error messages and negative P&L
- **Cyan**: Symbols
- **Magenta**: Quantities and order details

### Performance Notes

- TUI makes HTTP requests to backend (no local buffering)
- Each menu selection triggers API call
- Positions and orders fetched fresh on demand
- P&L calculated real-time by backend

### Next Steps

1. **Customize**: Modify `frontend/tui.py` to add features
2. **Integrate**: Connect to live market data
3. **Deploy**: Package TUI in Docker image
4. **Automate**: Create trading scripts using TUI API

### References

- TUI Code: `ml-trading-app-py/frontend/tui.py`
- API Client: `ml-trading-app-py/frontend/client/api_client.py`
- Tests: `ml-trading-app-py/frontend/tests/test_tui.py`
- Rich Docs: https://rich.readthedocs.io/
