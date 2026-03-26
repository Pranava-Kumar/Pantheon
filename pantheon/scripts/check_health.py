import sys
import os
from pathlib import Path

# Add project root to sys.path so we can run from anywhere
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from sqlalchemy import text
from pantheon.config.settings import settings


def main():
    print("Running System Health Checks...\n")
    passed = 0
    total = 7

    # CHECK 1 — Database
    try:
        from pantheon.db.session import SessionLocal, init_db
        init_db()
        db = SessionLocal()
        db.execute(text("SELECT 1"))
        db.close()
        print("[OK] Database — PostgreSQL (Neon) connected")
        passed += 1
    except Exception as e:
        print(f"[FAIL] Database — {e}")

    # CHECK 2 — Gemini API
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash", 
            google_api_key=settings.GOOGLE_API_KEY, 
            max_output_tokens=5
        )
        res = llm.invoke("Hi")
        if res and res.content:
            print(f"[OK] Gemini API — reachable")
            passed += 1
        else:
            print("[FAIL] Gemini API — empty response")
    except Exception as e:
        print(f"[FAIL] Gemini API — {e}")

    # CHECK 3 — Groq API
    try:
        from openai import OpenAI
        client = OpenAI(
            api_key=settings.GROQ_API_KEY,
            base_url="https://api.groq.com/openai/v1"
        )
        models = client.models.list()
        print("[OK] Groq API — reachable")
        passed += 1
    except Exception as e:
        print(f"[FAIL] Groq API — {e}")

    # CHECK 4 — NSE API
    try:
        from pantheon.data.nse_client import NSEClient
        nse = NSEClient()
        status = nse.get_market_status()
        print(f"[OK] NSE API — market is {status}")
        passed += 1
    except Exception as e:
        print(f"[FAIL] NSE API — {e}")

    # CHECK 5 — Screener.in
    try:
        from pantheon.data.screener_client import ScreenerClient
        client = ScreenerClient(settings.SCREENER_EMAIL, settings.SCREENER_PASSWORD)
        if getattr(client, "_logged_in", False):
            print("[OK] Screener.in — logged in")
            passed += 1
        else:
            print("[FAIL] Screener.in — not logged in")
    except Exception as e:
        print(f"[FAIL] Screener.in — {e}")

    # CHECK 6 — yfinance
    try:
        import yfinance as yf
        ticker = yf.Ticker("WIPRO.NS")
        price = ticker.fast_info.last_price
        print(f"[OK] yfinance — WIPRO last price ₹{price:.2f}")
        passed += 1
    except Exception as e:
        print(f"[FAIL] yfinance — {e}")

    # CHECK 7 — LangSmith
    try:
        key = getattr(settings, "LANGSMITH_API_KEY", getattr(settings, "LANGCHAIN_API_KEY", ""))
        if key and len(str(key)) > 10:
            print("[OK] LangSmith — API key configured")
            passed += 1
        else:
            print("[WARN] LangSmith — API key missing, tracing disabled")
            # Warnings do not block pipeline execution
            passed += 1
    except Exception as e:
        print(f"[FAIL] LangSmith — {e}")

    print("\nSYSTEM HEALTH: {}/{} checks passed".format(passed, total))
    if passed == total:
        print("✅ Ready to run analysis")
    else:
        print("⚠ Fix failing checks before running analysis")

if __name__ == "__main__":
    main()
