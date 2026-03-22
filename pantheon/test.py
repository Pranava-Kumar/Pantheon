import asyncio
from jobs.daily_analysis import run_daily_analysis
from db.session import SessionLocal
from db.models import SignalRecord

async def test():
    results = await run_daily_analysis(symbols=['WIPRO'])
    db = SessionLocal()
    count = db.query(SignalRecord).filter_by(symbol='WIPRO').count()
    db.close()
    print(f'Signals in DB for WIPRO: {count}')
    print(f'Direction: {results[0]["direction"]}')
    print('PASS' if count >= 1 else 'FAIL')

asyncio.run(test())