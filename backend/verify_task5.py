"""Task 5 验证脚本：计费规则 & 报修 API"""
import os
import sys
import json

os.environ["USE_SQLITE"] = "true"
os.environ["FLASK_ENV"] = "development"

sys.path.insert(0, os.path.dirname(__file__))

from app import create_app
from extensions import db
from seed import seed as run_seed

app = create_app("development")

with app.app_context():
    run_seed()

client = app.test_client()

PASSED = 0
FAILED = 0
RESULTS = []


def record_result(name, passed, detail=""):
    global PASSED, FAILED
    if passed:
        PASSED += 1
        status = "✅ PASS"
    else:
        FAILED += 1
        status = "❌ FAIL"
    RESULTS.append((name, passed, detail))
    print(f"  {status}: {name}")
    if detail:
        print(f"         {detail}")


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def login(username, password):
    resp = client.post(
        "/api/auth/login",
        json={"username": username, "password": password},
    )
    data = resp.get_json()
    return data["token"]


def register(username, password):
    resp = client.post(
        "/api/auth/register",
        json={
            "username": username,
            "password": password,
            "confirm_password": password,
            "real_name": "Test User",
            "phone": "13800000000",
        },
    )
    data = resp.get_json()
    return data.get("token")


def test_tr_5_1():
    print("\n" + "=" * 60)
    print("TR-5.1 GET /api/rules?type=electricity")
    print("=" * 60)

    token = login("demo", "demo123")
    headers = auth_header(token)

    resp = client.get("/api/rules?type=electricity", headers=headers)
    record_result("HTTP 200", resp.status_code == 200, f"actual={resp.status_code}")

    data = resp.get_json()
    rules = data.get("rules", [])
    record_result("rules 长度=3 (tier 1,2,3)", len(rules) == 3, f"actual={len(rules)}")

    tiers = sorted([r["tier"] for r in rules])
    record_result("tier 包含 1,2,3", tiers == [1, 2, 3], f"actual={tiers}")

    example = data.get("example", {})
    record_result("example.usage=250", example.get("usage") == 250, f"actual={example.get('usage')}")

    amount = example.get("amount")
    record_result(
        "example.amount≈150.50",
        abs(amount - 150.50) < 0.01 if amount is not None else False,
        f"actual={amount}"
    )

    breakdown = example.get("breakdown", [])
    record_result("example.breakdown 非空", len(breakdown) > 0, f"actual len={len(breakdown)}")

    if len(breakdown) > 0:
        print(f"         breakdown:")
        for item in breakdown:
            print(f"           tier{item['tier']}: usage={item['usage_in_tier']}, subtotal={item['subtotal']}")


def test_tr_5_2():
    print("\n" + "=" * 60)
    print("TR-5.2 POST /api/repairs 创建报修（正常数据）")
    print("=" * 60)

    token = login("demo", "demo123")
    headers = auth_header(token)

    payload = {
        "type": "water",
        "description": "厨房水龙头一直在滴水，关不紧，地面有积水",
        "phone": "13900001111",
        "urgency": "urgent"
    }

    resp = client.post("/api/repairs", headers=headers, json=payload)
    record_result("HTTP 201", resp.status_code == 201, f"actual={resp.status_code}")

    data = resp.get_json() or {}
    repair = data.get("repair", {})
    record_result("返回包含 repair 对象", "repair" in data, "")

    status = repair.get("status")
    record_result('repair.status="pending"', status == "pending", f"actual={status}")

    rid = repair.get("id")
    record_result("repair.id>0", isinstance(rid, int) and rid > 0, f"actual={rid}")

    record_result("repair.type=water", repair.get("type") == "water", f"actual={repair.get('type')}")
    record_result("repair.urgency=urgent", repair.get("urgency") == "urgent", f"actual={repair.get('urgency')}")
    record_result("repair.phone=13900001111", repair.get("phone") == "13900001111", f"actual={repair.get('phone')}")


def test_tr_5_3():
    print("\n" + "=" * 60)
    print("TR-5.3 报修 description 过短(<10字) → HTTP 400")
    print("=" * 60)

    token = login("demo", "demo123")
    headers = auth_header(token)

    payload = {
        "type": "water",
        "description": "abc",
        "phone": "13900001111",
        "urgency": "urgent"
    }

    resp = client.post("/api/repairs", headers=headers, json=payload)
    record_result("description='abc' → HTTP 400", resp.status_code == 400, f"actual={resp.status_code}")


def test_tr_5_4():
    print("\n" + "=" * 60)
    print("TR-5.4 description 超长 & 手机号非法 → HTTP 400")
    print("=" * 60)

    token = login("demo", "demo123")
    headers = auth_header(token)

    long_desc = "测试" * 300
    record_result(f"超长 description 长度={len(long_desc)} (>500)", len(long_desc) > 500, f"len={len(long_desc)}")

    payload1 = {
        "type": "water",
        "description": long_desc,
        "phone": "13900001111",
        "urgency": "urgent"
    }
    resp1 = client.post("/api/repairs", headers=headers, json=payload1)
    record_result("description 超长(600字) → HTTP 400", resp1.status_code == 400, f"actual={resp1.status_code}")

    payload2 = {
        "type": "water",
        "description": "厨房水龙头一直在滴水，关不紧，地面有积水",
        "phone": "12345678901",
        "urgency": "urgent"
    }
    resp2 = client.post("/api/repairs", headers=headers, json=payload2)
    record_result(
        '手机号 "12345678901"(第二位为2) → HTTP 400',
        resp2.status_code == 400,
        f"actual={resp2.status_code}"
    )


