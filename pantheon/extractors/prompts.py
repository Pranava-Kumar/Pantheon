import json
from datetime import datetime

OUTPUT_SCHEMA = """{
  "direction": "BUY or HOLD or SELL",
  "confidence": 0.0 to 1.0,
  "timeframe": "SHORT or MEDIUM or LONG",
  "reasoning": "max 400 characters explaining your decision",
  "price_target": null or float
}"""

def _fmt(val) -> str:
    """Format float values to 2 decimal places, return 'N/A' if None."""
    if val is None:
        return "N/A"
    try:
        fval = float(val)
        return f"{fval:.2f}"
    except (ValueError, TypeError):
        return str(val)

def serialize_context(ctx: dict) -> str:
    symbol = ctx.get("symbol", "N/A")
    company_name = ctx.get("company_name", "N/A")
    sector = ctx.get("sector", "N/A")
    as_of = ctx.get("as_of", "N/A")
    market_regime = ctx.get("market_regime", "N/A")
    current_price = _fmt(ctx.get("current_price"))

    tech = ctx.get("technicals", {})
    fund = ctx.get("fundamentals", {})

    # Technicals
    rsi_14 = _fmt(tech.get("rsi_14"))
    macd_line = _fmt(tech.get("macd_line"))
    macd_signal = _fmt(tech.get("macd_signal"))
    macd_hist = _fmt(tech.get("macd_hist"))
    bb_upper = _fmt(tech.get("bb_upper"))
    bb_lower = _fmt(tech.get("bb_lower"))
    ema_20 = _fmt(tech.get("ema_20"))
    ema_50 = _fmt(tech.get("ema_50"))
    ema_200 = _fmt(tech.get("ema_200"))
    atr_14 = _fmt(tech.get("atr_14"))
    volume_ratio = _fmt(tech.get("volume_ratio"))

    # Fundamentals
    pe_ratio = _fmt(fund.get("pe_ratio"))
    pb_ratio = _fmt(fund.get("pb_ratio"))
    roe = _fmt(fund.get("roe"))
    roce = _fmt(fund.get("roce"))
    debt_to_equity = _fmt(fund.get("debt_to_equity"))
    revenue_growth = _fmt(fund.get("revenue_growth"))
    profit_growth = _fmt(fund.get("profit_growth"))
    promoter_pct = _fmt(fund.get("promoter_pct"))
    fii_pct = _fmt(fund.get("fii_pct"))

    # Institutional Flows
    fii_net_cash = _fmt(ctx.get("fii_net_cash"))
    dii_net_cash = _fmt(ctx.get("dii_net_cash"))

    # News
    news_items = ctx.get("news", [])
    if news_items:
        news_str = "\\n".join([f"• {item.get('source', 'Unknown')}: {item.get('title', '')}" for item in news_items])
    else:
        news_str = "No recent news found"

    # Assemble block
    text = f"""STOCK: {symbol} | {company_name} | Sector: {sector}
DATE: {as_of}
MARKET REGIME: {market_regime}
CURRENT PRICE: ₹{current_price}

--- TECHNICAL INDICATORS ---
RSI(14): {rsi_14}
MACD Line: {macd_line} | Signal: {macd_signal} | Hist: {macd_hist}
Bollinger: Upper={bb_upper} Lower={bb_lower}
EMA: 20={ema_20} 50={ema_50} 200={ema_200}
ATR(14): {atr_14}
Volume Ratio: {volume_ratio}x (vs 20-day avg)

--- FUNDAMENTALS ---
P/E: {pe_ratio} | P/B: {pb_ratio}
ROE: {roe}% | ROCE: {roce}%
Debt/Equity: {debt_to_equity}
Revenue Growth: {revenue_growth}% | Profit Growth: {profit_growth}%
Promoter Holding: {promoter_pct}% | FII: {fii_pct}%

--- INSTITUTIONAL FLOWS (Today) ---
FII Net Cash: ₹{fii_net_cash} Cr | DII Net Cash: ₹{dii_net_cash} Cr

--- RECENT NEWS (last 48h) ---
{news_str}
"""
    return text[:4000]

def build_gemini_pro_prompt(ctx: dict) -> str:
    ctx_str = serialize_context(ctx)
    return f"""You are a senior macro analyst specializing in Indian equity markets.
Analyze the following stock data with emphasis on:
- Macroeconomic and geopolitical context
- Business quality and competitive positioning  
- Long-term fundamental strength
- Market regime implications

{ctx_str}

Based on your analysis, respond with ONLY a JSON object:
{OUTPUT_SCHEMA}

Rules: Return ONLY the JSON. No explanation outside JSON.
Direction must be exactly BUY, HOLD, or SELL.
"""

def build_gemini_flash_prompt(ctx: dict) -> str:
    ctx_str = serialize_context(ctx)
    return f"""You are a quantitative momentum analyst specializing in Indian equity markets.
Analyze the following stock data with emphasis on:
- Recent news and short-term momentum signals
- Price action and technical indicators
- Catalysts driving near-term volatility

{ctx_str}

Based on your analysis, respond with ONLY a JSON object:
{OUTPUT_SCHEMA}

Rules: Return ONLY the JSON. No explanation outside JSON.
Direction must be exactly BUY, HOLD, or SELL.
"""

def build_groq_qwen_prompt(ctx: dict) -> str:
    ctx_str = serialize_context(ctx)
    return f"""You are a purely quantitative trading algorithm processing Indian equity market data.
Analyze the following stock data with emphasis on:
Focus exclusively on the numerical data — technical indicators, price patterns, and quantitative metrics.

{ctx_str}

Based on your analysis, respond with ONLY a JSON object:
{OUTPUT_SCHEMA}

Rules: Return ONLY the JSON. No explanation outside JSON.
Direction must be exactly BUY, HOLD, or SELL.
"""

def build_groq_llama_prompt(ctx: dict) -> str:
    ctx_str = serialize_context(ctx)
    return f"""You are a value investing fundamental analyst evaluating Indian equity markets.
Analyze the following stock data with emphasis on:
Focus on fundamental value — P/E relative to growth, ROE sustainability, debt levels, and margin trends.

{ctx_str}

Based on your analysis, respond with ONLY a JSON object:
{OUTPUT_SCHEMA}

Rules: Return ONLY the JSON. No explanation outside JSON.
Direction must be exactly BUY, HOLD, or SELL.
"""

def build_groq_gpt_prompt(ctx: dict) -> str:
    ctx_str = serialize_context(ctx)
    return f"""You are a meticulous hedge fund manager in the Indian equity markets.
Analyze the following stock data. Think step by step. First assess technicals, then fundamentals, then reconcile both before deciding.

{ctx_str}

Based on your analysis, respond with ONLY a JSON object:
{OUTPUT_SCHEMA}

Rules: Return ONLY the JSON. No explanation outside JSON.
Direction must be exactly BUY, HOLD, or SELL.
"""

def build_all_prompts(ctx: dict) -> dict:
    return {
        "gemini_pro": build_gemini_pro_prompt(ctx),
        "gemini_flash": build_gemini_flash_prompt(ctx),
        "groq_qwen": build_groq_qwen_prompt(ctx),
        "groq_llama": build_groq_llama_prompt(ctx),
        "groq_gpt": build_groq_gpt_prompt(ctx)
    }
