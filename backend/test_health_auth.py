"""健康检查与鉴权保护验证脚本
用法: USE_SQLITE=true python test_health_auth.py

7 项断言:
  a) GET /api/health 匿名 → 200, {"status":"ok","service":"life-system"}
  b) GET /api/bills 无 token → 401（含 msg 字段）
  c) GET /api/households/mine 无 token → 401
  d) GET /api/repairs 无 token → 401
  e) GET /api/dashboard 无 token → 401
  f) GET /api/auth/me 无 token → 401
  g) GET /api/rules 匿名 → 200（规则接口不保护）
"""
import os
import sys

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


def main():
    app = create_app()
    client = app.test_client()

    print("\n" + "=" * 70)
    print("  HEALTH & AUTH PROTECTION TESTS (7 assertions)")
    print("=" * 70)

    # --- a) GET /api/health 匿名 ---
    print("\n[a] GET /api/health 匿名")
    r = client.get("/api/health")
    body = r.get_json(silent=True) or {}
    check("health 状态码 200", r.status_code == 200, f"实际={r.status_code}")
    check("health body.status == ok",
          body.get("status") == "ok", f"status={body.get('status')}")
    check("health body.service == life-system",
          body.get("service") == "life-system", f"service={body.get('service')}")

    # --- b) GET /api/bills 无 token ---
    print("\n[b] GET /api/bills 无 token")
    r = client.get("/api/bills")
    body = r.get_json(silent=True) or {}
    check("bills 无 token → 401", r.status_code == 401,
          f"实际={r.status_code}, body={body}")
    check("bills 401 含 msg 字段", "msg" in body, f"body keys={list(body.keys())}")

    # --- c) GET /api/households/mine 无 token ---
    print("\n[c] GET /api/households/mine 无 token")
    r = client.get("/api/households/mine")
    body = r.get_json(silent=True) or {}
    check("households/mine 无 token → 401", r.status_code == 401,
          f"实际={r.status_code}, body={body}")

    # --- d) GET /api/repairs 无 token ---
    print("\n[d] GET /api/repairs 无 token")
    r = client.get("/api/repairs")
    body = r.get_json(silent=True) or {}
    check("repairs 无 token → 401", r.status_code == 401,
          f"实际={r.status_code}, body={body}")

    # --- e) GET /api/dashboard 无 token ---
    print("\n[e] GET /api/dashboard 无 token")
    r = client.get("/api/dashboard")
    body = r.get_json(silent=True) or {}
    check("dashboard 无 token → 401", r.status_code == 401,
          f"实际={r.status_code}, body={body}")

    # --- f) GET /api/auth/me 无 token ---
    print("\n[f] GET /api/auth/me 无 token")
    r = client.get("/api/auth/me")
    body = r.get_json(silent=True) or {}
    check("auth/me 无 token → 401", r.status_code == 401,
          f"实际={r.status_code}, body={body}")

    # --- g) GET /api/rules 匿名 → 200 ---
    print("\n[g] GET /api/rules 匿名（规则接口不保护）")
    r = client.get("/api/rules")
    body = r.get_json(silent=True) or {}
    check("rules 匿名 → 200", r.status_code == 200,
          f"实际={r.status_code}, body={body}")
    check("rules 含 rules 数组（8 条）",
          isinstance(body.get("rules"), list) and len(body.get("rules", [])) == 8,
          f"rules len={len(body.get('rules', []))}")

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
        print("  ✅ 全部 7+ 健康与鉴权保护断言通过")
    print()

    return FAIL == 0


if __name__ == "__main__":
    ok = main()
    sys.exit(0 if ok else 1)
