import sys
import json
import time
import config
from data_engine import DataEngine
from ai_agent import DeepSeekAgent
from execution import OrderExecutor
from portfolio import PortfolioManager
from utils import RateLimiter, round_price_to_tick, setup_loggers, setup_position_logger
from universe_manager import UniverseManager
from tigeropen.common.consts import Market, BarPeriod

# Setup Logging
trading_logger, error_logger = setup_loggers()
position_logger = setup_position_logger()

def main():
    print("=== Tiger Trade & DeepSeek Auto Trader (Agentic Mode) ===")
    
    # Initialize Modules
    try:
        if not config.TIGER_TOKEN:
            msg = "Error: TIGER_TOKEN is missing. Please check tiger_openapi_token.txt"
            print(msg)
            error_logger.error(msg)
            return

        data_engine = DataEngine()
        ai_agent = DeepSeekAgent()
        executor = OrderExecutor()
        portfolio_mgr = PortfolioManager()
        universe_mgr = UniverseManager()
        # Rate Limit: 5 actions per minute (60 seconds)
        rate_limiter = RateLimiter(max_calls=5, period_seconds=60)
        print("Modules initialized successfully.")
    except Exception as e:
        error_logger.error(f"Initialization Error: {e}")
        print(f"Initialization Error: {e}")
        return

    # User Input
    # For non-interactive environments, we can set a default strategy
    print(f"Using Tiger Account ID: {config.TIGER_ACCOUNT}")
    
    try:
        strategy = input("Enter Strategy Description (e.g., 'Find undervalued tech stocks with positive momentum'): ").strip()
    except EOFError:
        print("Non-interactive mode detected. Using default strategy.")
        strategy = "Construct portfolio for US and HK stocks for the most profitable stocks"

    print(f"\nStarting Agentic Trading Loop. Press Ctrl+C to stop.")

    while True:
        try:
            # 1. Rate Limiting Check
            if not rate_limiter.can_proceed():
                print("Rate limit reached. Waiting for next slot...")
                rate_limiter.wait_for_slot()
                print("Resuming...")

            print(f"\n--- New Cycle: {time.strftime('%H:%M:%S')} ---")
            
            # Check Market Status
            us_open, us_status = data_engine.check_market_status(Market.US)
            hk_open, hk_status = data_engine.check_market_status(Market.HK)
            cn_open, cn_status = data_engine.check_market_status(Market.CN)
            print(f"Market Status - US: {us_status}, HK: {hk_status}, CN: {cn_status}")

            if not us_open and not hk_open and not cn_open:
                print("All markets (US, HK, CN) are closed. Waiting for markets to open...")
                time.sleep(60)
                continue

            # 2. Step 1: Select Ticker (The "Scanner" Agent)
            # User requested AI to pick stocks with internet access and HSI/HSCEI/CSI300 constraint
            # NEW: Check portfolio first
            print("Checking current portfolio holdings...")
            current_holdings = portfolio_mgr.get_all_positions()
            
            # Log latest positions
            try:
                position_logger.info(f"Positions: {json.dumps(current_holdings)}")
            except Exception as log_err:
                error_logger.error(f"Failed to log positions: {log_err}")

            funds_info = portfolio_mgr.get_account_funds()
            
            if current_holdings:
                print(f"Current Holdings: {len(current_holdings)} positions")
            else:
                print("Current Holdings: None")
                
            if funds_info:
                print("Account Funds:")
                for currency, data in funds_info.items():
                    print(f"  - {currency}: Available {data.get('available_for_trade', 0)}")
            
            # Position Management (Risk Control)
            if current_holdings:
                print("Running Position Management (Risk Control)...")
                position_decisions = ai_agent.manage_positions(current_holdings)
                
                for decision in position_decisions:
                    if decision.get('action') == 'SELL':
                        symbol = decision.get('symbol')
                        percentage = decision.get('percentage', 1.0)
                        reason = decision.get('reason', 'Risk Management')
                        
                        # Find the quantity to sell
                        pos_data = next((p for p in current_holdings if p['symbol'] == symbol), None)
                        if pos_data:
                            total_qty = pos_data['quantity']
                            sell_qty = int(total_qty * percentage)
                            
                            if sell_qty > 0:
                                print(f"Executing RISK MANAGEMENT SELL: {symbol}, Qty: {sell_qty}, Reason: {reason}")
                                order_payload = {
                                    "symbol": symbol,
                                    "action": "SELL",
                                    "quantity": sell_qty,
                                    "price": 0, # Market order for immediate exit
                                    "reason": reason
                                }
                                executor.place_order(order_payload)
                            else:
                                print(f"Calculated sell quantity is 0 for {symbol} (Total: {total_qty}, Pct: {percentage})")

            print(f"AI Agent is scanning the market (HSI, HSCEI, CSI 300) based on strategy...")
            
            selection = ai_agent.select_ticker(strategy, current_holdings=current_holdings, universe_constraint="HSI, HSCEI, CSI 300")
            target_symbol = selection.get('symbol')
            company_name = selection.get('company_name', 'Unknown')
            reason = selection.get('reason', 'No reason provided')
            
            # Fix for HK Tickers: Ensure 5 digits (e.g., 700 -> 00700, 2828 -> 02828)
            if target_symbol and target_symbol.isdigit() and len(target_symbol) < 5:
                original_symbol = target_symbol
                target_symbol = target_symbol.zfill(5)
                print(f"Normalized ticker: {original_symbol} -> {target_symbol}")
            
            if not target_symbol:
                print("AI failed to select a target. Skipping cycle.")
                continue
                
            print(f"✓ Target Selected: {target_symbol} ({company_name})")
            print(f"  Reason: {reason}")

            # 3. Step 2: Fetch Data (The "Data" Step)
            print(f"Fetching data for {target_symbol}...")
            # Fetch Daily Data (Day K-line)
            df_day = data_engine.get_historical_data(target_symbol, period=BarPeriod.DAY, limit=120)
            # Fetch Weekly Data (Week K-line)
            df_week = data_engine.get_historical_data(target_symbol, period=BarPeriod.WEEK, limit=120)
            
            fundamentals = data_engine.get_fundamental_data(target_symbol)
            position = portfolio_mgr.get_position(target_symbol)
            
            if df_day.empty:
                print(f"No historical data found for {target_symbol}. Skipping.")
                time.sleep(5)
                continue

            # Add Indicators & Prepare JSON
            df_day_enriched = data_engine.add_technical_indicators(df_day)
            daily_data_json = df_day_enriched.tail(14).to_json(orient="records")
            
            if not df_week.empty:
                df_week_enriched = data_engine.add_technical_indicators(df_week)
                weekly_data_json = df_week_enriched.tail(14).to_json(orient="records")
            else:
                weekly_data_json = "[]"
            
            # 4. Step 3: Deep Analysis with Web Search (The "Analyst" Agent)
            print(f"Analyst Agent is researching {target_symbol}...")
            decision = ai_agent.analyze_market(target_symbol, daily_data_json, weekly_data_json, fundamentals, strategy, position_context=position, funds_info=funds_info)
            
            print("\n=== Final Decision ===")
            print(json.dumps(decision, indent=2))
            
            # 5. Execution
            if decision.get('action') in ['BUY', 'SELL']:
                trading_logger.info(f"Initiating Order Execution for {target_symbol}: {decision}")
                
                # Fix for "Invalid Order Type" (MKT) on standard accounts (especially HK stocks)
                # If price is 0 (Market Order), convert to Limit Order with buffer using real-time price
                if decision.get('price', 0) <= 0:
                    print("Fetching real-time price for Limit Order conversion...")
                    rt_price = data_engine.get_realtime_price(target_symbol)
                    
                    if rt_price and rt_price > 0:
                        buffer = 0.02 # 2% buffer to ensure immediate fill (simulating Market order)
                        if decision.get('action') == 'BUY':
                            raw_limit_price = rt_price * (1 + buffer)
                        else:
                            raw_limit_price = rt_price * (1 - buffer)
                            
                        # Check if it is a HK stock (5 digits)
                        is_hk_stock = target_symbol.isdigit() and len(target_symbol) == 5
                        
                        limit_price = round_price_to_tick(raw_limit_price, is_hk=is_hk_stock)
                            
                        print(f"Converted Market Order to Limit Order: Price {rt_price} -> Limit {limit_price}")
                        decision['price'] = limit_price
                    else:
                        msg = "Warning: Could not fetch real-time price. Proceeding with Market Order (might fail)."
                        print(msg)
                        error_logger.warning(msg)

                print("Executing order...")
                order = executor.place_order(decision)
                
                if order:
                    # Verify Order Status
                    print("Verifying order status...")
                    time.sleep(2) # Wait for network propagation
                    
                    # Assuming order has an 'id' or 'order_id' attribute
                    order_id = order.id if hasattr(order, 'id') and order.id else (order.order_id if hasattr(order, 'order_id') else None)
                    
                    if order_id:
                        updated_order = executor.get_order_status(order_id)
                        if updated_order:
                            status_msg = f"Order Status: {updated_order.status} | Filled: {updated_order.filled}/{updated_order.quantity}"
                            print(status_msg)
                            trading_logger.info(status_msg)
                            
                            status_str = str(updated_order.status)
                            if updated_order.status == 'Filled' or 'FILLED' in status_str:
                                print("Order executed successfully.")
                            elif updated_order.status in ['Submitted', 'New'] or any(s in status_str for s in ['SUBMITTED', 'NEW', 'PENDING']):
                                print("Order is active and waiting to be filled.")
                            elif 'EXPIRED' in status_str or 'REJECTED' in status_str:
                                print(f"Order failed with status: {status_str}")
                                
                                # Fallback for HK Stocks to RMB Counter (e.g., 00388 -> 80388)
                                if target_symbol and target_symbol.isdigit() and len(target_symbol) == 5 and target_symbol.startswith('0'):
                                    rmb_symbol = '8' + target_symbol[1:]
                                    print(f"Initiating fallback to RMB counter: {target_symbol} -> {rmb_symbol}")
                                    trading_logger.info(f"Fallback: Retrying {target_symbol} on RMB counter {rmb_symbol}")
                                    
                                    # Update decision with new symbol
                                    decision['symbol'] = rmb_symbol
                                    
                                    try:
                                        # Fetch real-time price for RMB counter
                                        print(f"Fetching real-time price for RMB counter {rmb_symbol}...")
                                        rmb_price = data_engine.get_realtime_price(rmb_symbol)
                                        
                                        if rmb_price and rmb_price > 0:
                                            # Calculate new limit price
                                            buffer = 0.02
                                            if decision.get('action') == 'BUY':
                                                new_limit = rmb_price * (1 + buffer)
                                            else:
                                                new_limit = rmb_price * (1 - buffer)
                                            
                                            decision['price'] = round_price_to_tick(new_limit, is_hk=True)
                                            print(f"RMB Counter Price: {rmb_price} -> Limit Order: {decision['price']}")
                                        else:
                                            print("Could not fetch RMB price. Defaulting to Market Order (price=0).")
                                            decision['price'] = 0
                                    except Exception as price_err:
                                        print(f"Error fetching RMB price: {price_err}. Defaulting to Market Order.")
                                        decision['price'] = 0

                                    # Execute Fallback Order
                                    print(f"Executing fallback order for {rmb_symbol}...")
                                    fallback_order = executor.place_order(decision)
                                    
                                    if fallback_order:
                                        # Verify Fallback Order
                                        time.sleep(2)
                                        fb_id = fallback_order.id if hasattr(fallback_order, 'id') and fallback_order.id else (fallback_order.order_id if hasattr(fallback_order, 'order_id') else None)
                                        
                                        if fb_id:
                                            fb_status_obj = executor.get_order_status(fb_id)
                                            if fb_status_obj:
                                                print(f"Fallback Order Status: {fb_status_obj.status} | Filled: {fb_status_obj.filled}")
                                                trading_logger.info(f"Fallback Order Status: {fb_status_obj.status}")
                                        else:
                                            print("Fallback order placed but ID not found.")
                                    else:
                                        print("Fallback order placement failed.")
                            else:
                                print(f"Order state: {status_str}")
                        else:
                            msg = "Could not fetch updated order status."
                            print(msg)
                            error_logger.error(msg)
                    else:
                        msg = "Could not determine Order ID to verify."
                        print(msg)
                        error_logger.error(msg)
            else:
                print(f"Decision is {decision.get('action')}. No trade executed.")
            
            # 6. Step 4: Manage Pending Orders
            # Check if there are any active orders that need attention (e.g. partial fills, old orders)
            try:
                open_orders = executor.get_open_orders()
                if open_orders:
                    print(f"\n--- Managing {len(open_orders)} Pending Orders ---")
                    # Collect market prices for referenced symbols
                    market_prices = {}
                    for order in open_orders:
                        sym = order.contract.symbol
                        if sym not in market_prices:
                            p = data_engine.get_realtime_price(sym)
                            market_prices[sym] = p if p else "Unknown"
                    
                    actions = ai_agent.manage_pending_orders(open_orders, market_prices)
                    
                    for act in actions:
                        oid = act.get('order_id')
                        action_type = act.get('action')
                        reason = act.get('reason', '')
                        
                        print(f"Order {oid}: {action_type} - {reason}")
                        
                        if action_type == 'CANCEL':
                            executor.cancel_order(oid)
                        elif action_type == 'MODIFY':
                            new_price = act.get('new_price')
                            if new_price:
                                executor.modify_order(oid, new_price=new_price)
                            else:
                                print("  - Warning: MODIFY action missing new_price")
                        elif action_type == 'KEEP':
                            pass
            except Exception as e:
                error_logger.error(f"Error managing pending orders: {e}")
                print(f"Error managing pending orders: {e}")

            # Cooldown
            time.sleep(180) 

        except KeyboardInterrupt:
            print("\nStopping bot...")
            break
        except Exception as e:
            error_logger.error(f"Unexpected Error: {e}")
            print(f"Unexpected Error: {e}")
            time.sleep(10)

if __name__ == "__main__":
    main()
