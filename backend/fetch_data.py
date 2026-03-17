"""
Market Scanner - Data Fetcher  (Hybrid Edition)
=====================================================
Uses a hybrid approach for maximum free-tier coverage:
  - Polygon/Massive API (free tier): Stock list, prices, basic info
  - Yahoo Finance (yfinance): Financial metrics, fundamentals

Install:
    pip install -U massive yfinance python-dotenv requests

.env:
    MASSIVE_API_KEY=your_key_here
    FRED_API_KEY=your_key_here
    MAX_TICKERS=5000
    REQUEST_DELAY=0.5      # 可选: 请求间隔(秒), 默认 0.5
    MAX_RETRIES=3          # 可选: 429错误最大重试次数, 默认 3

Rate Limiting:
    - Polygon free tier: ~5 requests/minute (used for prices only)
    - Yahoo Finance: No official limit, but be respectful (~1-2 req/sec)
    - Current setting: 0.5s delay = ~2 req/sec (safe for both)

Outputs: ../frontend/data/market.json
"""

import os
import json
import time
import requests
import warnings
from datetime import datetime
from dotenv import load_dotenv

# 抑制 urllib3 的 OpenSSL 警告（macOS LibreSSL 兼容性问题）
warnings.filterwarnings('ignore', message='.*urllib3 v2.*')

# Official Massive SDK — pip install massive
from massive import RESTClient
# Yahoo Finance — pip install yfinance
import yfinance as yf

load_dotenv()

MASSIVE_API_KEY = os.getenv("MASSIVE_API_KEY") or os.getenv("POLYGON_API_KEY", "")
FRED_API_KEY    = os.getenv("FRED_API_KEY", "")
MAX_TICKERS     = int(os.getenv("MAX_TICKERS", "5000"))
MIN_MARKET_CAP  = 500_000_000   # skip < $500M market cap — 改这里可调整门槛
OUTPUT_PATH     = os.path.join(os.path.dirname(__file__), "../frontend/data/market.json")

# Rate limiting settings (可在 .env 中覆盖)
# yfinance 需要更保守的速率限制
REQUEST_DELAY   = float(os.getenv("REQUEST_DELAY", "1.5"))  # 默认 1.5 秒（更安全）
MAX_RETRIES     = int(os.getenv("MAX_RETRIES", "5"))        # 增加重试次数
BACKOFF_FACTOR  = 2                                          # 指数退避因子

# SDK client — handles Bearer auth + base URL automatically
client = RESTClient(api_key=MASSIVE_API_KEY)


# ═══════════════════════════════════════════════════════
# RETRY HELPER WITH EXPONENTIAL BACKOFF
# ═══════════════════════════════════════════════════════

def retry_with_backoff(func, *args, **kwargs):
    """
    执行函数，如果遇到 429 错误则使用指数退避重试
    """
    for attempt in range(MAX_RETRIES):
        try:
            return func(*args, **kwargs)
        except Exception as e:
            error_msg = str(e)
            # 检查是否是 429 错误
            if '429' in error_msg or 'too many' in error_msg.lower():
                if attempt < MAX_RETRIES - 1:
                    wait_time = REQUEST_DELAY * (BACKOFF_FACTOR ** attempt)
                    print(f"    ⚠️  Rate limit hit, waiting {wait_time:.1f}s...")
                    time.sleep(wait_time)
                    continue
            # 其他错误或最后一次重试失败，抛出异常
            raise
    raise Exception(f"Max retries ({MAX_RETRIES}) exceeded")

