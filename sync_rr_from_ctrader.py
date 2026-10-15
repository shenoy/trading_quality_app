"""Set each trade's R:R from the real cTrader Net $ so risk x R:R == actual P&L.

Usage:  python sync_rr_from_ctrader.py path/to/database.db path/to/ctrader.xlsx [--apply]
Without --apply it only reports what would change (dry run).
Trades are matched by symbol + closing time (within 10 minutes, nearest first).
"""
import sqlite3, sys, datetime as dt, shutil
import openpyxl

db, xlsx = sys.argv[1], sys.argv[2]
apply = '--apply' in sys.argv

ws = openpyxl.load_workbook(xlsx, data_only=True).active
ct = []
for r in list(ws.iter_rows(values_only=True))[1:]:
    if not r[0]:
        continue
    t = r[2] if isinstance(r[2], dt.datetime) else dt.datetime.strptime(str(r[2])[:19], '%d/%m/%Y %H:%M:%S')
    ct.append({'sym': r[0], 't': t, 'net': float(r[7])})

con = sqlite3.connect(db)
con.row_factory = sqlite3.Row
trades = [dict(r) for r in con.execute('select id, ticker, entry_datetime, exit_datetime, risk_str, risk_reward_str from trade')]
parse = lambda s: dt.datetime.fromisoformat(s.replace(' ', 'T')) if s else None
used, changes, unmatched = set(), [], []
for tr in sorted(trades, key=lambda x: x['exit_datetime'] or x['entry_datetime']):
    ref = parse(tr['exit_datetime']) or parse(tr['entry_datetime'])
    best = None
    for i, c in enumerate(ct):
        if i in used or c['sym'] != tr['ticker']:
            continue
        d = abs((c['t'] - ref).total_seconds())
        if d <= 600 and (best is None or d < best[0]):
            best = (d, i)
    if not best:
        unmatched.append(tr); continue
    used.add(best[1])
    risk = float(tr['risk_str'] or 0)
    old = risk * float(tr['risk_reward_str'] or 0)
    net = ct[best[1]]['net']
    if risk and abs(old - net) > 1:
        changes.append((tr['id'], tr['ticker'], round(old, 2), net, round(net / risk, 4)))

print(f'{len(changes)} trades differ from cTrader by more than $1')
for c in changes:
    print('  id %s %s: app %s -> cTrader %s  (new R:R %s)' % c)
print('not in cTrader (left unchanged):', [(t['id'], t['ticker']) for t in unmatched])
print('cTrader rows with no app trade:', [(ct[i]['sym'], str(ct[i]['t']), ct[i]['net']) for i in range(len(ct)) if i not in used])

if apply:
    shutil.copy(db, db + '.bak')
    for id_, _, _, _, rr in changes:
        con.execute('update trade set risk_reward_str=? where id=?', (str(rr), id_))
    con.commit()
    print('Applied. Backup saved as', db + '.bak')
