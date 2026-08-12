"""Task 4 账单 API 验证脚本"""
import requests
import json
import sys

BASE = "http://127.0.0.1:5000/api"
results = []

def log_result(tr_id, passed, detail=""):
    status = "PASS" if passed else "FAIL"
    results.append((tr_id, status, detail))
    print(f"\n{'='*60}")
    print(f"[{status}] {tr_id}")
    if detail:
        print(detail)
    print(f"{'='*60}")

def auth_login(username, password):
    r = requests.post(f"{BASE}/auth/login", json={"username": username, "password": password})
    if r.status_code != 200:
        print(f"登录失败: {r.status_code} {r.text}")
        sys.exit(1)
    data = r.json()
    return data["token"]

def auth_register(username, password):
    r = requests.post(f"{BASE}/auth/register", json={
        "username": username, "password": password,
        "real_name": "新用户", "phone": "13800002222"
    })
    if r.status_code == 201:
        return r.json()["token"]
    elif r.status_code == 409:
        return auth_login(username, password)
    else:
        print(f"注册失败: {r.status_code} {r.text}")
        sys.exit(1)

def get_headers(token):
    return {"Authorization": f"Bearer {token}"}

def main():
    print("Step 1: 登录 demo/demo123")
    demo_token = auth_login("demo", "demo123")
    print(f"  demo token 获取成功: {demo_token[:30]}...")
    demo_h = get_headers(demo_token)

    # ===== TR-4.1 =====
    print("\n>>> TR-4.1: GET /api/bills (无筛选)")
    r = requests.get(f"{BASE}/bills", headers=demo_h)
    data = r.json()
    total = data.get("total")
    bills_count = len(data.get("bills", []))
    detail = f"请求: GET /api/bills\n响应 status={r.status_code}, total={total}, 返回条数={bills_count}\n账单 periods/types: {[(b['period'], b['type']) for b in data.get('bills',[])]}"
    log_result("TR-4.1", total == 18 and bills_count <= 18, detail)

    # ===== TR-4.2 =====
    print("\n>>> TR-4.2: GET /api/bills?type=electricity")
    r = requests.get(f"{BASE}/bills?type=electricity", headers=demo_h)
    data = r.json()
    total = data.get("total")
    bills = data.get("bills", [])
    all_elec = all(b["type"] == "electricity" for b in bills)
    detail = f"请求: GET /api/bills?type=electricity\n响应 status={r.status_code}, total={total}, 返回条数={len(bills)}\n所有 type=electricity: {all_elec}"
    log_result("TR-4.2", total == 6 and all_elec, detail)

    # ===== TR-4.3 =====
    print("\n>>> TR-4.3: GET /api/bills?status=unpaid")
    r = requests.get(f"{BASE}/bills?status=unpaid", headers=demo_h)
    data = r.json()
    total = data.get("total")
    bills = data.get("bills", [])
    all_unpaid = all(b["status"] == "unpaid" for b in bills)
    periods = sorted([b["period"] for b in bills])
    detail = f"请求: GET /api/bills?status=unpaid\n响应 status={r.status_code}, total={total}, 返回条数={len(bills)}\n所有 status=unpaid: {all_unpaid}\nPeriods: {periods}"
    log_result("TR-4.3", total == 6 and all_unpaid, detail)

    # ===== TR-4.4 =====
    print("\n>>> TR-4.4: GET /api/bills/:id (取某条 unpaid)")
    unpaid_bill_id = bills[0]["id"] if bills else None
    if unpaid_bill_id:
        r = requests.get(f"{BASE}/bills/{unpaid_bill_id}", headers=demo_h)
        data = r.json()
        bill = data.get("bill", {})
        breakdown = bill.get("breakdown", [])
        detail = f"请求: GET /api/bills/{unpaid_bill_id}\n响应 status={r.status_code}\nbill.type={bill.get('type')}, bill.status={bill.get('status')}\nbreakdown 长度={len(breakdown)}, 非空={len(breakdown) > 0}\nbreakdown 内容: {json.dumps(breakdown, ensure_ascii=False, indent=2)}"
        log_result("TR-4.4", r.status_code == 200 and len(breakdown) > 0, detail)
    else:
        log_result("TR-4.4", False, "没有找到 unpaid 账单")

    # ===== TR-4.5 =====
    print("\n>>> TR-4.5: POST /api/bills/:id/pay (选一条 unpaid)")
    # 用另一条 unpaid
    unpaid_bills = requests.get(f"{BASE}/bills?status=unpaid", headers=demo_h).json()["bills"]
    if len(unpaid_bills) < 2:
        # 如果只剩 1 条，那就用它
        pay_bill = unpaid_bills[0]
    else:
        pay_bill = unpaid_bills[1]
    pay_bill_id = pay_bill["id"]
    before_unpaid_count = requests.get(f"{BASE}/bills?status=unpaid", headers=demo_h).json()["total"]

    r = requests.post(f"{BASE}/bills/{pay_bill_id}/pay", headers=demo_h, json={"method": "alipay"})
    pay_data = r.json()
    payment = pay_data.get("payment", {})
    returned_bill = pay_data.get("bill", {})
    tx_no = payment.get("transaction_no", "")
    bill_paid = returned_bill.get("status") == "paid"

    # 再 GET 查一次
    r2 = requests.get(f"{BASE}/bills/{pay_bill_id}", headers=demo_h)
    bill_after = r2.json().get("bill", {})
    status_after = bill_after.get("status")
    tx_no_after = bill_after.get("payment", {}).get("transaction_no", "")

    # 查 unpaid 总数
    after_unpaid_count = requests.get(f"{BASE}/bills?status=unpaid", headers=demo_h).json()["total"]
    count_diff = before_unpaid_count - after_unpaid_count

    detail = (f"支付前 unpaid 总数={before_unpaid_count}\n"
              f"请求: POST /api/bills/{pay_bill_id}/pay\n"
              f"响应 status={r.status_code}\n"
              f"返回 payment.transaction_no={tx_no}, 以 PAY 开头={tx_no.startswith('PAY')}\n"
              f"返回 bill.status={returned_bill.get('status')}\n"
              f"再 GET /api/bills/{pay_bill_id} -> status={status_after}, payment.tx_no={tx_no_after}\n"
              f"支付后 unpaid 总数={after_unpaid_count}, 差值={count_diff} (应=1)")
    passed = (r.status_code == 200 and bill_paid and tx_no.startswith("PAY") and
              status_after == "paid" and tx_no_after.startswith("PAY") and count_diff == 1)
    log_result("TR-4.5", passed, detail)

    # ===== TR-4.6 =====
    print("\n>>> TR-4.6: POST 再次支付同一条 id")
    r = requests.post(f"{BASE}/bills/{pay_bill_id}/pay", headers=demo_h, json={"method": "alipay"})
    msg = r.json().get("msg", "")
    detail = f"请求: POST /api/bills/{pay_bill_id}/pay\n响应 status={r.status_code}, msg={msg}"
    log_result("TR-4.6", r.status_code == 400 and "已支付" in msg, detail)

    # ===== TR-4.7 =====
    print("\n>>> TR-4.7: newusr 支付 demo 的账单")
    newusr_token = auth_register("newusr", "newusr123")
    newusr_h = get_headers(newusr_token)
    # 找 demo 的一条 unpaid 账单
    demo_unpaid = requests.get(f"{BASE}/bills?status=unpaid", headers=demo_h).json()["bills"]
    if not demo_unpaid:
        # 如果都付了，就用已经付过的那条也行，不过应该先检查权限
        target_id = pay_bill_id
    else:
        target_id = demo_unpaid[0]["id"]
    r = requests.post(f"{BASE}/bills/{target_id}/pay", headers=newusr_h, json={"method": "wechat"})
    status_code = r.status_code
    msg = r.json().get("msg", "")
    detail = (f"先注册/登录 newusr 获取 token\n"
              f"请求: POST /api/bills/{target_id}/pay (newusr token)\n"
              f"响应 status={status_code}, msg={msg}")
    log_result("TR-4.7", status_code == 403 and ("无权" in msg or "权限" in msg), detail)

    # ===== 分页验证 =====
    print("\n>>> 分页: GET /api/bills?per_page=3&page=2")
    # 先重置数据，重新 seed，保证分页验证准确
    print("  先重新 seed 保证数据干净...")
    import subprocess
    env = dict(__import__("os").environ)
    env["USE_SQLITE"] = "true"
    subprocess.run(["python", "seed.py"], cwd="/workspace/backend", capture_output=True, env=env)
    demo_token2 = auth_login("demo", "demo123")
    demo_h2 = get_headers(demo_token2)

    all_total = requests.get(f"{BASE}/bills", headers=demo_h2).json()["total"]
    r = requests.get(f"{BASE}/bills?per_page=3&page=2", headers=demo_h2)
    data = r.json()
    total = data.get("total")
    returned_count = len(data.get("bills", []))
    page = data.get("page")
    per_page = data.get("per_page")
    detail = (f"总账单数 all_total={all_total}\n"
              f"请求: GET /api/bills?per_page=3&page=2\n"
              f"响应 status={r.status_code}\n"
              f"page={page}, per_page={per_page}, total={total}, 返回条数={returned_count}\n"
              f"返回 bills periods: {[b['period'] for b in data.get('bills', [])]}\n"
              f"offset 校验: page2 应从第 4 条开始 (index 3)")
    # 验证逻辑：总数应该=18（不随分页变），返回条数=3，page=2，per_page=3
    passed = (r.status_code == 200 and total == 18 and returned_count == 3 and
              page == 2 and per_page == 3)
    log_result("分页(per_page=3&page=2)", passed, detail)

    # ===== 汇总 =====
    print("\n\n" + "#"*60)
    print("最终汇总结果")
    print("#"*60)
    passed_count = 0
    for tr_id, status, detail in results:
        print(f"  [{status}] {tr_id}")
        if status == "PASS":
            passed_count += 1
    print(f"\n总计: {passed_count}/{len(results)} 通过")
    return all(s == "PASS" for _, s, _ in results)

if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