def get_yfinance_data_safe(symbol):
    """
    安全获取 yfinance 数据，带重试和速率限制处理
    """
    import random
    
    for attempt in range(MAX_RETRIES):
        try:
            # 添加随机延迟避免模式识别 (0-0.5秒)
            jitter = random.uniform(0, 0.5)
            time.sleep(jitter)
            
            # 使用更宽松的超时设置
            ticker_obj = yf.Ticker(symbol)
            
            # 尝试多次获取 info，处理连接问题
            info = None
            for info_attempt in range(3):
                try:
                    info = ticker_obj.info
                    if info and len(info) > 5:
                        break
                    time.sleep(1)  # 短暂等待后重试
                except Exception as e:
                    if info_attempt < 2:
                        time.sleep(1)
                        continue
                    raise
            
            # 验证数据有效性
            if not info or len(info) < 5:
                if attempt < MAX_RETRIES - 1:
                    time.sleep(REQUEST_DELAY * (attempt + 1))
                    continue
                return None, None
            
            return ticker_obj, info
            
        except Exception as e:
            error_msg = str(e).lower()
            
            # 检查错误类型
            is_rate_limit = 'rate limit' in error_msg or 'too many' in error_msg or '429' in error_msg
            is_connection = 'connection' in error_msg or 'timeout' in error_msg or 'closed' in error_msg
            
            # 速率限制错误
            if is_rate_limit:
                if attempt < MAX_RETRIES - 1:
                    wait_time = REQUEST_DELAY * (BACKOFF_FACTOR ** (attempt + 1))
                    if attempt == 0:
                        print(f"    ⚠️  Yahoo Finance rate limit, slowing down...")
                    time.sleep(wait_time)
                    continue
                else:
                    return None, None
            
            # 连接错误 - 更激进的重试
            elif is_connection:
                if attempt < MAX_RETRIES - 1:
                    wait_time = 2 + (attempt * 2)  # 2秒, 4秒, 6秒...
                    if attempt == 0:
                        print(f"    ⚠️  Connection issue, retrying...")
                    time.sleep(wait_time)
                    continue
                else:
                    return None, None
            
            # 其他错误（如股票不存在）
            else:
                if attempt < 2:  # 轻微重试
                    time.sleep(REQUEST_DELAY)
                    continue
                return None, None
    
    return None, None


# ═══════════════════════════════════════════════════════
# 1. MACRO DATA  (FRED — still uses requests, free API)
# ═══════════════════════════════════════════════════════

FRED_SERIES = {
    "fed_funds_rate":  "FEDFUNDS",        # already a rate — use as-is
    "cpi_yoy":         None,              # computed below from CPIAUCSL
    "unemployment":    "UNRATE",
    "gdp_growth":      "A191RL1Q225SBEA", # already a % change series
    "10y_treasury":    "GS10",
    "2y_treasury":     "GS2",
    "yield_curve":     None,              # computed: 10y − 2y
    "m2_money_supply": "M2SL",
    "pce_inflation":   None,              # computed below from PCEPI
    "vix":             "VIXCLS",
}

def _fred_obs(series_id, limit=14):
    r = requests.get(
        "https://api.stlouisfed.org/fred/series/observations",
        params={"series_id": series_id, "api_key": FRED_API_KEY,
                "file_type": "json", "sort_order": "desc", "limit": limit},
        timeout=10,
    )
    r.raise_for_status()
    return [o for o in r.json().get("observations", []) if o["value"] != "."]

def fetch_macro():
    print("📊 Fetching macro from FRED...")
    macro = {}

    for key, sid in FRED_SERIES.items():
        if sid is None:
            continue
        try:
            obs = _fred_obs(sid, limit=3)
            if not obs:
                continue
            latest = float(obs[0]["value"])
            prev   = float(obs[1]["value"]) if len(obs) > 1 else latest
            macro[key] = {
                "value":  round(latest, 2),
                "prev":   round(prev, 2),
                "change": round(latest - prev, 2),
                "date":   obs[0]["date"],
            }
            print(f"  ✓ {key}: {latest}")
            time.sleep(0.25)
        except Exception as e:
            print(f"  ✗ {key}: {e}")
            macro[key] = {"value": None, "prev": None, "change": None, "date": None}

    # CPI → true YoY %  (CPIAUCSL is an index, not a rate)
    try:
        obs = _fred_obs("CPIAUCSL", limit=14)
        if len(obs) >= 13:
            yoy      = round((float(obs[0]["value"]) / float(obs[12]["value"]) - 1) * 100, 2)
            yoy_prev = round((float(obs[1]["value"]) / float(obs[13]["value"]) - 1) * 100, 2) if len(obs) >= 14 else yoy
            macro["cpi_yoy"] = {
                "value": yoy, "prev": yoy_prev,
                "change": round(yoy - yoy_prev, 2), "date": obs[0]["date"],
            }
            print(f"  ✓ cpi_yoy: {yoy}%")
    except Exception as e:
        print(f"  ✗ CPI YoY: {e}")

    # PCE inflation → true YoY %  (PCEPI is also an index)
    try:
        obs = _fred_obs("PCEPI", limit=14)
        if len(obs) >= 13:
            yoy      = round((float(obs[0]["value"]) / float(obs[12]["value"]) - 1) * 100, 2)
            yoy_prev = round((float(obs[1]["value"]) / float(obs[13]["value"]) - 1) * 100, 2) if len(obs) >= 14 else yoy
            macro["pce_inflation"] = {
                "value": yoy, "prev": yoy_prev,
                "change": round(yoy - yoy_prev, 2), "date": obs[0]["date"],
            }
            print(f"  ✓ pce_inflation: {yoy}%")
    except Exception as e:
        print(f"  ✗ PCE YoY: {e}")

    # Yield curve spread
    t10 = macro.get("10y_treasury", {}).get("value")
    t2  = macro.get("2y_treasury",  {}).get("value")
    if t10 and t2:
        macro["yield_curve"] = {
            "value": round(t10 - t2, 2), "prev": None, "change": None,
            "date":  macro["10y_treasury"]["date"],
        }

    return macro


