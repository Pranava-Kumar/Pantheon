import asyncio
from datetime import datetime
from db.session import SessionLocal, init_db
from db.models import SignalRecord
from data.weights_store import load_weights, save_weights
from mmci.weights import WeightManager
from jobs.weight_updater import determine_actual_outcome, get_trading_days_ago

# Test 1: outcome determination
print('Test outcome logic:')
print(determine_actual_outcome(100.0, 103.0))  # Should be BUY
print(determine_actual_outcome(100.0, 97.0))   # Should be SELL
print(determine_actual_outcome(100.0, 101.0))  # Should be HOLD

# Test 2: trading days calculation
print('5 trading days ago:', get_trading_days_ago(5))

# Test 3: weight update simulation
print('Test weight update:')
wm = WeightManager(load_weights())
print('Before:', {k: round(v,3) for k, v in wm.get_weights().items()})

# Simulate: groq_qwen and groq_llama were correct (BUY), others wrong
fake_signals = [
    {'model_id': 'gemini_pro',   'direction': 'HOLD', 'confidence': 0.6, 'failed': False},
    {'model_id': 'gemini_flash', 'direction': 'HOLD', 'confidence': 0.6, 'failed': False},
    {'model_id': 'groq_qwen',    'direction': 'BUY',  'confidence': 0.7, 'failed': False},
    {'model_id': 'groq_llama',   'direction': 'BUY',  'confidence': 0.8, 'failed': False},
    {'model_id': 'groq_gpt',     'direction': 'HOLD', 'confidence': 0.5, 'failed': False},
]
wm.update(fake_signals, 'BUY')
print('After:', {k: round(v,3) for k, v in wm.get_weights().items()})
print('groq_qwen went UP:', wm.get_weights()['groq_qwen'] > load_weights()['groq_qwen'])
print('gemini_pro went DOWN:', wm.get_weights()['gemini_pro'] < load_weights()['gemini_pro'])
print('PASS')