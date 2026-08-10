"""Task 3 验证脚本"""
import random
import string
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app
from extensions import db
from models import Household, Meter


def rand_username():
    return "testuser_" + "".join(random.choices(string.ascii_lowercase + string.digits, k=6))


def main():
    app = create_app()
    results = []

    with app.test_client() as client:
        with app.app_context():
            print("=" * 60)
            print("Task 3: 认证 API 验证")
            print("=" * 60)

            # TR-3.1 注册: 随机新用户名
            print("\n--- TR-3.1 注册验证 ---")
            username = rand_username()
            password = "test123"
            confirm_password = "test123"

            resp = client.post(
                "/api/auth/register",
                json={
                    "username": username,
                    "password": password,
                    "confirm_password": confirm_password,
                },
            )
            data = resp.get_json() or {}
            status_code = resp.status_code
            token_ok = "token" in data and len(data.get("token", "")) > 0
            user_id_ok = data.get("user", {}).get("id", 0) > 0
            result = (
                f"TR-3.1-1 新用户注册: HTTP {status_code} | "
                f"token存在={token_ok} | user.id>0={user_id_ok}"
            )
            passed = status_code == 201 and token_ok and user_id_ok
            results.append(("TR-3.1-1", passed, result))
            print(f"[{'PASS' if passed else 'FAIL'}] {result}")
            if status_code == 201:
                print(f"  response keys: {list(data.keys())}")
                print(f"  user.id: {data['user']['id']}, user.username: {data['user']['username']}")
            else:
                print(f"  data: {data}")

            # 查 DB: households 和 meters
            user_id = data["user"]["id"]
            households = Household.query.filter_by(user_id=user_id).all()
            hh_count = len(households)
            meter_types = sorted([m.type for h in households for m in h.meters])
            expected_types = ["electricity", "gas", "water"]
            result2 = (
                f"TR-3.2 自动创建户号表计: Household={hh_count}条 | "
                f"Meter类型={meter_types} (期望 {expected_types})"
            )
            passed2 = hh_count == 1 and meter_types == expected_types
            results.append(("TR-3.2", passed2, result2))
            print(f"\n[{'PASS' if passed2 else 'FAIL'}] {result2}")
            if households:
                print(f"  household_no: {households[0].household_no}")
                for m in households[0].meters:
                    print(f"  meter: {m.type} / {m.meter_no}")

            # 重复 POST 同用户名 => HTTP 409
            resp2 = client.post(
                "/api/auth/register",
                json={"username": username, "password": password},
            )
            data2 = resp2.get_json() or {}
            result3 = (
                f"TR-3.1-2 重复注册: HTTP {resp2.status_code} (期望409) | "
                f"msg={data2.get('msg', '')}"
            )
            passed3 = resp2.status_code == 409
            results.append(("TR-3.1-2", passed3, result3))
            print(f"\n[{'PASS' if passed3 else 'FAIL'}] {result3}")

            # 用户名 'ab'（<4） => HTTP 400
            resp3 = client.post(
                "/api/auth/register",
                json={"username": "ab", "password": "test123"},
            )
            data3 = resp3.get_json() or {}
            result4 = (
                f"TR-3.1-3 用户名过短(ab<4): HTTP {resp3.status_code} (期望400) | "
                f"msg={data3.get('msg', '')}"
            )
            passed4 = resp3.status_code == 400
            results.append(("TR-3.1-3", passed4, result4))
            print(f"[{'PASS' if passed4 else 'FAIL'}] {result4}")

            # TR-3.3 登录
            print("\n--- TR-3.3 登录验证 ---")
            resp_ok = client.post(
                "/api/auth/login",
                json={"username": "demo", "password": "demo123"},
            )
            data_ok = resp_ok.get_json() or {}
            token_ok_login = "token" in data_ok and len(data_ok.get("token", "")) > 0
            result5 = (
                f"TR-3.3-1 登录成功(demo/demo123): HTTP {resp_ok.status_code} (期望200) | "
                f"token存在={token_ok_login}"
            )
            passed5 = resp_ok.status_code == 200 and token_ok_login
            results.append(("TR-3.3-1", passed5, result5))
            print(f"[{'PASS' if passed5 else 'FAIL'}] {result5}")
            if resp_ok.status_code == 200:
                demo_token = data_ok["token"]
                print(f"  获取到 token 长度: {len(demo_token)}")
            else:
                demo_token = None
                print(f"  data: {data_ok}")

            resp_bad = client.post(
                "/api/auth/login",
                json={"username": "demo", "password": "wrong"},
            )
            data_bad = resp_bad.get_json() or {}
            result6 = (
                f"TR-3.3-2 登录失败(demo/wrong): HTTP {resp_bad.status_code} (期望401) | "
                f"msg={data_bad.get('msg', '')}"
            )
            passed6 = resp_bad.status_code == 401 and data_bad.get("msg") == "用户名或密码错误"
            results.append(("TR-3.3-2", passed6, result6))
            print(f"[{'PASS' if passed6 else 'FAIL'}] {result6}")

            # TR-3.4 当前用户
            print("\n--- TR-3.4 当前用户验证 ---")
            if demo_token:
                resp_me = client.get(
                    "/api/auth/me",
                    headers={"Authorization": f"Bearer {demo_token}"},
                )
                data_me = resp_me.get_json() or {}
                user_data = data_me.get("user", {})
                uname_ok = user_data.get("username") == "demo"
                result7 = (
                    f"TR-3.4-1 带Token获取当前用户: HTTP {resp_me.status_code} (期望200) | "
                    f"user.username={user_data.get('username')} (期望demo)"
                )
                passed7 = resp_me.status_code == 200 and uname_ok
                results.append(("TR-3.4-1", passed7, result7))
                print(f"[{'PASS' if passed7 else 'FAIL'}] {result7}")
            else:
                passed7 = False
                results.append(("TR-3.4-1", False, "TR-3.4-1 跳过：未获取到 demo token"))
                print("[SKIP] TR-3.4-1 跳过：未获取到 demo token")

            resp_me_no = client.get("/api/auth/me")
            result8 = (
                f"TR-3.4-2 不带Token访问: HTTP {resp_me_no.status_code} (期望401或422)"
            )
            passed8 = resp_me_no.status_code in (401, 422)
            results.append(("TR-3.4-2", passed8, result8))
            print(f"[{'PASS' if passed8 else 'FAIL'}] {result8}")

            # 汇总
            print("\n" + "=" * 60)
            print("验证结果汇总")
            print("=" * 60)
            all_pass = True
            for code, ok, desc in results:
                status = "PASS" if ok else "FAIL"
                if not ok:
                    all_pass = False
                print(f"[{status}] {code}: {desc}")
            print("=" * 60)
            print(f"总体结果: {'全部通过 ✅' if all_pass else '存在失败 ❌'}")
            print("=" * 60)
            return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