# ═══════════════════════════════════════════════════════
# 2. SECTOR NORMALIZATION
# ═══════════════════════════════════════════════════════

SECTOR_ORDER = [
    "Technology", "Healthcare", "Financials", "Consumer Discretionary",
    "Communication Services", "Industrials", "Consumer Staples", "Energy",
    "Utilities", "Real Estate", "Materials", "Other",
]

_SECTOR_KEYWORDS = {
    "Technology":              ["software", "semiconductor", "tech", "computer", "cloud",
                                 "cyber", "data", "internet", "electronics", "hardware"],
    "Healthcare":              ["pharma", "biotech", "medical", "health", "therapeutics",
                                 "diagnostics", "hospital", "drug", "life science"],
    "Financials":              ["bank", "insurance", "financial", "capital", "invest",
                                 "credit", "asset management", "lending", "brokerage"],
    "Energy":                  ["oil", "gas", "petroleum", "energy", "mining", "drilling", "refin"],
    "Consumer Discretionary":  ["retail", "automobile", "restaurant", "hotel", "apparel",
                                 "entertainment", "leisure", "gaming"],
    "Consumer Staples":        ["food", "beverage", "grocery", "tobacco", "household",
                                 "personal care"],
    "Industrials":             ["aerospace", "defense", "industrial", "machinery",
                                 "construction", "transport", "logistics"],
    "Materials":               ["chemical", "material", "steel", "aluminum", "paper",
                                 "packaging"],
    "Communication Services":  ["telecom", "media", "broadcasting", "wireless", "cable",
                                 "social", "streaming"],
    "Utilities":               ["utility", "electric", "water", "gas distribution"],
    "Real Estate":             ["reit", "real estate", "property", "mortgage"],
}

def normalize_sector(raw):
    if not raw:
        return "Other"
    s = raw.lower()
    for sector, kws in _SECTOR_KEYWORDS.items():
        if any(kw in s for kw in kws):
            return sector
    for std in SECTOR_ORDER:
        if std.lower() in s:
            return std
    return "Other"


# ═══════════════════════════════════════════════════════
# 3. FINANCIAL METRICS FROM YFINANCE
# ═══════════════════════════════════════════════════════

def safe_get(data, *keys):
    """安全获取嵌套字典的值"""
    for key in keys:
        if data is None:
            return None
        if isinstance(data, dict):
            data = data.get(key)
        else:
            return None
    return data

