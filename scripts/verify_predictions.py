import json
from datetime import datetime

fn = r'web_visualization/data/kline_simplified_data.json'
with open(fn, 'r', encoding='utf-8') as f:
    data = json.load(f)

meta = data.get('metadata', {})
seq_len = meta.get('sequence_length')
print(f'sequence_length = {seq_len}')

real = data.get('real_kline', [])
pred = data.get('predicted_kline', [])
print(f'real count = {len(real)}, pred count = {len(pred)}')

# build map timestamp -> index for real
real_index = {item['timestamp']: i for i, item in enumerate(real)}

# sample a few prediction indices: first, middle, last
sample_indices = [0, len(pred)//2, len(pred)-1]

for si in sample_indices:
    print('\n--- Sample prediction index', si, '---')
    p = pred[si]
    ts = p['timestamp']
    dt = p.get('datetime')
    print('pred timestamp:', ts, dt)
    if ts not in real_index:
        print('WARNING: pred timestamp not found in real_kline timestamps')
        continue
    idx = real_index[ts]
    print('matched real index:', idx)
    window_start_idx = idx - (seq_len - 1)
    window_end_idx = idx
    if window_start_idx < 0:
        print('Warning: window start < 0 (not enough history)')
        window_start_idx = 0
    print('input window indices:', window_start_idx, '->', window_end_idx)
    print('window start datetime:', datetime.fromtimestamp(real[window_start_idx]['timestamp']/1000).strftime('%Y-%m-%d %H:%M:%S'))
    print('window end datetime:', datetime.fromtimestamp(real[window_end_idx]['timestamp']/1000).strftime('%Y-%m-%d %H:%M:%S'))
    # compare predicted open vs real close at same idx
    pred_open = p.get('open')
    real_close = real[idx].get('close')
    pred_close = p.get('close')
    print('pred open:', pred_open, 'real close:', real_close, 'pred close:', pred_close)
    print('pred_open == real_close ?', pred_open == real_close)
    # check error field
    err = p.get('error') if 'error' in p else None
    if err is not None:
        calc_err = pred_close - real_close
        print('stored error:', err, 'calc error:', calc_err)

# summary count where pred.open == real.close
count_equal = sum(1 for p in pred if p.get('open') == real[real_index[p['timestamp']]]['close'])
print(f'pred.open == real.close for {count_equal}/{len(pred)} predictions')
