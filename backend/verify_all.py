"""Full verification script for Colosseum. Starts server internally."""
import http.client, json, time, os, sys, threading, subprocess

os.environ['MARKET_SOURCE'] = 'mock'
os.environ['PORT'] = '8787'

# Start server in subprocess
server = subprocess.Popen(
    [sys.executable, '-m', 'app.main'],
    cwd=os.path.dirname(os.path.abspath(__file__)),
    env={**os.environ},
    stdout=subprocess.PIPE, stderr=subprocess.STDOUT
)

def drain():
    for line in server.stdout:
        pass
threading.Thread(target=drain, daemon=True).start()

time.sleep(4)

def req(method, path, body=None, headers=None):
    conn = http.client.HTTPConnection('127.0.0.1', 8787, timeout=10)
    h = {'Content-Type': 'application/json'}
    if headers:
        h.update(headers)
    conn.request(method, path, json.dumps(body) if body else None, h)
    r = conn.getresponse()
    data = r.read().decode()
    conn.close()
    try:
        return r.status, json.loads(data) if data else {}
    except:
        return r.status, {"raw": data[:200]}

results = {}

try:
    # 1. Health
    s, d = req('GET', '/health')
    results['backend_health'] = 'PASS' if s == 200 else 'FAIL'
    print(f"1. Health: {s} -> {results['backend_health']}")

    # 2. Create tournament
    now = time.time()
    s, t = req('POST', '/tournaments', {
        'name': 'Verification Arena', 'leverage': 15,
        'startAt': now + 120, 'endAt': now + 3600
    })
    tid = t.get('id', '')
    results['create_tournament'] = 'PASS' if s == 200 and tid else 'FAIL'
    print(f"2. Create tournament: {s} id={tid} -> {results['create_tournament']}")

    # 3. Scheduled
    s, timer = req('GET', f'/tournaments/{tid}/timer')
    results['scheduled_start'] = 'PASS' if s == 200 and timer.get('effectiveStatus') == 'scheduled' else 'FAIL'
    print(f"3. Scheduled: {timer.get('effectiveStatus')} -> {results['scheduled_start']}")

    # 4. Register agent via API BEFORE starting
    s, reg = req('POST', '/agent-api/v1/register', {'agentId': 'lev-test', 'name': 'Leverage Tester'})
    api_key = reg.get('api_key', '')
    auth = {'Authorization': f'Bearer {api_key}'}
    s, jd = req('POST', f'/agent-api/v1/tournaments/{tid}/join', {'name': 'Leverage Tester'}, auth)
    results['register_agent'] = 'PASS' if s == 200 else f'FAIL({s}:{jd})'
    print(f"4. Register+Join: {s} -> {results['register_agent']}")

    # 5. Force start
    s, d = req('POST', f'/tournaments/{tid}/status', {'status': 'running'})
    eff = d.get('effectiveStatus', '')
    results['force_start'] = 'PASS' if s == 200 and eff == 'running' else 'FAIL'
    print(f"5. Force start: {eff} -> {results['force_start']}")

    # 6. Start test agent
    s, ta = req('POST', '/test-agent/start', {'tournamentId': tid})
    taId = ta.get('agentId', '')
    results['test_agent_start'] = 'PASS' if s == 200 and taId else 'FAIL'
    print(f"6. Test agent start: id={taId} -> {results['test_agent_start']}")

    # 7. Signal with leverage=3
    s, sig = req('POST', '/agent-api/v1/signal', {
        'tournamentId': tid, 'symbol': 'BTCUSDT', 'side': 'buy', 'qty': 0.05, 'leverage': 3.0
    }, auth)
    ev_lev = sig.get('event', {}).get('detail', {}).get('leverage')
    results['custom_leverage'] = 'PASS' if s == 200 and ev_lev == 3.0 else f'FAIL(s={s},lev={ev_lev})'
    print(f"7. Custom leverage=3: lev={ev_lev} -> {results['custom_leverage']}")

    # 8. Leverage clamp
    s, sig2 = req('POST', '/agent-api/v1/signal', {
        'tournamentId': tid, 'symbol': 'ETHUSDT', 'side': 'sell', 'qty': 0.1, 'leverage': 20.0
    }, auth)
    ev_lev2 = sig2.get('event', {}).get('detail', {}).get('leverage')
    results['leverage_clamp'] = 'PASS' if s == 200 and ev_lev2 == 15.0 else f'FAIL(s={s},lev={ev_lev2})'
    print(f"8. Leverage clamp 20->15: lev={ev_lev2} -> {results['leverage_clamp']}")

    # 9. Default leverage
    s, sig3 = req('POST', '/agent-api/v1/signal', {
        'tournamentId': tid, 'symbol': 'AVAXUSDT', 'side': 'buy', 'qty': 0.5
    }, auth)
    ev_lev3 = sig3.get('event', {}).get('detail', {}).get('leverage')
    results['default_leverage'] = 'PASS' if s == 200 and ev_lev3 == 15.0 else f'FAIL(s={s},lev={ev_lev3})'
    print(f"9. Default leverage: lev={ev_lev3} -> {results['default_leverage']}")

    # 10. Export JSON
    s, exp = req('GET', f'/tournaments/{tid}/agents/lev-test/trades/export?format=json')
    trades = exp.get('trades', [])
    levs = [t['leverage'] for t in trades]
    results['export_json'] = 'PASS' if s == 200 and 3.0 in levs and 15.0 in levs else f'FAIL(levs={levs})'
    print(f"10. Export JSON: {len(trades)} trades, levs={levs} -> {results['export_json']}")

    # 11. CSV
    s, _ = req('GET', f'/tournaments/{tid}/agents/lev-test/trades/export?format=csv')
    results['export_csv'] = 'PASS' if s == 200 else f'FAIL({s})'
    print(f"11. CSV export: {s} -> {results['export_csv']}")

    # Wait for test agent
    print("   Waiting 12s for test agent trades...")
    time.sleep(12)

    # 12. Test agent status
    s, tas = req('GET', f'/test-agent/status/{taId}')
    t_trades = tas.get('trades', 0)
    results['test_agent_trades'] = 'PASS' if t_trades > 0 else 'FAIL'
    print(f"12. Test agent trades: {t_trades} -> {results['test_agent_trades']}")
    for line in (tas.get('log') or [])[-3:]:
        print(f"   {line}")

    # 13. Leaderboard public
    s, lb = req('GET', f'/tournaments/{tid}/leaderboard')
    results['leaderboard_public'] = 'PASS' if s == 200 and len(lb) > 0 else 'FAIL'
    print(f"13. Leaderboard: {len(lb)} entries -> {results['leaderboard_public']}")

    # 14. Dynamic leverage
    test_agents = [e for e in lb if e['agentId'].startswith('test-ai-')]
    if test_agents:
        ta_aid = test_agents[0]['agentId']
        s, ta_exp = req('GET', f'/tournaments/{tid}/agents/{ta_aid}/trades/export?format=json')
        ta_trades = ta_exp.get('trades', [])
        ta_levs = set(t['leverage'] for t in ta_trades)
        results['dynamic_leverage'] = 'PASS' if len(ta_levs) > 1 else f'WARN({ta_levs})'
        print(f"14. Dynamic leverage: {ta_levs} -> {results['dynamic_leverage']}")
    else:
        results['dynamic_leverage'] = 'SKIP'
        print("14. Dynamic leverage: SKIP")

    req('POST', f'/test-agent/stop/{taId}')

except Exception as e:
    print(f"ERROR: {e}")
    import traceback
    traceback.print_exc()
finally:
    server.terminate()

# Summary
print("\n" + "="*60)
print("VERIFICATION SUMMARY")
print("="*60)
for k, v in results.items():
    icon = "[OK]" if v == 'PASS' else ("[!]" if 'WARN' in str(v) else "[X]")
    print(f"  {icon} {k}: {v}")

passed = sum(1 for v in results.values() if v == 'PASS')
total = len(results)
print(f"\n  {passed}/{total} PASSED")