def compute_metrics_from_yfinance(ticker_obj, market_cap):
    metrics = {}
    
    try:
        info = ticker_obj.info

        # ── 基础财务数值（后面计算用）──────────────────
        ebitda       = info.get("ebitda")
        total_debt   = info.get("totalDebt") or 0
        total_cash   = info.get("totalCash") or 0
        op_income    = info.get("operatingIncome") or info.get("ebit")
        int_expense  = info.get("interestExpense")   # yfinance 返回负数
        revenue      = info.get("totalRevenue")
        fcf          = info.get("freeCashflow")
        net_income   = info.get("netIncomeToCommon")
        total_equity = info.get("totalStockholderEquity") or info.get("bookValue")
        total_assets = info.get("totalAssets")
        ev           = info.get("enterpriseValue")
        shares       = info.get("sharesOutstanding")

        # bookValue 在 yfinance 有时是每股值，需乘股数
        if total_equity and shares and total_equity < 1e8:
            total_equity = total_equity * shares

        # ── 估值 ──────────────────────────────────────
        metrics["pe"]       = round(info.get("trailingPE") or info.get("forwardPE"), 2) if (info.get("trailingPE") or info.get("forwardPE")) else None
        metrics["ps_ratio"] = round(info.get("priceToSalesTrailing12Months"), 2) if info.get("priceToSalesTrailing12Months") else None
        metrics["pb_ratio"] = round(info.get("priceToBook"), 2) if info.get("priceToBook") else None

        # EV/EBITDA — yfinance 直接有
        metrics["ev_ebitda"] = round(info.get("enterpriseToEbitda"), 2) if info.get("enterpriseToEbitda") else None

        # EV/EBIT — 需要计算：enterpriseValue / operatingIncome
        if ev and op_income and op_income > 0:
            metrics["ev_ebit"] = round(ev / op_income, 2)
        else:
            metrics["ev_ebit"] = None

        # ── 利润率 ──────────────────────────────────
        metrics["gross_margin"]     = round(info.get("grossMargins")    * 100, 2) if info.get("grossMargins")    else None
        metrics["operating_margin"] = round(info.get("operatingMargins") * 100, 2) if info.get("operatingMargins") else None
        metrics["net_margin"]       = round(info.get("profitMargins")   * 100, 2) if info.get("profitMargins")   else None

        # FCF Yield & FCF Margin
        if fcf and market_cap and market_cap > 0:
            metrics["fcf_yield"]  = round((fcf / market_cap) * 100, 2)
        else:
            metrics["fcf_yield"]  = None
        metrics["fcf_margin"] = round((fcf / revenue) * 100, 2) if (fcf and revenue and revenue > 0) else None

        # ── 回报率 ──────────────────────────────────
        metrics["roe"] = round(info.get("returnOnEquity") * 100, 2) if info.get("returnOnEquity") else None
        metrics["roa"] = round(info.get("returnOnAssets") * 100, 2) if info.get("returnOnAssets") else None

        # ROIC = EBIT * (1 - 税率) / 投入资本
        # 投入资本 = 股东权益 + 有息负债 - 现金
        tax_rate     = info.get("effectiveTaxRate") or 0.21
        invested_cap = (total_equity or 0) + total_debt - total_cash
        if op_income and invested_cap and invested_cap > 0:
            metrics["roic"] = round((op_income * (1 - tax_rate) / invested_cap) * 100, 2)
        else:
            metrics["roic"] = None

        # ── 杠杆 ────────────────────────────────────
        # Debt/EBITDA — yfinance 无直接字段，手动算
        if total_debt and ebitda and ebitda > 0:
            metrics["debt_ebitda"] = round(total_debt / ebitda, 2)
        else:
            metrics["debt_ebitda"] = None

        # Net Debt/EBITDA
        net_debt = total_debt - total_cash
        metrics["net_debt_ebitda"] = round(net_debt / ebitda, 2) if (ebitda and ebitda > 0) else None

        metrics["debt_equity"] = round(info.get("debtToEquity") / 100, 2) if info.get("debtToEquity") else None

        # Interest Coverage = EBIT / |利息支出|
        # yfinance interestExpense 通常为负数（支出）
        if op_income and int_expense and int_expense != 0:
            metrics["interest_coverage"] = round(op_income / abs(int_expense), 2)
        else:
            metrics["interest_coverage"] = None

        # ── 增长率 ──────────────────────────────────
        metrics["revenue_cagr"] = round(info.get("revenueGrowth")  * 100, 2) if info.get("revenueGrowth")  else None
        metrics["eps_cagr"]     = round(info.get("earningsGrowth") * 100, 2) if info.get("earningsGrowth") else None

        # ── 原始财务数据（百万美元）──────────────────
        metrics["revenue_ttm"]    = round(revenue   / 1e6, 1) if revenue   else None
        metrics["ebitda_ttm"]     = round(ebitda    / 1e6, 1) if ebitda    else None
        metrics["fcf_ttm"]        = round(fcf       / 1e6, 1) if fcf       else None
        metrics["net_income_ttm"] = round(net_income / 1e6, 1) if net_income else None
        metrics["eps"]            = info.get("trailingEps")
        metrics["shares_outstanding"] = round(shares / 1e6, 1) if shares else None

    except Exception as e:
        pass

    return metrics


# ═══════════════════════════════════════════════════════
# 4. PER-TICKER PIPELINE  (SDK calls, Bearer auth auto)
# ═══════════════════════════════════════════════════════

