#!/usr/bin/env python3
import subprocess
import json
import time
import sys
import os

BASE_URL = "http://localhost:5000"

def curl_get(path, auth_header=None, params=None):
    cmd = ["curl", "-s"]
    if auth_header:
        cmd += ["-H", auth_header]
    url = f"{BASE_URL}{path}"
    if params:
        qs = "&".join(f"{k}={v}" for k, v in params.items())
        url = f"{url}?{qs}"
    cmd.append(url)
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return json.loads(result.stdout)
    except:
        print(f"ERROR parsing GET {path}: stdout={result.stdout!r}, stderr={result.stderr!r}")
        return None

def curl_post(path, auth_header=None, body=None):
    cmd = ["curl", "-s", "-X", "POST"]
    if auth_header:
        cmd += ["-H", auth_header]
    if body is not None:
        cmd += ["-H", "Content-Type: application/json", "-d", json.dumps(body)]
    cmd.append(f"{BASE_URL}{path}")
    result = subprocess.run(cmd, capture_output=True, text=True)
    try:
        return json.loads(result.stdout)
    except:
        print(f"ERROR parsing POST {path}: stdout={result.stdout!r}, stderr={result.stderr!r}")
        return None

def main():
    time.sleep(2)

    # Show backend log tail
    with open("/tmp/backend2.log") as f:
        lines = f.readlines()
        for l in lines[-5:]:
            print(l, end="")

    # 1. Login
    print("--- LOGIN: ", end="")
    login = curl_post("/api/auth/login", body={"username":"demo","password":"demo123"})
    if login and "access_token" in login:
        print("ok")
        token = login["access_token"]
    else:
        print(login)
        print("FATAL: cannot login")
        sys.exit(1)
    auth = f"Authorization: Bearer {token}"

    # 2. Dashboard
    print("--- GET /api/dashboard")
    d = curl_get("/api/dashboard", auth_header=auth)
    if d:
        print(f"keys: {sorted(d.keys())}")
        print(f"unpaid_total: {d.get('unpaid_total')}")
        trends = d.get("trends") or d.get("monthly_usage") or []
        print(f"monthly_usage len: {len(trends)}")
    else:
        print("ERROR: empty dashboard response")

    # 3. Payment: unpaid electricity
    print("--- GET /api/bills?status=unpaid&type=electricity")
    d = curl_get("/api/bills", auth_header=auth, params={"status":"unpaid","type":"electricity"})
    if d:
        b = d.get("bills", [])
        print(f"count={len(b)}")
        for x in b[:3]:
            print(f"  - id={x['id']} period={x['period']} amount={x['amount']} type={x['type']} status={x['status']}")
    else:
        print("ERROR")

    # 4. Records: paid with pagination
    print("--- GET /api/bills?status=paid&page=1&per_page=2")
    d = curl_get("/api/bills", auth_header=auth, params={"status":"paid","page":"1","per_page":"2"})
    if d:
        types_list = [x["type"] for x in d.get("bills", [])]
        print(f"total={d.get('total')}, returned={len(d.get('bills',[]))}, types={types_list}")
    else:
        print("ERROR")

    # 5. Bill detail - first unpaid
    first_resp = curl_get("/api/bills", auth_header=auth, params={"status":"unpaid","per_page":"1"})
    first_unpaid_id = first_resp["bills"][0]["id"]
    print(f"--- GET /api/bills/{first_unpaid_id} (detail)")
    d = curl_get(f"/api/bills/{first_unpaid_id}", auth_header=auth)
    if d:
        bill = d["bill"]
        breakdown = bill.get("breakdown", []) or []
        subtotal_sum = sum(b["subtotal"] for b in breakdown)
        print(f"id={bill['id']} amount={bill['amount']} status={bill['status']}")
        print(f"breakdown tiers={len(breakdown)}")
        match = abs(subtotal_sum - bill['amount']) < 0.02
        print(f"subtotal_sum={subtotal_sum:.2f}, bill_amount={bill['amount']:.2f}, match={match}")
    else:
        print("ERROR")

    # 6. Pay bill
    print(f"--- POST /api/bills/{first_unpaid_id}/pay (模拟支付)")
    d = curl_post(f"/api/bills/{first_unpaid_id}/pay", auth_header=auth, body={"method":"wechat"})
    if d:
        p = d.get("payment")
        b = d.get("bill")
        tx = p.get("transaction_no") if p else None
        print(f"transaction_no={tx} (starts with PAY? {tx.startswith('PAY') if tx else False})")
        status = b.get("status") if b else None
        paid_at = b.get("paid_at") if b else None
        print(f"bill.status now={status}, paid_at set={bool(paid_at) if paid_at is not None else None}")
    else:
        print("ERROR")

    # 7. Refresh unpaid list
    print("--- GET /api/bills?status=unpaid 再次刷新")
    d = curl_get("/api/bills", auth_header=auth, params={"status":"unpaid","per_page":"50"})
    if d:
        ids = [b["id"] for b in d.get("bills", [])]
        print(f"unpaid count now={len(ids)}")
    else:
        print("ERROR")

    # Stop backend
    subprocess.run(["pkill", "-f", "python app.py"], capture_output=True)
    time.sleep(1)
    print("--- Done ---")

if __name__ == "__main__":
    main()
