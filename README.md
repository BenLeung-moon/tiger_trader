# Tiger Trade & DeepSeek Auto Trader

A fully automated trading bot powered by **DeepSeek AI** and **Tiger Brokers API**. This agentic system autonomously scans markets, analyzes stocks using fundamental and technical data, and executes trades based on a customizable strategy.

Includes a **Web Dashboard** for real-time monitoring of portfolio performance, positions, and trade history.

## Features

- **AI-Powered Analysis**: Uses DeepSeek AI to select tickers and analyze market trends.
- **Multi-Market Support**: Automated trading for US, HK, and CN markets (configurable via `universe_manager.py`).
- **Intelligent Execution**: Handles market status checks, rate limiting, and automatic order type conversion (Market to Limit).
- **Portfolio Management**: Tracks current holdings and available funds to make informed decisions.
- **Pending Order Management**: Automatically monitors and manages open orders (cancel, modify, or keep).
- **Web Dashboard**: React-based frontend to visualize equity curves, current holdings, and trade logs.

## Quick Start

For detailed deployment instructions (including Docker setup), please refer to [DEPLOY.md](DEPLOY.md).

### Prerequisites

- Python 3.10+
- A Tiger Brokers account with API access enabled.
- DeepSeek API Key.
- Node.js (for Frontend).

### Installation (Manual)

1. **Clone the repository:**
   ```bash
   git clone https://github.com/yourusername/tiger_trader.git
   cd tiger_trader
   ```

2. **Install dependencies:**
   ```bash
   # Backend
   pip install -r requirements.txt

   # Frontend
   cd frontend
   npm install
   cd ..
   ```

### Configuration

Create a `credential/` directory and add the following files (see [DEPLOY.md](DEPLOY.md) for content details):

1.  `credential/ds_api.txt`: Your DeepSeek API Key.
2.  `credential/tiger_openapi_token.properties`: Tiger API token details.
3.  `credential/tiger_openapi_config.properties`: Tiger account configuration.
4.  `credential/private_key.pem`: Your Tiger API RSA private key.

## Usage

### 1. Run the Trading Bot
Run the main trading loop:
```bash
python main.py
```

### 2. Run the Dashboard
To view the dashboard, you need to run the backend API server and the frontend client.

**Backend API:**
```bash
python server.py
```

**Frontend:**
```bash
cd frontend
npm run dev
```

Visit `http://localhost:5173` (or the port shown) to view the dashboard.

## Agent Decision Procedure

The trading bot follows a structured decision-making process for each trading cycle:

1. **Market Scanning (Scanner Agent)**:
   - **Context**: Analyzes the user-defined strategy and current portfolio holdings.
   - **Search**: Scans the defined universe (managed in `universe_manager.py`) for potential candidates.
   - **Selection**: The AI selects the single best ticker candidate based on strategy alignment and market trends.

2. **Data Retrieval**:
   - Fetches historical price data (OHLCV) and fundamental data for the selected ticker.
   - Calculates technical indicators.
   - Checks current position status and available account funds.

3. **Deep Analysis (Analyst Agent)**:
   - **News Research**: Searches for real-time news, earnings reports, and sentiment regarding the specific ticker.
   - **Synthesis**: Combines technical data, fundamentals, news, and financial constraints.
   - **Decision**: The AI outputs a structured decision (`BUY`, `SELL`, or `HOLD`) along with a specific price and quantity, applying built-in risk management rules.

4. **Execution & Order Management**:
   - **Execution**: Places orders, automatically converting Market orders to Limit orders with a buffer for better execution.
   - **Pending Orders**: Periodically reviews open orders, deciding to `KEEP`, `MODIFY`, or `CANCEL` them based on real-time price movements.

## Structure

- `main.py`: Entry point and main trading loop.
- `server.py`: FastAPI backend for the dashboard.
- `frontend/`: React frontend code.
- `ai_agent.py`: AI logic for ticker selection and market analysis.
- `universe_manager.py`: Manages the list of trackable assets (stocks/ETFs).
- `data_engine.py`: Fetches historical and real-time market data.
- `execution.py`: Handles order placement and status checks.
- `portfolio.py`: Manages account funds and positions.
- `config.py`: Configuration loader for API keys and settings.
- `database.py`: SQLite database operations for trade history.
- `utils.py`: Utility functions (logging, JSON parsing, etc.).

## Disclaimer

**Use at your own risk.** Algorithmic trading involves significant risk of financial loss. This software is for educational purposes only and does not constitute financial advice.