def process_ticker(symbol):
    try:
        # ── 快速市值检查（再次确认，防止 fast_info 误判漏网） ──
        try:
            mcap_quick = getattr(yf.Ticker(symbol).fast_info, "market_cap", None)
            if mcap_quick is not None and mcap_quick < MIN_MARKET_CAP:
                return None
        except Exception:
            pass  # fast_info 失败则继续走完整流程

        # ── Reference / company details (Polygon - 免费) ──
        ref        = retry_with_backoff(client.get_ticker_details, symbol)
        name       = getattr(ref, "name", symbol)
        sic_desc   = getattr(ref, "sic_description", None)
        exchange   = getattr(ref, "primary_exchange", None)
        sector     = normalize_sector(sic_desc)

        # ── 所有数据从 Yahoo Finance 获取 ─────────────
        ticker_obj, info = get_yfinance_data_safe(symbol)
        
        if not info:
            # yfinance 完全失败 - 使用 Polygon 的基本数据
            market_cap = getattr(ref, "market_cap", None)
            if market_cap and market_cap < MIN_MARKET_CAP:
                return None
            
            return {
                "ticker":       symbol,
                "name":         name,
                "sector":       sector,
                "exchange":     exchange,
                "market_cap":   market_cap,
                "market_cap_b": round(market_cap / 1e9, 2) if market_cap else None,
                "price":        None,
                "change_pct":   None,
                "volume":       None,
            }
        
        # 成功获取 yfinance 数据
        market_cap = info.get("marketCap")
        price      = info.get("currentPrice") or info.get("regularMarketPrice")
        prev_close = info.get("previousClose")
        volume     = info.get("volume")
        
        # 补充名称和行业信息
        if not name or name == symbol:
            name = info.get("longName") or info.get("shortName") or symbol
        
        if not sector or sector == "Other":
            yf_sector = info.get("sector")
            if yf_sector:
                sector = normalize_sector(yf_sector)
        
        # 市值过滤
        if market_cap and market_cap < MIN_MARKET_CAP:
            return None
        
        # 计算涨跌幅
        change_pct = None
        if price and prev_close and prev_close > 0:
            change_pct = round((price / prev_close - 1) * 100, 2)
        
        # 获取财务指标
        metrics = compute_metrics_from_yfinance(ticker_obj, market_cap) if market_cap else {}
        
        return {
            "ticker":       symbol,
            "name":         name,
            "sector":       sector,
            "exchange":     exchange,
            "market_cap":   market_cap,
            "market_cap_b": round(market_cap / 1e9, 2) if market_cap else None,
            "price":        round(price, 2) if price else None,
            "change_pct":   change_pct,
            "volume":       volume,
            **metrics,
        }

    except Exception as e:
        print(f"  ✗ {symbol}: {e}")
        return None


# ═══════════════════════════════════════════════════════
# 5. MAIN PIPELINE
# ═══════════════════════════════════════════════════════

