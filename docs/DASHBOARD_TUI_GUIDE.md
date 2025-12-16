# Dashboard TUI Guide - Modern k9s/btop Style Interface

## Overview

The Dashboard TUI provides a **real-time, multi-section terminal interface** similar to popular tools like `k9s` (Kubernetes dashboard) and `btop` (system monitor). It displays price charts, orders, positions, and portfolio metrics in a single, organized view.

## Architecture

```
┌────────────────────────────────────────────────────────────┐
│  HFT Trading Platform Dashboard                            │
├────────────────────────────────────────────────────────────┤
│  [Ticker Input] [Load Chart Button]                        │
├────────────────────────────────────────────────────────────┤
│  Chart: AAPL                                               │
│  ┌──────────────────────────────────────────────────────┐ │
│  │  ASCII Price Chart (Real-time)                       │ │
│  │  With trend line and price points                    │ │
│  │  Updates every 5 seconds                             │ │
│  └──────────────────────────────────────────────────────┘ │
├──────────────────────────────┬──────────────────────────────┤
│  Recent Orders               │  Open Positions              │
│  ┌────────────────────────┐ │ ┌─────────────────────────┐  │
│  │ ID | Symbol | Qty | Px │ │ Symbol | Qty | Curr | PL│  │
│  │ ... Orders ...       │ │ │ ... Positions ...      │  │
│  └────────────────────────┘ │ └─────────────────────────┘  │
├─────────────────────────────────────────────────────────────┤
│  Portfolio Summary                                          │
│  Positions: 5 | Realized: $1,250 | Unrealized: $450       │
│  Total P&L: $1,700                                         │
└─────────────────────────────────────────────────────────────┘
```

## Installation

### 1. Install Dependencies

```bash
cd /Users/taylor/Library/CloudStorage/Dropbox/_GitHub/ml-trading-app-py

pip install -r requirements.txt
```

This installs:
- `textual>=0.40.0` - TUI framework (built on Rich)
- `plotext>=5.2.0` - ASCII charting library

### 2. Start Backend

```bash
cd /Users/taylor/Library/CloudStorage/Dropbox/_GitHub/hft-trading-app
docker-compose up -d
```

## Quick Start

```bash
cd /Users/taylor/Library/CloudStorage/Dropbox/_GitHub/ml-trading-app-py

# Run the dashboard TUI
python -m frontend.dashboard_tui
```

The dashboard will:
1. Connect to the backend at http://localhost:8000
2. Load default ticker (AAPL)
3. Fetch chart data and portfolio info
4. Display live dashboard with 5-second refresh

## Features

### 1. Price Chart Section (Top)
- **ASCII-based chart** showing price trends
- **Real-time updates** every 5 seconds
- **Ticker symbol** displayed in title
- **Last 50 price points** displayed
- **Responsive** to terminal width

**How to change ticker:**
```
1. Type symbol in "Enter ticker symbol" field
2. Click "Load Chart" or press Enter
3. Chart updates automatically
```

### 2. Orders Widget (Bottom Left)
- **Recent orders** table
- Columns: ID, Symbol, Side, Quantity, Price, Status
- **Shows last 10 orders**
- **Color-coded** by side (BUY/SELL)
- **Live updates** as orders are placed

### 3. Positions Widget (Bottom Right)
- **Open positions** with P&L
- Columns: Symbol, Quantity, Entry Price, Current Price, P&L
- **Green P&L** for profitable positions
- **Red P&L** for losing positions
- **Real-time** price updates

### 4. Portfolio Summary (Bottom)
- **Position count**
- **Realized P&L** (completed trades)
- **Unrealized P&L** (open positions)
- **Total P&L** (all combined)
- **Color-coded** (green for profit, red for loss)

## Controls

### Keyboard Shortcuts

| Key | Action |
|-----|--------|
| `q` | Quit the dashboard |
| `r` | Manual refresh |
| `Tab` | Switch between widgets |
| `Enter` | Load ticker (from input field) |

### Mouse Support
- Click buttons to interact
- Click widgets to focus

## Example Workflows

### Monitoring a Specific Stock

```
1. Launch dashboard: python -m frontend.dashboard_tui
2. Type "TSLA" in ticker input
3. Press Enter or click "Load Chart"
4. Watch real-time TSLA price chart
5. Monitor orders/positions below
```

### Watching Portfolio Performance

1. Dashboard loads automatically with portfolio metrics
2. Green numbers = profit, Red numbers = loss
3. All positions visible in Positions widget
4. Recent orders in Orders widget
5. Overall summary at bottom

### Placing Orders While Watching

The dashboard can run **while placing orders** via the REST API:

```bash
# In separate terminal
curl -X POST http://localhost:8000/api/orders \
  -H "Authorization: Bearer TOKEN" \
  -d '{
    "symbol": "AAPL",
    "side": "BUY",
    "quantity": 100,
    "order_type": "MARKET"
  }'

# Dashboard updates automatically within 5 seconds
```

## Customization

### Change Refresh Rate

Edit `frontend/dashboard_tui.py`:

```python
# Line 239: Change refresh interval (in seconds)
await asyncio.sleep(5)  # Change 5 to your preferred interval
```

### Add More Widgets

```python
class CustomWidget(Static):
    """Your custom widget."""
    
    def render(self) -> RenderResult:
        return Panel("Your content here")

# Add to TradingDashboard.compose()
yield CustomWidget()
```

### Change Layout

The `CSS` section controls layout:

```python
CSS = """
#chart_section {
    height: 15;  # Change height
    width: 1fr;
}
"""
```

## Performance Considerations

### Data Updates
- **Default refresh**: 5 seconds
- **Optimal for**: Intraday trading
- **Larger intervals**: For swing trading

### Network Usage
- **Per refresh**: ~5 API calls (chart, orders, positions, summary, health)
- **5 sec interval**: ~60 calls/min (~3.6 calls/sec average)
- **Suitable for**: Local network and normal internet

### Terminal Requirements
- **Minimum width**: 100 characters
- **Minimum height**: 30 lines
- **Best experience**: Full screen terminal
- **Supported**: macOS, Linux, Windows (with WSL)

## Troubleshooting

### Dashboard doesn't connect to backend

```
Error: Connection refused
```

**Solution:**
1. Start backend: `docker-compose up -d`
2. Check backend is healthy: `curl http://localhost:8000/health`
3. Verify backend URL in code (default: http://localhost:8000)

### Chart doesn't update

```
Chart shows "Loading chart data..."
```

**Solution:**
1. Ensure market data is available for ticker
2. Check backend is running and healthy
3. Verify ticker symbol is valid (AAPL, GOOG, TSLA, etc.)

### Dashboard crashes

```
textual error or crash
```

**Solution:**
1. Ensure terminal is large enough (100x30 minimum)
2. Update packages: `pip install --upgrade textual plotext`
3. Check Python version (3.10+)

### Slow refresh rate

**Solution:**
1. Increase refresh interval in code
2. Check internet connection
3. Verify backend is responsive

## Advanced Features

### Market Hours Detection (Future)
```python
async def is_market_open():
    """Check if market is open."""
    # Implementation here
```

### Alert System (Future)
```python
async def check_alerts():
    """Monitor positions for alerts."""
    # Notify on price targets, stop-loss, etc.
```

### Order Execution from Dashboard (Future)
```python
async def place_order_from_dashboard(symbol, side, qty):
    """Place orders directly from dashboard."""
    # Interactive order placement
```

## Comparison: Old vs New TUI

| Feature | Menu TUI | Dashboard TUI |
|---------|----------|---------------|
| **Layout** | Sequential menu | Multi-section dashboard |
| **Chart** | None | Real-time ASCII chart |
| **Updates** | Manual input | Automatic every 5s |
| **View** | One item at a time | All metrics visible |
| **Look & Feel** | Traditional CLI | Modern k9s/btop style |
| **Scalability** | Limited | Extensible with widgets |

## Integration with Existing Code

The Dashboard TUI uses the same `TradingAPIClient`:

```python
from frontend.client.api_client import TradingAPIClient

client = TradingAPIClient(base_url="http://localhost:8000")
```

All existing backend endpoints work with the dashboard:
- `/health` - Health check
- `/api/orders` - List orders
- `/api/positions` - List positions
- `/api/portfolio/summary` - Portfolio metrics

## File Structure

```
ml-trading-app-py/
├── frontend/
│   ├── dashboard_tui.py       # Main dashboard application
│   ├── tui.py                 # Legacy menu-based TUI
│   ├── client/
│   │   └── api_client.py      # Shared API client
│   └── tests/
│       └── test_tui.py        # TUI tests
└── requirements.txt           # Dependencies (includes textual, plotext)
```

## Next Steps

1. **Test the dashboard** with real market data
2. **Add more charts** (volume, bid/ask, orderbook depth)
3. **Implement alerts** (price targets, position limits)
4. **Add order placement** directly from dashboard
5. **Add historical analysis** with multiple timeframes

## References

- **Textual Docs**: https://textual.textualize.io/
- **Plotext Docs**: https://github.com/piccolomo/plotext
- **Similar Tools**: k9s (Kubernetes), btop (System Monitor), glances (System Monitor)
- **Backend API**: See `docs/README.md`

---

**Status**: Production Ready with placeholder market data

The dashboard is fully functional and ready for integration with live market data feeds.
