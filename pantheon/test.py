import asyncio
from extractors import get_all_extractors
from extractors.prompts import build_all_prompts

ctx = {
    'symbol': 'WIPRO', 'company_name': 'Wipro', 'sector': 'IT',
    'market_regime': 'SIDEWAYS', 'current_price': 190.9,
    'as_of': '2026-03-22',
    'technicals': {'rsi_14': 31.1, 'macd_line': -1.2, 'macd_signal': -0.8,
                   'macd_hist': -0.4, 'bb_upper': 210.0, 'bb_lower': 175.0,
                   'ema_20': 195.0, 'ema_50': 200.0, 'ema_200': None,
                   'atr_14': 5.2, 'volume_ratio': 1.3},
    'fundamentals': {'pe_ratio': 16.7, 'pb_ratio': 3.1, 'roe': 17.8,
                     'roce': 23.0, 'debt_to_equity': 0.1,
                     'revenue_growth': 5.2, 'profit_growth': 8.1,
                     'promoter_pct': 72.64, 'fii_pct': 6.2},
    'fii_net_cash': -5518.39, 'dii_net_cash': 5706.23,
    'news': [{'source': 'ET', 'title': 'Wipro wins cloud deal'}],
    'news_count': 1, 'price_summary': [], 'bulk_deals': []
}

async def test():
    extractors = get_all_extractors()
    prompts = build_all_prompts(ctx)

    tasks = [
        e.extract(prompts[e.model_id])
        for e in extractors
    ]

    print('Calling all 5 models in parallel...')
    signals = await asyncio.gather(*tasks, return_exceptions=True)

    all_pass = True
    for s in signals:
        if isinstance(s, Exception):
            print(f'EXCEPTION: {s}')
            all_pass = False
            continue
        status = 'OK' if not s.failed else 'FAILED'
        print(f'{s.model_id:15} | {s.direction:4} | conf={s.confidence:.2f} | {status} | {s.latency_ms}ms')
        if s.failed:
            print(f'  Reason: {s.failure_reason}')
            all_pass = False

    print('ALL PASS' if all_pass else 'SOME FAILURES - check above')

asyncio.run(test())