def build_market_data():
    print("\n🚀 Market Scanner — Data Fetch (Pure yfinance Mode)\n" + "=" * 50)
    print(f"📊 Data Sources:")
    print(f"   - Polygon API (free): Stock list, company names")
    print(f"   - Yahoo Finance: All prices & financial metrics")
    print(f"⚙️  Rate limit: {1/REQUEST_DELAY:.1f} req/sec  |  Delay: {REQUEST_DELAY}s  |  Retries: {MAX_RETRIES}")
    print(f"⚠️  Yahoo Finance has strict rate limits - be patient!")
    print(f"💡 If you hit rate limits, increase REQUEST_DELAY in .env\n")

    # ── Macro ──────────────────────────────────────────
    macro = fetch_macro()

    # ── Ticker list (SDK iterator, auto-paginates) ─────
    print("\n📋 Fetching ticker list...")
    symbols = []
    try:
        # 修复: 移除 params 参数,直接传递参数给 list_tickers
        for t in client.list_tickers(
            market="stocks",
            type="CS",        # Common Stock only
            active=True,
            limit=1000,       # page size
        ):
            sym = getattr(t, "ticker", None)
            if sym:
                # 可选: 如果需要过滤特定交易所,在这里添加过滤逻辑
                exchange = getattr(t, "primary_exchange", "")
                if exchange in ["XNAS", "XNYS", "XASE"]:
                    symbols.append(sym)
                else:
                    symbols.append(sym)  # 或者注释这行以仅保留特定交易所
            if len(symbols) >= MAX_TICKERS:
                break
    except Exception as e:
        print(f"  Ticker list error: {e}")

    print(f"✅ {len(symbols)} tickers queued")

    # ── Phase 1: 批量预过滤市值 ────────────────────────
    # 用 yf.fast_info（比 .info 快 ~10x）批量检查市值，提前丢掉不合格的
    # 避免对数千只小市值股票浪费 yfinance .info 请求
    print(f"\n🔍 Pre-filtering by market cap ≥ ${MIN_MARKET_CAP/1e9:.1f}B ...")
    qualified_symbols = []
    batch_size = 100
    for i in range(0, len(symbols), batch_size):
        batch = symbols[i : i + batch_size]
        try:
            tickers_obj = yf.Tickers(" ".join(batch))
            for sym in batch:
                try:
                    mcap = getattr(tickers_obj.tickers[sym].fast_info, "market_cap", None)
                    if mcap and mcap >= MIN_MARKET_CAP:
                        qualified_symbols.append(sym)
                except Exception:
                    # fast_info 失败时保留，让后续 process_ticker 再判断
                    qualified_symbols.append(sym)
            time.sleep(0.3)
        except Exception as e:
            # 整批失败时全部保留，不丢数据
            qualified_symbols.extend(batch)
            time.sleep(1)
        if (i // batch_size + 1) % 10 == 0:
            print(f"  Pre-filter: checked {i + len(batch)}/{len(symbols)}, "
                  f"qualified so far: {len(qualified_symbols)}")

    print(f"✅ Pre-filter done: {len(qualified_symbols)}/{len(symbols)} stocks pass ≥${MIN_MARKET_CAP/1e9:.1f}B\n")
    symbols = qualified_symbols

    # ── Process tickers ────────────────────────────────
    est_time_min = (len(symbols) * REQUEST_DELAY) / 60
    print(f"\n⚙️  Processing {len(symbols)} tickers...")
    print(f"   Rate: {1/REQUEST_DELAY:.1f} req/sec  |  Est. time: {est_time_min:.1f} min\n")
    
    stocks, failed = [], 0
    start_time = time.time()

    for i, symbol in enumerate(symbols):
        if i % 50 == 0 and i > 0:  # 更频繁的进度更新
            elapsed = time.time() - start_time
            rate = i / elapsed if elapsed > 0 else 0
            remaining = (len(symbols) - i) / rate if rate > 0 else 0
            print(f"  [{i}/{len(symbols)}]  valid={len(stocks)}  |  {rate:.1f} tick/sec  |  ETA: {remaining/60:.1f} min")

        result = process_ticker(symbol)
        if result:
            stocks.append(result)
        else:
            failed += 1

        time.sleep(REQUEST_DELAY)   # 使用配置的延迟时间

    print(f"\n✅ {len(stocks)} valid  |  {failed} skipped")

    # ── Group by sector, sort by market cap ────────────
    sectors = {}
    for s in stocks:
        sec = s.get("sector", "Other")
        sectors.setdefault(sec, []).append(s)
    for sec in sectors:
        sectors[sec].sort(key=lambda x: x.get("market_cap") or 0, reverse=True)

    # ── Summary ────────────────────────────────────────
    total_mcap = sum(s.get("market_cap") or 0 for s in stocks)
    now = datetime.utcnow().isoformat() + "Z"
    summary = {
        "total_stocks":       len(stocks),
        "total_market_cap_t": round(total_mcap / 1e12, 2),
        "sectors":            len(sectors),
        "last_updated":       now,
    }

    # ── Assemble output ────────────────────────────────
    output = {
        "meta":    {"generated_at": now, "version": "1.1"},
        "summary": summary,
        "macro":   macro,
        "sectors": {sec: sectors[sec] for sec in SECTOR_ORDER if sec in sectors},
    }
    for sec in sectors:   # append any non-standard sectors
        if sec not in output["sectors"]:
            output["sectors"][sec] = sectors[sec]

    # ── Write JSON ─────────────────────────────────────
    os.makedirs(os.path.dirname(OUTPUT_PATH), exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        json.dump(output, f, separators=(",", ":"))

    size_mb = os.path.getsize(OUTPUT_PATH) / 1e6
    print(f"\n✅ Written → {OUTPUT_PATH}  ({size_mb:.1f} MB)")
    print(f"   Stocks: {summary['total_stocks']}  |  MCap: ${summary['total_market_cap_t']}T")
    print(f"   Generated: {now}")


if __name__ == "__main__":
    build_market_data()
