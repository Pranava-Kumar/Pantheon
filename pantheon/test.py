import asyncio
from agents.graph import build_graph
from data.weights_store import load_weights
import uuid

async def test():
    graph = build_graph()

    state = {
        'symbol': 'WIPRO',
        'run_id': str(uuid.uuid4()),
        'market_regime': 'SIDEWAYS',
        'model_signals': [],
        'errors': [],
        'stock_context': {
            'symbol': 'WIPRO', 'company_name': 'Wipro',
            'sector': 'IT', 'market_regime': 'SIDEWAYS',
            'current_price': 190.9, 'as_of': '2026-03-22',
            'technicals': {'rsi_14': 31.1, 'macd_line': -1.2,
                           'macd_signal': -0.8, 'macd_hist': -0.4,
                           'bb_upper': 210.0, 'bb_lower': 175.0,
                           'ema_20': 195.0, 'ema_50': 200.0,
                           'ema_200': None, 'atr_14': 5.2,
                           'volume_ratio': 1.3},
            'fundamentals': {'pe_ratio': 16.7, 'roe': 17.8,
                             'roce': 23.0, 'promoter_pct': 72.64},
            'fii_net_cash': -5518.39, 'dii_net_cash': 5706.23,
            'news': [], 'news_count': 0,
            'price_summary': [], 'bulk_deals': []
        }
    }

    print('Running full MMCI pipeline...')
    result = await graph.ainvoke(state)
    signal = result['final_signal']

    print(f'Symbol:    {signal["symbol"]}')
    print(f'Direction: {signal["direction"]}')
    print(f'Score S:   {signal["consensus_score"]}')
    print(f'Dissent D: {signal["dissent_score"]}')
    print(f'Alloc:     {signal["suggested_alloc"]:.1%}')
    print(f'Risk:      {signal["risk_level"]}')
    print(f'Models:    {signal["models_used"]}')
    print(f'Regime:    {signal["market_regime"]}')
    print('PASS' if signal['direction'] in ['BUY','HOLD','SELL'] else 'FAIL')

asyncio.run(test())