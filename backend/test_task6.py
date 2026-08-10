"""Task 6 故障报修 API 验证脚本"""
import sys
import json
import urllib.request
import urllib.error

BASE_URL = "http://127.0.0.1:5000"


def request(method, path, data=None, token=None):
    url = f"{BASE_URL}{path}"
    headers = {"Content-Type": "application/json"}
    if token:
        headers["Authorization"] = f"Bearer {token}"
    body = None
    if data is not None:
        body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(url, data=body, method=method, headers=headers)
    try:
        with urllib.request.urlopen(req) as resp:
            status = resp.status
            text = resp.read().decode("utf-8")
            try:
                js = json.loads(text) if text else None
            except json.JSONDecodeError:
                js = None
            return status, js, text
    except urllib.error.HTTPError as e:
        text = e.read().decode("utf-8")
        try:
            js = json.loads(text) if text else None
        except json.JSONDecodeError:
            js = None
        return e.code, js, text


def login_demo():
    status, data, _ = request("POST", "/api/auth/login",
                              {"username": "demo", "password": "demo123"})
    assert status == 200, f"登录失败: {status} {data}"
    return data["token"], data["user"]


def check_db_counts():
    """通过 API 间接查询数量"""
    pass


def main():
    results = []
    token, demo_user = login_demo()
    demo_id = demo_user["id"]
    print(f"demo 用户 id = {demo_id}")

    # ===== 先获取初始工单数量用于 TR-6.2 验证 =====
    status, data, _ = request("GET", "/api/repairs", token=token)
    assert status == 200
    initial_count = len(data["repairs"])
    print(f"初始工单数量: {initial_count}")

    # ===== TR-6.1 合法提交 =====
    print("\n=== TR-6.1 合法提交 ===")
    status, data, _ = request("POST", "/api/repairs", {
        "type": "electricity",
        "description": "客厅空调插座不通电，已经持续2天了",
        "phone": "13812345678",
        "urgency": "urgent",
    }, token=token)
    tr61_pass = True
    checks = []

    check = status == 201
    checks.append(("HTTP 201", check, f"实际={status}"))
    tr61_pass &= check

    repair = data.get("repair") if data else None
    check = repair is not None
    checks.append(("返回 repair 对象", check))
    tr61_pass &= check

    if repair:
        check = repair.get("id", 0) > 0
        checks.append(("repair.id > 0", check, f"id={repair.get('id')}"))
        tr61_pass &= check

        check = repair.get("status") == "pending"
        checks.append(("repair.status == pending", check, f"status={repair.get('status')}"))
        tr61_pass &= check

        check = repair.get("type") == "electricity"
        checks.append(("repair.type == electricity", check, f"type={repair.get('type')}"))
        tr61_pass &= check

        check = repair.get("created_at") is not None and len(repair.get("created_at", "")) > 0
        checks.append(("repair.created_at 存在 (isoformat)", check, f"created_at={repair.get('created_at')}"))
        tr61_pass &= check

    for check_item in checks:
        name = check_item[0]
        ok = check_item[1]
        extra = check_item[2] if len(check_item) > 2 else None
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}" + (f"  ({extra})" if extra else ""))
    results.append(("TR-6.1 合法提交", tr61_pass))

    # ===== TR-6.2 非法参数 =====
    print("\n=== TR-6.2 非法参数 ===")

    # (a) description 仅 "坏了"（<10 字）=> 400，DB 无新增
    tr62a_checks = []
    status, data, _ = request("POST", "/api/repairs", {
        "type": "electricity",
        "description": "坏了",
        "phone": "13812345678",
        "urgency": "normal",
    }, token=token)
    check = status == 400
    tr62a_checks.append(("描述过短 => HTTP 400", check, f"实际={status}, msg={data.get('msg') if data else None}"))
    tr62a = all(c[1] for c in tr62a_checks)

    # 检查 DB 无新增
    status, data, _ = request("GET", "/api/repairs", token=token)
    count_after_a = len(data["repairs"])
    # TR-6.1 新增了 1 条，所以应为 initial_count + 1（TR-6.2a 不应再增加）
    check = count_after_a == initial_count + 1
    tr62a_checks.append(("DB 无新增（初始+1 不变）", check, f"初始={initial_count}, 当前={count_after_a}, 期望={initial_count + 1}"))
    tr62a = all(c[1] for c in tr62a_checks)

    for check_item in tr62a_checks:
        name = check_item[0]
        ok = check_item[1]
        extra = check_item[2] if len(check_item) > 2 else None
        print(f"  (a) [{'PASS' if ok else 'FAIL'}] {name}" + (f"  ({extra})" if extra else ""))
    results.append(("TR-6.2(a) 描述过短", tr62a))

    # (b) type = "internet" 非法 => 400
    tr62b_checks = []
    status, data, _ = request("POST", "/api/repairs", {
        "type": "internet",
        "description": "客厅空调插座不通电，已经持续2天了",
        "phone": "13812345678",
    }, token=token)
    check = status == 400
    tr62b_checks.append(("type=internet => HTTP 400", check, f"实际={status}, msg={data.get('msg') if data else None}"))
    tr62b = all(c[1] for c in tr62b_checks)
    for check_item in tr62b_checks:
        name = check_item[0]
        ok = check_item[1]
        extra = check_item[2] if len(check_item) > 2 else None
        print(f"  (b) [{'PASS' if ok else 'FAIL'}] {name}" + (f"  ({extra})" if extra else ""))
    results.append(("TR-6.2(b) 非法 type", tr62b))

    # (c) phone = "12345" => 400
    tr62c_checks = []
    status, data, _ = request("POST", "/api/repairs", {
        "type": "electricity",
        "description": "客厅空调插座不通电，已经持续2天了",
        "phone": "12345",
    }, token=token)
    check = status == 400
    tr62c_checks.append(("phone=12345 => HTTP 400", check, f"实际={status}, msg={data.get('msg') if data else None}"))
    tr62c = all(c[1] for c in tr62c_checks)
    for check_item in tr62c_checks:
        name = check_item[0]
        ok = check_item[1]
        extra = check_item[2] if len(check_item) > 2 else None
        print(f"  (c) [{'PASS' if ok else 'FAIL'}] {name}" + (f"  ({extra})" if extra else ""))
    results.append(("TR-6.2(c) 非法 phone", tr62c))

    tr62_all = tr62a and tr62b and tr62c
    results.append(("TR-6.2 全部非法参数", tr62_all))

    # ===== TR-6.3 列表排序与过滤 =====
    print("\n=== TR-6.3 列表排序与过滤 ===")

    # GET /api/repairs（demo 登录）=> 按 created_at 降序
    status, data, _ = request("GET", "/api/repairs", token=token)
    tr63a_checks = []
    check = status == 200
    tr63a_checks.append(("HTTP 200", check, f"实际={status}"))
    repairs = data.get("repairs", [])
    check = len(repairs) >= 3  # 原 seed 有 3 条 + TR-6.1 新增 1 条
    tr63a_checks.append(("返回工单数量", check, f"数量={len(repairs)}"))

    # 排序检查：第 0 条 created_at >= 第 1 条
    if len(repairs) >= 2:
        check = repairs[0]["created_at"] >= repairs[1]["created_at"]
        tr63a_checks.append(("第 0 条 created_at >= 第 1 条（降序）", check,
                             f"0: {repairs[0]['created_at']}, 1: {repairs[1]['created_at']}"))

    # 所有工单 user_id == demo.id
    all_demo_user = all(r["user_id"] == demo_id for r in repairs)
    tr63a_checks.append(("所有工单 user_id == demo.id", all_demo_user,
                         f"demo_id={demo_id}, ids={[r['user_id'] for r in repairs]}"))

    tr63a = all(c[1] for c in tr63a_checks)
    for check_item in tr63a_checks:
        name = check_item[0]
        ok = check_item[1]
        extra = check_item[2] if len(check_item) > 2 else None
        print(f"  [列表排序] [{'PASS' if ok else 'FAIL'}] {name}" + (f"  ({extra})" if extra else ""))
    results.append(("TR-6.3 列表排序", tr63a))

    # GET /api/repairs?status=pending
    tr63b_checks = []
    status, data, _ = request("GET", "/api/repairs?status=pending", token=token)
    check = status == 200
    tr63b_checks.append(("status=pending => HTTP 200", check))
    pending_repairs = data.get("repairs", [])
    check = len(pending_repairs) >= 1 and all(r["status"] == "pending" for r in pending_repairs)
    tr63b_checks.append(("仅返回 status='pending' 的工单", check,
                         f"数量={len(pending_repairs)}, statuses={[r['status'] for r in pending_repairs]}"))
    tr63b = all(c[1] for c in tr63b_checks)
    for check_item in tr63b_checks:
        name = check_item[0]
        ok = check_item[1]
        extra = check_item[2] if len(check_item) > 2 else None
        print(f"  [status=pending] [{'PASS' if ok else 'FAIL'}] {name}" + (f"  ({extra})" if extra else ""))
    results.append(("TR-6.3 status=pending 过滤", tr63b))

    # GET /api/repairs?status=resolved
    tr63c_checks = []
    status, data, _ = request("GET", "/api/repairs?status=resolved", token=token)
    check = status == 200
    tr63c_checks.append(("status=resolved => HTTP 200", check))
    resolved_repairs = data.get("repairs", [])
    check = len(resolved_repairs) >= 1 and all(r["status"] == "resolved" for r in resolved_repairs)
    tr63c_checks.append(("仅返回 status='resolved' 的工单", check,
                         f"数量={len(resolved_repairs)}, statuses={[r['status'] for r in resolved_repairs]}"))
    tr63c = all(c[1] for c in tr63c_checks)
    for check_item in tr63c_checks:
        name = check_item[0]
        ok = check_item[1]
        extra = check_item[2] if len(check_item) > 2 else None
        print(f"  [status=resolved] [{'PASS' if ok else 'FAIL'}] {name}" + (f"  ({extra})" if extra else ""))
    results.append(("TR-6.3 status=resolved 过滤", tr63c))

    tr63_all = tr63a and tr63b and tr63c
    results.append(("TR-6.3 列表排序与过滤全部", tr63_all))

    # ===== 汇总 =====
    print("\n" + "=" * 50)
    print("验证结果汇总：")
    all_pass = True
    for name, ok in results:
        print(f"  [{'PASS' if ok else 'FAIL'}] {name}")
        all_pass &= ok
    print("=" * 50)
    if all_pass:
        print("✅ 全部验证通过")
        return 0
    else:
        print("❌ 部分验证失败")
        return 1


if __name__ == "__main__":
    sys.exit(main())
