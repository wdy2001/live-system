"""横向越权测试脚本
用法: USE_SQLITE=true python test_privilege.py

5 条越权检查（全部期望 403）:
  1) userB token GET /api/repairs/{repairA.id} → 403
  2) userA token GET /api/bills/{demo_bill_id} → 403
  3) userA token POST /api/bills/{demo_bill_id}/pay → 403

额外（注册/登录辅助检查）:
  - 注册 userA / userB 成功
  - 用 userA 创建报修 repairA 成功
  - 用 demo token 获取 unpaid bill 成功
"""
import os
import sys
import uuid

os.environ.setdefault("USE_SQLITE", "true")

from app import create_app


PASS = 0
FAIL = 0
FAILURES = []


def check(name, condition, extra=""):
    global PASS, FAIL
    if condition:
        PASS += 1
        print(f"  ✓ PASS: {name}")
    else:
        FAIL += 1
        msg = f"  ✗ FAIL: {name}"
        if extra:
            msg += f" | {extra}"
        print(msg)
        FAILURES.append((name, extra))


def _suffix():
    return uuid.uuid4().hex[:6]


def main():
    app = create_app()
    client = app.test_client()

    print("\n" + "=" * 70)
    print("  HORIZONTAL PRIVILEGE ESCALATION TESTS (5 assertions, expect 403)")
    print("=" * 70)

    suf = _suffix()
    username_a = f"priv_userA_{suf}"
    username_b = f"priv_userB_{suf}"

    # ---------- 0. 注册 userA / userB ----------
    print(f"\n[0] 注册账号: userA={username_a}, userB={username_b}")

    r = client.post("/api/auth/register", json={
        "username": username_a, "password": "test123456",
        "real_name": "用户A", "phone": "13800000001",
    })
    check("userA 注册成功 (201)", r.status_code == 201,
          f"status={r.status_code}, body={r.get_json(silent=True)}")
    userA_token = (r.get_json(silent=True) or {}).get("token")
    check("userA token 非空", bool(userA_token))

    r = client.post("/api/auth/register", json={
        "username": username_b, "password": "test123456",
        "real_name": "用户B", "phone": "13800000002",
    })
    check("userB 注册成功 (201)", r.status_code == 201,
          f"status={r.status_code}, body={r.get_json(silent=True)}")
    userB_token = (r.get_json(silent=True) or {}).get("token")
    check("userB token 非空", bool(userB_token))

    if not (userA_token and userB_token):
        print("\n  !!! 注册失败，无法继续后续越权测试 !!!\n")
        return False

    # ---------- 1. userA 创建 repairA ----------
    print("\n[1] userA 创建报修 repairA")
    r = client.post("/api/repairs", json={
        "type": "water",
        "description": f"越权测试用报修 A-{suf}",
        "phone": "13800000001",
        "urgency": "normal",
    }, headers={"Authorization": f"Bearer {userA_token}"})
    check("userA 创建 repair → 201", r.status_code == 201,
          f"status={r.status_code}, body={r.get_json(silent=True)}")
    repairA = (r.get_json(silent=True) or {}).get("repair", {})
    repairA_id = repairA.get("id")
    check("repairA.id 非空", bool(repairA_id), f"repair={repairA}")
    print(f"    repairA.id = {repairA_id}")

    # ---------- 2. demo 登录并拿一个 unpaid bill id ----------
    print("\n[2] demo 登录并获取 unpaid bill")
    r = client.post("/api/auth/login", json={
        "username": "demo", "password": "demo123",
    })
    check("demo 登录成功", r.status_code == 200,
          f"status={r.status_code}")
    demo_token = (r.get_json(silent=True) or {}).get("token")
    check("demo token 非空", bool(demo_token))

    r = client.get("/api/bills?status=unpaid",
                   headers={"Authorization": f"Bearer {demo_token}"})
    check("demo 获取 unpaid bills 成功", r.status_code == 200,
          f"status={r.status_code}")
    demo_bills = (r.get_json(silent=True) or {}).get("bills", [])
    check("demo unpaid bills 非空", len(demo_bills) > 0,
          f"len={len(demo_bills)}")
    demo_bill_id = demo_bills[0]["id"] if demo_bills else None
    print(f"    demo unpaid bill_id = {demo_bill_id}")

    # ================================================================
    # ======  5 条越权检查（全部期望 403）  ======
    # ================================================================
    print("\n" + "-" * 50)
    print("  开始 5 条越权检查（全部期望 403）")
    print("-" * 50)

    # (1) userB 访问 userA 的 repairA
    print(f"\n<检查1> userB → GET /api/repairs/{repairA_id} (应 403)")
    r = client.get(f"/api/repairs/{repairA_id}",
                   headers={"Authorization": f"Bearer {userB_token}"})
    check("[越权1] userB 访问 repairA → 403",
          r.status_code == 403,
          f"status={r.status_code}, body={r.get_json(silent=True)}")

    # (2) userA GET demo 的 bill
    print(f"\n<检查2> userA → GET /api/bills/{demo_bill_id} (应 403)")
    r = client.get(f"/api/bills/{demo_bill_id}",
                   headers={"Authorization": f"Bearer {userA_token}"})
    check("[越权2] userA GET demo bill → 403",
          r.status_code == 403,
          f"status={r.status_code}, body={r.get_json(silent=True)}")

    # (3) userA POST pay demo 的 bill
    print(f"\n<检查3> userA → POST /api/bills/{demo_bill_id}/pay (应 403)")
    r = client.post(f"/api/bills/{demo_bill_id}/pay",
                    headers={"Authorization": f"Bearer {userA_token}"},
                    json={"method": "alipay"})
    check("[越权3] userA pay demo bill → 403",
          r.status_code == 403,
          f"status={r.status_code}, body={r.get_json(silent=True)}")

    # --- 汇总 ---
    print("\n" + "=" * 70)
    print(f"  SUMMARY: PASS={PASS} / FAIL={FAIL}")
    print("=" * 70)
    if FAILURES:
        print("  失败用例:")
        for idx, (name, extra) in enumerate(FAILURES, 1):
            line = f"    {idx}. {name}"
            if extra:
                line += f" | {extra}"
            print(line)
    else:
        print("  ✅ 全部越权检查通过，所有横向越权接口均正确返回 403")
    print()

    return FAIL == 0


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
