"""Task 3 补充验证: households/mine 接口 + spec.md AC-1 核对"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app


def main():
    app = create_app()
    results = []

    with app.test_client() as client:
        with app.app_context():
            print("=" * 60)
            print("Task 3 补充验证: Households + AC-1")
            print("=" * 60)

            # ========== demo 登录获取 token ==========
            print("\n--- 1. demo 登录获取 token ---")
            resp_login = client.post(
                "/api/auth/login",
                json={"username": "demo", "password": "demo123"},
            )
            data_login = resp_login.get_json() or {}
            token = data_login.get("token")

            login_ok = resp_login.status_code == 200 and token is not None
            print(f"登录状态: HTTP {resp_login.status_code} | token存在={token is not None}")
            results.append(("PRE-login", login_ok, f"demo登录: HTTP {resp_login.status_code}"))

            # ========== AC-1: 注册返回用户信息 + token ==========
            print("\n--- AC-1-1 注册成功返回用户信息 + token ---")
            import random, string
            username = "ac1test_" + "".join(random.choices(string.ascii_lowercase, k=5))
            resp_reg = client.post(
                "/api/auth/register",
                json={"username": username, "password": "test123", "confirm_password": "test123"},
            )
            data_reg = resp_reg.get_json() or {}
            reg_code = resp_reg.status_code == 201
            reg_has_user = "user" in data_reg and "id" in data_reg.get("user", {})
            reg_has_token = "token" in data_reg and len(data_reg.get("token", "")) > 0
            reg_uname_match = data_reg.get("user", {}).get("username") == username
            r1 = (
                f"AC-1-1 注册: HTTP {resp_reg.status_code}(期望201)={reg_code} | "
                f"user存在={reg_has_user} | token存在={reg_has_token} | "
                f"username匹配={reg_uname_match}"
            )
            passed1 = reg_code and reg_has_user and reg_has_token and reg_uname_match
            results.append(("AC-1-1", passed1, r1))
            print(f"[{'PASS' if passed1 else 'FAIL'}] {r1}")
            if not passed1:
                print(f"  data keys: {list(data_reg.keys())}")
                print(f"  user: {data_reg.get('user')}")
                print(f"  token: {data_reg.get('token', '')[:50]}...")

            # ========== AC-1: 登录成功返回 JWT token ==========
            print("\n--- AC-1-2 登录成功返回 JWT token ---")
            resp_login2 = client.post(
                "/api/auth/login",
                json={"username": username, "password": "test123"},
            )
            data_login2 = resp_login2.get_json() or {}
            login2_code = resp_login2.status_code == 200
            login2_has_token = "token" in data_login2 and len(data_login2.get("token", "")) > 0
            r2 = (
                f"AC-1-2 新用户登录: HTTP {resp_login2.status_code}(期望200)={login2_code} | "
                f"token存在且非空={login2_has_token}"
            )
            passed2 = login2_code and login2_has_token
            results.append(("AC-1-2", passed2, r2))
            print(f"[{'PASS' if passed2 else 'FAIL'}] {r2}")
            new_token = data_login2.get("token") if passed2 else None

            # ========== AC-1: /me 鉴权 - 有 Token ==========
            print("\n--- AC-1-3a /me 鉴权: 有 Token 返回用户 ---")
            if new_token:
                resp_me_ok = client.get(
                    "/api/auth/me",
                    headers={"Authorization": f"Bearer {new_token}"},
                )
                me_data = resp_me_ok.get_json() or {}
                me_ok_code = resp_me_ok.status_code == 200
                me_ok_has_user = "user" in me_data
                me_ok_uname = me_data.get("user", {}).get("username") == username
                r3a = (
                    f"AC-1-3a 有Token访问/me: HTTP {resp_me_ok.status_code}(期望200)={me_ok_code} | "
                    f"user存在={me_ok_has_user} | username匹配={me_ok_uname}"
                )
                passed3a = me_ok_code and me_ok_has_user and me_ok_uname
            else:
                r3a = "AC-1-3a 跳过：未获取到新用户token"
                passed3a = False
            results.append(("AC-1-3a", passed3a, r3a))
            print(f"[{'PASS' if passed3a else 'FAIL'}] {r3a}")

            # ========== AC-1: /me 鉴权 - 无 Token ==========
            print("\n--- AC-1-3b /me 鉴权: 无 Token 返回 401/422 ---")
            resp_me_no = client.get("/api/auth/me")
            me_no_code = resp_me_no.status_code in (401, 422)
            r3b = f"AC-1-3b 无Token访问/me: HTTP {resp_me_no.status_code}(期望401/422)={me_no_code}"
            passed3b = me_no_code
            results.append(("AC-1-3b", passed3b, r3b))
            print(f"[{'PASS' if passed3b else 'FAIL'}] {r3b}")

            # ========== TR-3.5: GET /api/households/mine ==========
            print("\n--- TR-3.5 demo 访问 /api/households/mine ---")
            if token:
                resp_hh = client.get(
                    "/api/households/mine",
                    headers={"Authorization": f"Bearer {token}"},
                )
                hh_data = resp_hh.get_json() or {}
                households = hh_data.get("households", [])
                hh_count = len(households)
                hh_code = resp_hh.status_code == 200
                hh_one = hh_count == 1
                meter_types = []
                if hh_count >= 1:
                    meters = households[0].get("meters", [])
                    meter_types = sorted([m.get("type") for m in meters])
                expected_types = ["electricity", "gas", "water"]
                meters_ok = meter_types == expected_types

                r_hh = (
                    f"TR-3.5 /households/mine: HTTP {resp_hh.status_code}(期望200)={hh_code} | "
                    f"户号数={hh_count}(期望1)={hh_one} | "
                    f"表类型={meter_types}(期望{expected_types})={meters_ok}"
                )
                passed_hh = hh_code and hh_one and meters_ok
                print(f"[{'PASS' if passed_hh else 'FAIL'}] {r_hh}")
                if hh_count >= 1:
                    print(f"  户号: {households[0].get('household_no')} | 地址: {households[0].get('address')}")
                    for m in households[0].get("meters", []):
                        print(f"  表: {m.get('type')} / {m.get('meter_no')} / 当前读数={m.get('current_reading')}")
                else:
                    print(f"  返回数据: {hh_data}")
            else:
                r_hh = "TR-3.5 跳过：未获取到 demo token"
                passed_hh = False
                print(f"[SKIP] {r_hh}")
            results.append(("TR-3.5", passed_hh, r_hh))

            # ========== 无 Token 访问 /households/mine ==========
            print("\n--- /households/mine 无 Token 鉴权 ---")
            resp_hh_no = client.get("/api/households/mine")
            hh_no_code = resp_hh_no.status_code in (401, 422)
            r_hh_no = f"/households/mine 无Token: HTTP {resp_hh_no.status_code}(期望401/422)={hh_no_code}"
            passed_hh_no = hh_no_code
            results.append(("TR-3.5-auth", passed_hh_no, r_hh_no))
            print(f"[{'PASS' if passed_hh_no else 'FAIL'}] {r_hh_no}")

            # ========== 汇总 ==========
            print("\n" + "=" * 60)
            print("补充验证结果汇总")
            print("=" * 60)
            all_pass = True
            for code, ok, desc in results:
                status = "PASS" if ok else "FAIL"
                if not ok and not code.startswith("PRE-"):
                    all_pass = False
                print(f"[{status}] {code}: {desc}")
            print("=" * 60)
            print(f"总体结果: {'全部通过 ✅' if all_pass else '存在失败 ❌'}")
            print("=" * 60)
            return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
