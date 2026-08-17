#!/usr/bin/env python3
import subprocess
import json
import time
import sys
import os
import random
import string

BASE_URL = "http://localhost:5000"

passed = 0
failed = 0

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

def check(name, condition, detail=""):
    global passed, failed
    if condition:
        passed += 1
        print(f"  [PASS] {name}")
        if detail:
            print(f"         {detail}")
    else:
        failed += 1
        print(f"  [FAIL] {name}")
        if detail:
            print(f"         {detail}")

def rand_user():
    suffix = ''.join(random.choices(string.ascii_lowercase + string.digits, k=6))
    return f"testuser_{suffix}", f"pass{suffix}123", suffix

def main():
    global passed, failed
    print("=" * 60)
    print("生活缴费系统 · 全流程API测试")
    print("=" * 60)

    time.sleep(2)

    print("\n=== Step 1: 注册新用户 ===")
    username, password, suffix = rand_user()
    print(f"  用户名: {username}")
    register_data = {
        "username": username,
        "password": password,
        "confirm_password": password,
        "real_name": f"测试用户{suffix}",
        "phone": "13800138000",
    }
    reg = curl_post("/api/auth/register", body=register_data)
    check("注册成功返回201/access_token", reg is not None and "access_token" in reg, str(reg)[:100])
    if not reg or "access_token" not in reg:
        print("FATAL: 注册失败，无法继续")
        sys.exit(1)

    print("\n=== Step 2: 登录（新用户） ===")
    login = curl_post("/api/auth/login", body={"username": username, "password": password})
    check("登录成功返回access_token", login is not None and "access_token" in login, str(login)[:100])
    if not login or "access_token" not in login:
        print("FATAL: 登录失败，无法继续")
        sys.exit(1)
    new_token = login["access_token"]
    new_auth = f"Authorization: Bearer {new_token}"
    print(f"  新用户 Token prefix: {new_token[:30]}...")

    print("\n=== Step 3: 查询户号 GET /api/households/mine（新用户） ===")
    hh = curl_get("/api/households/mine", auth_header=new_auth)
    check("返回households数组", hh is not None and "households" in hh, str(hh)[:100] if hh else "")
    households = hh.get("households", []) if hh else []
    check("至少1个户号", len(households) >= 1, f"count={len(households)}")
    if households:
        h = households[0]
        check("户号含household_no字段", "household_no" in h, str(h)[:80])
        check("户号含meters数组", "meters" in h and isinstance(h.get("meters"), list), f"meters_count={len(h.get('meters',[]))}")

    print("\n=== 切换到 demo 用户（有预设账单/报修/用量数据） ===")
    demo_login = curl_post("/api/auth/login", body={"username": "demo", "password": "demo123"})
    check("demo 用户登录成功", demo_login is not None and "access_token" in demo_login, str(demo_login)[:100])
    if not demo_login or "access_token" not in demo_login:
        print("FATAL: demo 登录失败，无法继续")
        sys.exit(1)
    token = demo_login["access_token"]
    auth = f"Authorization: Bearer {token}"
    print(f"  Demo Token prefix: {token[:30]}...")

    print("\n=== Step 4: 查询账单列表（type+status筛选+分页） ===")
    print("--- 4a: 查未缴电费 GET /api/bills?status=unpaid&type=electricity ---")
    b_elec = curl_get("/api/bills", auth_header=auth, params={"status": "unpaid", "type": "electricity"})
    check("返回bills+total字段", b_elec is not None and "bills" in b_elec and "total" in b_elec, str(b_elec)[:100] if b_elec else "")
    bills_unpaid_elec = b_elec.get("bills", []) if b_elec else []
    check("未缴电费数量>=1", len(bills_unpaid_elec) >= 1, f"count={len(bills_unpaid_elec)} / total={b_elec.get('total') if b_elec else 'N/A'}")

    print("--- 4b: 查已缴账单（分页page=1,per_page=2）GET /api/bills?status=paid&page=1&per_page=2 ---")
    b_paid_paged = curl_get("/api/bills", auth_header=auth, params={"status": "paid", "page": "1", "per_page": "2"})
    check("分页返回total+page+per_page", b_paid_paged is not None and all(k in b_paid_paged for k in ("total", "page", "per_page")), str(b_paid_paged)[:100] if b_paid_paged else "")
    page_size = len(b_paid_paged.get("bills", [])) if b_paid_paged else 0
    check("分页结果数量<=per_page", page_size <= 2, f"returned={page_size}")

    print("\n=== Step 5: 查询某账单详情（含breakdown阶梯拆分） ===")
    first_unpaid_resp = curl_get("/api/bills", auth_header=auth, params={"status": "unpaid", "per_page": "1"})
    first_unpaid_id = None
    if first_unpaid_resp and first_unpaid_resp.get("bills"):
        first_unpaid_id = first_unpaid_resp["bills"][0]["id"]
    check("有未缴账单可取详情", first_unpaid_id is not None, f"first_unpaid_id={first_unpaid_id}")

    if first_unpaid_id:
        detail = curl_get(f"/api/bills/{first_unpaid_id}", auth_header=auth)
        check("返回bill字段", detail is not None and "bill" in detail, str(detail)[:80] if detail else "")
        if detail and "bill" in detail:
            bill = detail["bill"]
            check("账单含amount+status字段", all(k in bill for k in ("amount", "status")), f"keys={list(bill.keys())[:10]}")
            breakdown = bill.get("breakdown", []) or []
            check("账单含breakdown数组", isinstance(breakdown, list) and len(breakdown) >= 1, f"breakdown_len={len(breakdown)}")
            if breakdown:
                subtotal_sum = sum(b.get("subtotal", 0) for b in breakdown)
                match = abs(subtotal_sum - float(bill["amount"])) < 0.02
                check("breakdown小计之和≈账单金额", match, f"sum={subtotal_sum:.2f}, bill={bill['amount']:.2f}")

    print("\n=== Step 6: 支付1条账单 ===")
    pay_result = None
    if first_unpaid_id:
        pay_result = curl_post(f"/api/bills/{first_unpaid_id}/pay", auth_header=auth, body={"method": "wechat"})
        check("支付返回payment+bill", pay_result is not None and "payment" in pay_result and "bill" in pay_result, str(pay_result)[:100] if pay_result else "")
        if pay_result:
            p = pay_result.get("payment", {})
            tx = p.get("transaction_no", "")
            check("transaction_no以PAY开头", isinstance(tx, str) and tx.startswith("PAY"), f"tx={tx[:20]}...")
            b = pay_result.get("bill", {})
            check("支付后账单status=paid", b.get("status") == "paid", f"status={b.get('status')}")
            check("支付后paid_at已设置", bool(b.get("paid_at")), f"paid_at={b.get('paid_at')}")

    print("\n=== Step 7: 验证账单已paid ===")
    if first_unpaid_id and pay_result:
        verify_detail = curl_get(f"/api/bills/{first_unpaid_id}", auth_header=auth)
        if verify_detail and "bill" in verify_detail:
            vbill = verify_detail["bill"]
            check("刷新后status=paid", vbill.get("status") == "paid", f"status={vbill.get('status')}")
            check("刷新后payment字段存在", "payment" in vbill, f"has_payment={'payment' in vbill}")

        unpaid_after = curl_get("/api/bills", auth_header=auth, params={"status": "unpaid", "per_page": "50"})
        ids_after = [b["id"] for b in unpaid_after.get("bills", [])] if unpaid_after else []
        check("已付账单不在unpaid列表中", first_unpaid_id not in ids_after, f"id={first_unpaid_id}, unpaid_ids={ids_after[:5]}")

    print("\n=== Step 8: 查询GET /rules三种类型 ===")
    for bill_type in ["electricity", "water", "gas"]:
        print(f"--- 查询 {bill_type} 规则 ---")
        r = curl_get("/api/rules", params={"type": bill_type})
        check(f"返回rules+example字段({bill_type})", r is not None and "rules" in r and "example" in r, str(r)[:80] if r else "")
        if r:
            rules_of_type = [rl for rl in r.get("rules", []) if rl.get("type") == bill_type]
            check(f"{bill_type}规则数量>=1", len(rules_of_type) >= 1, f"count={len(rules_of_type)}")
            example = r.get("example", {})
            check(f"{bill_type}示例含amount+breakdown", all(k in example for k in ("amount", "breakdown")), f"example_keys={list(example.keys())}")

    print("\n=== Step 9: 创建报修工单（合法参数） ===")
    repair_data = {
        "type": "electricity",
        "description": "客厅吊灯无法正常开启，疑似线路故障，请尽快安排师傅上门检修，谢谢！",
        "phone": "13900139000",
        "urgency": "normal",
    }
    repair_create = curl_post("/api/repairs", auth_header=auth, body=repair_data)
    check("创建报修返回201/repair字段", repair_create is not None and "repair" in repair_create, str(repair_create)[:100] if repair_create else "")
    new_repair_id = None
    if repair_create and "repair" in repair_create:
        rp = repair_create["repair"]
        new_repair_id = rp.get("id")
        check("报修工单含id字段", new_repair_id is not None, f"id={new_repair_id}")
        check("报修status=pending", rp.get("status") == "pending", f"status={rp.get('status')}")
        check("报修type=electricity", rp.get("type") == "electricity", f"type={rp.get('type')}")

    print("\n=== Step 10: 查询repair列表 ===")
    repair_list = curl_get("/api/repairs", auth_header=auth)
    check("返回repairs数组", repair_list is not None and "repairs" in repair_list, str(repair_list)[:100] if repair_list else "")
    repairs = repair_list.get("repairs", []) if repair_list else []
    check("报修列表包含新创建工单", new_repair_id is None or any(r["id"] == new_repair_id for r in repairs), f"new_id={new_repair_id}, list_count={len(repairs)}")
    check("报修列表数量>=2（种子2条+新创建>=1条）", len(repairs) >= 2, f"count={len(repairs)}")

    print("\n=== Step 11: GET /dashboard 所有字段齐全 ===")
    d = curl_get("/api/dashboard", auth_header=auth)
    check("dashboard返回成功", d is not None, str(d)[:80] if d else "")
    required_dashboard_fields = ["total_unpaid_amount", "unpaid_count", "this_month_usage", "repair_stats", "usage_trend", "households"]
    if d:
        for f in required_dashboard_fields:
            check(f"dashboard含字段 {f}", f in d, f"{f} = {str(d.get(f))[:60]}")
        check("total_unpaid_amount是数字", isinstance(d.get("total_unpaid_amount"), (int, float)), f"type={type(d.get('total_unpaid_amount'))}")
        check("unpaid_count是数字", isinstance(d.get("unpaid_count"), int), f"type={type(d.get('unpaid_count'))}")
        if "this_month_usage" in d:
            tmu = d["this_month_usage"]
            check("this_month_usage含electricity/water/gas", all(k in tmu for k in ("electricity", "water", "gas")), f"keys={list(tmu.keys())}")
        if "repair_stats" in d:
            rs = d["repair_stats"]
            check("repair_stats含pending/processing/resolved", all(k in rs for k in ("pending", "processing", "resolved")), f"keys={list(rs.keys())}")
        if "usage_trend" in d:
            mu = d["usage_trend"]
            check("usage_trend为数组且=6条", isinstance(mu, list) and len(mu) == 6, f"len={len(mu)}")
            if isinstance(mu, list) and len(mu) > 0:
                check("usage_trend首条含period+三种用量", all(k in mu[0] for k in ("period", "electricity", "water", "gas")), f"keys={list(mu[0].keys())}")
        if "households" in d:
            check("households为数组", isinstance(d["households"], list), f"len={len(d['households'])}")

    print("\n" + "=" * 60)
    print(f"测试结果: 通过 {passed} 项, 失败 {failed} 项")
    print("=" * 60)
    if failed == 0:
        print("所有测试通过！")
        sys.exit(0)
    else:
        print(f"有 {failed} 项测试失败，请检查输出！")
        sys.exit(1)

if __name__ == "__main__":
    main()