def test_tr_5_5():
    print("\n" + "=" * 60)
    print("TR-5.5 报修 type=invalid_type → HTTP 400")
    print("=" * 60)

    token = login("demo", "demo123")
    headers = auth_header(token)

    payload = {
        "type": "invalid_type",
        "description": "厨房水龙头一直在滴水，关不紧，地面有积水",
        "phone": "13900001111",
        "urgency": "urgent"
    }

    resp = client.post("/api/repairs", headers=headers, json=payload)
    record_result('type="invalid_type" → HTTP 400', resp.status_code == 400, f"actual={resp.status_code}")


def test_tr_5_6():
    print("\n" + "=" * 60)
    print("TR-5.6 GET /api/repairs 筛选和用户隔离")
    print("=" * 60)

    demo_token = login("demo", "demo123")
    demo_headers = auth_header(demo_token)

    print("\n  --- demo 用户 ---")
    resp_all = client.get("/api/repairs", headers=demo_headers)
    record_result("GET /api/repairs → HTTP 200", resp_all.status_code == 200, f"actual={resp_all.status_code}")

    data_all = resp_all.get_json() or {}
    repairs_all = data_all.get("repairs", [])
    record_result(
        "demo 所有报修 = 4 条 (种子 3 + TR-5.2 创建 1)",
        len(repairs_all) == 4,
        f"actual={len(repairs_all)}"
    )

    resp_pending = client.get("/api/repairs?status=pending", headers=demo_headers)
    record_result("GET /api/repairs?status=pending → HTTP 200", resp_pending.status_code == 200, f"actual={resp_pending.status_code}")

    data_pending = resp_pending.get_json() or {}
    repairs_pending = data_pending.get("repairs", [])
    record_result(
        "status=pending 仅返回 pending 状态",
        all(r["status"] == "pending" for r in repairs_pending) if len(repairs_pending) > 0 else True,
        f"actual count={len(repairs_pending)}, statuses={[r['status'] for r in repairs_pending]}"
    )

    print("\n  --- 注册新用户 newusr2 ---")
    newusr2_token = register("newusr2_task5", "newpass123456")
    record_result("注册 newusr2 成功", newusr2_token is not None, "")

    newusr2_headers = auth_header(newusr2_token)
    resp_newusr2 = client.get("/api/repairs", headers=newusr2_headers)
    record_result("newusr2 GET /api/repairs → HTTP 200", resp_newusr2.status_code == 200, f"actual={resp_newusr2.status_code}")

    data_newusr2 = resp_newusr2.get_json() or {}
    repairs_newusr2 = data_newusr2.get("repairs", [])
    record_result(
        "newusr2 仅返回自己的 0 条（不泄露 demo 的）",
        len(repairs_newusr2) == 0,
        f"actual={len(repairs_newusr2)}"
    )

    return repairs_all


def test_authorization_violation(demo_repairs):
    print("\n" + "=" * 60)
    print("越权测试: newusr2 访问 demo 的 repair_id → HTTP 403")
    print("=" * 60)

    newusr2_token = login("newusr2_task5", "newpass123456")
    newusr2_headers = auth_header(newusr2_token)

    if not demo_repairs or len(demo_repairs) == 0:
        record_result("越权测试", False, "demo_repairs 为空，无法进行越权测试")
        return

    target_id = demo_repairs[0]["id"]
    print(f"  目标 repair_id = {target_id} (属于 demo 用户)")

    resp = client.get(f"/api/repairs/{target_id}", headers=newusr2_headers)
    record_result(
        f"newusr2 GET /api/repairs/{target_id} → HTTP 403",
        resp.status_code == 403,
        f"actual={resp.status_code}"
    )

    demo_token = login("demo", "demo123")
    demo_headers = auth_header(demo_token)
    resp_demo = client.get(f"/api/repairs/{target_id}", headers=demo_headers)
    record_result(
        f"demo GET /api/repairs/{target_id} → HTTP 200 (自己的工单可访问)",
        resp_demo.status_code == 200,
        f"actual={resp_demo.status_code}"
    )


def main():
    global PASSED, FAILED

    print("\n" + "=" * 60)
    print("  Task 5 验证测试开始（计费规则 & 报修 API）")
    print("=" * 60)

    test_tr_5_1()
    test_tr_5_2()
    test_tr_5_3()
    test_tr_5_4()
    test_tr_5_5()
    demo_repairs = test_tr_5_6()
    test_authorization_violation(demo_repairs)

    print("\n" + "=" * 60)
    print("  汇总明细")
    print("=" * 60)
    for name, passed, detail in RESULTS:
        icon = "✅" if passed else "❌"
        print(f"  {icon} {name}")
        if detail:
            print(f"     {detail}")

    print("\n" + "=" * 60)
    print(f"  测试结果: {PASSED} 通过, {FAILED} 失败")
    print("=" * 60)

    if FAILED > 0:
        sys.exit(1)


if __name__ == "__main__":
    main()
