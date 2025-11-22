import json
import os
import traceback
from datetime import datetime
from langchain_openai import ChatOpenAI
from langchain.agents import create_agent
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.tools import tool
from langchain_community.tools import DuckDuckGoSearchRun
import config
from utils import setup_loggers

trading_logger, error_logger = setup_loggers()

# Initialize Search Tool
search_tool = DuckDuckGoSearchRun()

@tool
def market_web_search(query: str):
    """
    Useful for searching the latest market news, sentiment, or specific stock events on the internet.
    Input should be a specific query string.
    """
    try:
        return search_tool.run(query)
    except Exception as e:
        return f"Search failed: {e}"

class DeepSeekAgent:
    def __init__(self):
        # LangChain Chat Model (DeepSeek Compatible)
        self.llm = ChatOpenAI(
            model="deepseek-reasoner",
            openai_api_key=config.DEEPSEEK_API_KEY,
            openai_api_base=config.DEEPSEEK_BASE_URL,
            temperature=0.1,
            timeout=60
        )
        
        # Tools for the agent
        self.tools = [market_web_search]

    def select_ticker(self, user_strategy, current_holdings=None, universe_constraint="HSI, HSCEI, CSI 300"):
        """
        Step 1: Select a ticker based on strategy and internet search, constrained by universe.
        """
        print(f"  - Searching for candidates in {universe_constraint}...")
        
        # Format holdings for context
        holdings_context = "No current holdings."
        if current_holdings:
            holdings_str = ", ".join([f"{h['symbol']} ({h['quantity']} shares)" for h in current_holdings])
            holdings_context = f"Current Portfolio Holdings: {holdings_str}"
        
        # 1. Perform a broad search to get market context
        search_query = f"top performing stocks or best buy candidates in {universe_constraint} today based on {user_strategy}"
        try:
            # access global search_tool
            search_results = search_tool.run(search_query)
        except Exception as e:
            print(f"  - Search warning: {e}")
            # Log warning but don't spam error log unless critical
            error_logger.warning(f"Search warning during ticker selection: {e}")
            search_results = "Search unavailable. Rely on internal knowledge."

        # 2. Ask LLM to pick a stock
        prompt = f"""
        You are an expert portfolio manager.
        User Strategy: {user_strategy}
        Universe Constraint: {universe_constraint}
        {holdings_context}
        
        Market Search Context:
        {search_results}
        
        Task: Select the SINGLE best ticker from the constrained universe (HSI, HSCEI, CSI 300) that matches the strategy.
        You MUST strictly select a valid ticker symbol (e.g., 00700 for Tencent, 09988 for Alibaba, etc.).
        
        Consider the current holdings. You may choose to:
        1. Add to an existing winning position.
        2. Diversify into a new opportunity.
        3. Hedge if necessary (though normally we look for long opportunities).
        
        CRITICAL INSTRUCTION: 
        Do NOT pick a stock randomly. Use the search context or your knowledge of these indices to pick a strong candidate.
        If unsure, pick a major ETF like '2800' (Tracker Fund).
        
        Return ONLY a JSON object: {{"symbol": "TICKER", "reason": "Detailed reason why this is a valuable investment"}}
        """
        
        try:
            response = self.llm.invoke(prompt)
            content = response.content.strip()
            # Handle DeepSeek R1 thinking process if it leaks into content (it usually doesn't for invoke, but just in case)
            # For now assume standard output.
            
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "")
            elif content.startswith("```"):
                content = content.replace("```", "")
            return json.loads(content)
        except Exception as e:
            error_logger.error(f"Ticker Selection Error: {e}")
            return {"symbol": "2800", "reason": "Fallback due to error"}

    def manage_pending_orders(self, open_orders, current_market_prices):
        """
        Step 3: Manage pending (active) orders.
        Decide whether to KEEP, MODIFY, or CANCEL based on market conditions.
        """
        if not open_orders:
            return []

        print(f"  - Managing {len(open_orders)} pending orders...")
        
        # Format orders for context
        orders_context = []
        for order in open_orders:
            symbol = order.contract.symbol
            market_price = current_market_prices.get(symbol, "Unknown")
            
            # Safe attribute access
            order_id = order.order_id if hasattr(order, 'order_id') else (order.id if hasattr(order, 'id') else "Unknown")
            limit_price = order.limit_price if hasattr(order, 'limit_price') else "Market"
            quantity = order.quantity
            filled = order.filled
            status = order.status
            action = order.action
            
            orders_context.append({
                "id": order_id,
                "symbol": symbol,
                "action": action,
                "limit_price": limit_price,
                "filled": filled,
                "quantity": quantity,
                "status": status,
                "market_price": market_price
            })
            
        prompt = f"""
        You are a trading order manager. You have the following PENDING (active) orders.
        Your goal is to ensure orders are filled at good prices, or cancelled if the opportunity is lost.
        
        Pending Orders:
        {json.dumps(orders_context, indent=2)}
        
        Market Context:
        For each order, compare the 'limit_price' with 'market_price'.
        - If BUY order and market_price >> limit_price: The price has moved away. Consider MODIFY to increase price or CANCEL.
        - If BUY order and market_price is close: KEEP (wait).
        - If SELL order and market_price << limit_price: The price has dropped. Consider MODIFY to decrease price or CANCEL.
        - If order has been pending for a long time (implied by context not changing), be more aggressive.
        
        Task: Return a JSON list of actions for EACH order.
        Format:
        [
            {{
                "order_id": "ID_FROM_INPUT",
                "action": "KEEP", // Options: "KEEP", "CANCEL", "MODIFY"
                "new_price": 0, // Only if MODIFY
                "reason": "Short explanation"
            }},
            ...
        ]
        
        CRITICAL: 
        - Return valid JSON list only.
        - "new_price" is required if action is MODIFY.
        """
        
        try:
            response = self.llm.invoke(prompt)
            content = response.content.strip()
            
            if content.startswith("```json"):
                content = content.replace("```json", "").replace("```", "")
            elif content.startswith("```"):
                content = content.replace("```", "")
                
            actions = json.loads(content)
            return actions
        except Exception as e:
            error_logger.error(f"Order Management Error: {e}")
            return []

    def analyze_market(self, symbol, daily_data_json, weekly_data_json, fundamental_data_json, user_strategy, position_context=None, funds_info=None):
        """
        Step 2: Analyze specific ticker with Tools (Web Search).
        使用简化的方法：先搜索，再分析 (Simplified approach: search first, then analyze)
        """
        
        # Step 1: 使用搜索工具获取最新信息 (Use search tool to get latest info)
        print(f"  - Searching for news about {symbol}...")
        try:
            current_date = datetime.now().strftime("%Y %B") # e.g. 2023 October
            search_query = f"{symbol} stock news earnings latest updates {current_date}"
            search_results = search_tool.run(search_query)
        except Exception as e:
            print(f"  - Search failed: {e}")
            error_logger.warning(f"Search failed for {symbol}: {e}")
            search_results = "No recent news available."
        
        # Step 2: Prepare Cash Context
        cash_context = "No cash info available."
        if funds_info:
            # Determine currency simple heuristic: digits -> HKD, chars -> USD
            currency = 'HKD' if str(symbol).isdigit() else 'USD'
            
            # Check if we have info for this currency
            if currency in funds_info:
                cash_avail = funds_info[currency].get('available_for_trade', 0)
                cash_context = f"Available Cash ({currency}): {cash_avail}"
            else:
                # Fallback: show all funds
                cash_context = f"Available Funds: {json.dumps(funds_info)}"

        # Step 3: 构建完整的分析提示 (Build complete analysis prompt)
        analysis_prompt = f"""
You are a high-frequency trading analyst analyzing stock: {symbol}

USER STRATEGY: {user_strategy}

CURRENT POSITION: {position_context if position_context else 'None'}

AVAILABLE FUNDS: {cash_context}

FUNDAMENTAL DATA:
{json.dumps(fundamental_data_json, indent=2)}

TECHNICAL DATA (Daily - Last 14 bars):
{daily_data_json}

TECHNICAL DATA (Weekly - Last 14 bars):
{weekly_data_json}

LATEST NEWS & MARKET SENTIMENT:
{search_results}

TASK: Based on ALL the above information, decide whether to BUY, SELL, or HOLD this stock.

CRITICAL: You MUST respond with ONLY a valid JSON object in this exact format (no other text):
{{
    "action": "BUY",
    "symbol": "{symbol}",
    "price": 0,
    "quantity": 10,
    "reason": "Your detailed analysis combining technicals, fundamentals, and news"
}}

Remember:
- action must be "BUY", "SELL", or "HOLD"
- price: use 0 for market order
- quantity: Determine based on AVAILABLE FUNDS. 
  - Do NOT exceed available cash. 
  - Apply risk management (e.g., allocate 5-10% of cash per trade, or more if high conviction).
  - If cash is low, adjust quantity accordingly.
- reason: combine technical, fundamental, and news analysis

Output ONLY the JSON, nothing else:
"""
        
        try:
            # 直接调用LLM，不使用复杂的agent graph (Direct LLM call, avoiding complex agent graph)
            response = self.llm.invoke(analysis_prompt)
            output = response.content.strip()
            
            # 如果输出为空，使用默认值 (If output is empty, use default)
            if not output or not output.strip():
                msg = "Warning: LLM returned empty response. Using HOLD as fallback."
                print(msg)
                error_logger.warning(msg)
                return {"action": "HOLD", "symbol": symbol, "reason": "Empty LLM response"}
            
            # Clean parsing - handle markdown and extra formatting
            if output.startswith("```json"):
                output = output.replace("```json", "").replace("```", "").strip()
            elif output.startswith("```"):
                output = output.replace("```", "").strip()
            
            # 尝试找到JSON内容 (Try to find JSON content if mixed with text)
            if "{" in output and "}" in output:
                start_idx = output.find("{")
                end_idx = output.rfind("}") + 1
                output = output[start_idx:end_idx]
            
            # 解析JSON (Parse JSON)
            decision = json.loads(output)
            
            # 验证必需字段 (Validate required fields)
            if 'action' not in decision or 'symbol' not in decision:
                raise ValueError("Missing required fields in decision")
                
            return decision
            
        except json.JSONDecodeError as e:
            error_logger.error(f"JSON Parse Error: {e}. Raw output: {output[:500] if 'output' in locals() else 'No output'}...")
            return {"action": "HOLD", "symbol": symbol, "reason": f"JSON Parse Error: {e}"}
        except Exception as e:
            error_logger.error(f"Analysis Failed: {e}")
            traceback.print_exc() # Keep this for console debugging
            return {"action": "HOLD", "symbol": symbol, "reason": f"Error: {e}"}
