"""Task 2 认证模块验证脚本"""
import json
import time
import sys
import requests

BASE_URL = "http://127.0.0.1:5000"

def print_result(test_name, passed, details=""):
    status = "✅ PASS" if passed else "❌ FAIL"
    print(f"\n{status} - {test_name}")
    if details:
        print(f"  {details}")
    return passed

def is_jwt(token):
    if not isinstance(token, str) or not token:
        return False
    parts = token.split(".")
    return len(parts) == 3

def run_tests():
    all_passed = True
    timestamp = int(time.time())
    test_username = f"testuser_{timestamp}"
    test_password = "testpass123"

    print("=" * 60)
    print("Task 2 - 用户认证模块验证")
    print(f"测试用户名: {test_username}")
    print("=" * 60)

    # ===== TR-2.1 注册成功 =====
    print("\n--- TR-2.1 注册成功 ---")
    payload = {
        "username": test_username,
        "password": test_password,
        "confirm_password": test_password
    }
    resp = requests.post(f"{BASE_URL}/api/auth/register", json=payload)
    status_code = resp.status_code
    try:
        data = resp.json()
    except:
        data = resp.text

    tr21_pass = True
    if status_code != 201:
        tr21_pass = False
    access_token = data.get("access_token") if isinstance(data, dict) else None
    user = data.get("user") if isinstance(data, dict) else None

    if not access_token or not is_jwt(access_token):
        tr21_pass = False
    if not user or not isinstance(user, dict):
        tr21_pass = False
    else:
        if user.get("username") != test_username:
            tr21_pass = False
        if user.get("role") != "user":
            tr21_pass = False
        if "id" not in user:
            tr21_pass = False

    details = f"HTTP {status_code}, token={'OK(JWT)' if is_jwt(access_token) else 'FAIL'}, user.role={user.get('role') if user else 'N/A'}"
    if not print_result("TR-2.1 注册成功", tr21_pass, details):
        all_passed = False
        print(f"  响应详情: {json.dumps(data, ensure_ascii=False, indent=2) if isinstance(data, dict) else data}")

    user_id = user.get("id") if user else None

    # 验证 GET /api/auth/me
    tr21_me_pass = True
    if access_token:
        resp_me = requests.get(
            f"{BASE_URL}/api/auth/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        me_status = resp_me.status_code
        try:
            me_data = resp_me.json()
        except:
            me_data = resp_me.text
        me_user = me_data.get("user") if isinstance(me_data, dict) else None
        if me_status != 200 or not me_user or me_user.get("username") != test_username:
            tr21_me_pass = False
        me_details = f"HTTP {me_status}, me.username={me_user.get('username') if me_user else 'N/A'}"
    else:
        tr21_me_pass = False
        me_details = "无 token 可用"

    if not print_result("TR-2.1 /api/auth/me 验证", tr21_me_pass, me_details):
        all_passed = False
        if access_token:
            print(f"  响应详情: {json.dumps(me_data, ensure_ascii=False, indent=2) if isinstance(me_data, dict) else me_data}")

    # ===== TR-2.2 重复注册冲突 =====
    print("\n--- TR-2.2 重复注册冲突 ---")
    resp2 = requests.post(f"{BASE_URL}/api/auth/register", json=payload)
    try:
        data2 = resp2.json()
    except:
        data2 = resp2.text
    msg = data2.get("msg") if isinstance(data2, dict) else None
    tr22_pass = (resp2.status_code == 409 and msg == "用户名已存在")
    details = f"HTTP {resp2.status_code}, msg={msg}"
    if not print_result("TR-2.2 重复注册冲突", tr22_pass, details):
        all_passed = False
        print(f"  响应详情: {json.dumps(data2, ensure_ascii=False, indent=2) if isinstance(data2, dict) else data2}")

    # ===== TR-2.3 自动开户号和表计 =====
    print("\n--- TR-2.3 自动开户号和表计 ---")
    tr23_pass = True
    if user_id:
        sys.path.insert(0, "/workspace/backend")
        from app import create_app
        from extensions import db
        from models import User, Household, Meter

        app = create_app()
        with app.app_context():
            user_obj = User.query.get(user_id)
            if not user_obj:
                tr23_pass = False
                details = f"users 表中未找到 user_id={user_id}"
            else:
                households = Household.query.filter_by(user_id=user_id).all()
                if len(households) != 1:
                    tr23_pass = False
                    details = f"households 表记录数={len(households)}, 期望 1"
                else:
                    hh = households[0]
                    if not hh.household_no:
                        tr23_pass = False
                        details = "household_no 为空"
                    else:
                        # 检查唯一
                        dup_hh = Household.query.filter_by(household_no=hh.household_no).all()
                        if len(dup_hh) != 1:
                            tr23_pass = False
                            details = f"household_no={hh.household_no} 不唯一"
                        else:
                            meters = Meter.query.filter_by(household_id=hh.id).all()
                            if len(meters) != 3:
                                tr23_pass = False
                                details = f"meters 表记录数={len(meters)}, 期望 3"
                            else:
                                types = [m.type for m in meters]
                                expected_types = {"electricity", "water", "gas"}
                                if set(types) != expected_types:
                                    tr23_pass = False
                                    details = f"meter types={types}, 期望 {expected_types}"
                                else:
                                    all_meter_ok = True
                                    meter_nos = []
                                    for m in meters:
                                        if not m.meter_no:
                                            all_meter_ok = False
                                        meter_nos.append(m.meter_no)
                                        dup_m = Meter.query.filter_by(meter_no=m.meter_no).all()
                                        if len(dup_m) != 1:
                                            all_meter_ok = False
                                    if not all_meter_ok:
                                        tr23_pass = False
                                        details = f"meter_no 校验失败，meter_nos={meter_nos}"
                                    else:
                                        details = f"hh_no={hh.household_no}, meters={[(m.type, m.meter_no) for m in meters]}"
    else:
        tr23_pass = False
        details = "user_id 无效（注册可能失败）"

    if not print_result("TR-2.3 自动开户号和表计", tr23_pass, details):
        all_passed = False

    # ===== TR-2.4 登录与未授权 =====
    print("\n--- TR-2.4 登录与未授权 ---")

    # 登录成功 demo/demo123
    resp_login_ok = requests.post(f"{BASE_URL}/api/auth/login", json={
        "username": "demo",
        "password": "demo123"
    })
    try:
        login_ok_data = resp_login_ok.json()
    except:
        login_ok_data = resp_login_ok.text
    tr24_login_pass = (resp_login_ok.status_code == 200 and 
                       isinstance(login_ok_data, dict) and 
                       is_jwt(login_ok_data.get("access_token")))
    details = f"HTTP {resp_login_ok.status_code}, token={'OK(JWT)' if isinstance(login_ok_data, dict) and is_jwt(login_ok_data.get('access_token')) else 'FAIL'}"
    if not print_result("TR-2.4 登录成功 demo/demo123", tr24_login_pass, details):
        all_passed = False
        print(f"  响应详情: {json.dumps(login_ok_data, ensure_ascii=False, indent=2) if isinstance(login_ok_data, dict) else login_ok_data}")

    # 登录失败 demo/wrongpass
    resp_login_fail = requests.post(f"{BASE_URL}/api/auth/login", json={
        "username": "demo",
        "password": "wrongpass"
    })
    tr24_loginfail_pass = (resp_login_fail.status_code == 401)
    details = f"HTTP {resp_login_fail.status_code}"
    if not print_result("TR-2.4 登录失败 demo/wrongpass", tr24_loginfail_pass, details):
        all_passed = False
        try:
            print(f"  响应详情: {json.dumps(resp_login_fail.json(), ensure_ascii=False, indent=2)}")
        except:
            print(f"  响应详情: {resp_login_fail.text}")

    # GET /api/auth/me 不带 Authorization
    resp_me_noauth = requests.get(f"{BASE_URL}/api/auth/me")
    tr24_noauth_pass = resp_me_noauth.status_code in (401, 422)
    details = f"HTTP {resp_me_noauth.status_code}"
    if not print_result("TR-2.4 /me 未授权访问", tr24_noauth_pass, details):
        all_passed = False
        try:
            print(f"  响应详情: {json.dumps(resp_me_noauth.json(), ensure_ascii=False, indent=2)}")
        except:
            print(f"  响应详情: {resp_me_noauth.text}")

    # ===== TR-2.5 随机冲突 fallback 逻辑 =====
    print("\n--- TR-2.5 随机冲突 fallback 逻辑 ---")
    tr25_pass = True
    details_parts = []
    try:
        import inspect
        sys.path.insert(0, "/workspace/backend")
        from routes import auth

        hh_src = inspect.getsource(auth._generate_household_no)
        meter_src = inspect.getsource(auth._generate_meter_no)

        if "for _ in range(100)" not in hh_src or "f\"U{user_id}\"" not in hh_src:
            tr25_pass = False
            details_parts.append("_generate_household_no 缺少循环重试或 fallback 逻辑")
        else:
            details_parts.append("household_no: 有100次循环重试 + U{id} fallback")

        if "for _ in range(100)" not in meter_src or "suffix = 1000" not in meter_src:
            tr25_pass = False
            details_parts.append("_generate_meter_no 缺少循环重试或 fallback 逻辑")
        else:
            details_parts.append("meter_no: 有100次循环重试 + 1000递增 fallback")
    except Exception as e:
        tr25_pass = False
        details_parts.append(f"代码检查异常: {e}")

    details = "; ".join(details_parts)
    if not print_result("TR-2.5 随机冲突 fallback 逻辑", tr25_pass, details):
        all_passed = False

    # ===== 额外输入校验 =====
    print("\n--- 额外输入校验 ---")

    # 用户名长度不足 3 位
    resp_short_user = requests.post(f"{BASE_URL}/api/auth/register", json={
        "username": "ab",
        "password": "testpass123",
        "confirm_password": "testpass123"
    })
    short_user_pass = resp_short_user.status_code == 400
    details = f"HTTP {resp_short_user.status_code}"
    if not print_result("用户名长度不足3位 → 400", short_user_pass, details):
        all_passed = False
        try:
            print(f"  响应详情: {json.dumps(resp_short_user.json(), ensure_ascii=False, indent=2)}")
        except:
            print(f"  响应详情: {resp_short_user.text}")

    # 密码长度不足 6 位
    resp_short_pwd = requests.post(f"{BASE_URL}/api/auth/register", json={
        "username": f"shortpwd_{timestamp}",
        "password": "12345",
        "confirm_password": "12345"
    })
    short_pwd_pass = resp_short_pwd.status_code == 400
    details = f"HTTP {resp_short_pwd.status_code}"
    if not print_result("密码长度不足6位 → 400", short_pwd_pass, details):
        all_passed = False
        try:
            print(f"  响应详情: {json.dumps(resp_short_pwd.json(), ensure_ascii=False, indent=2)}")
        except:
            print(f"  响应详情: {resp_short_pwd.text}")

    # confirm_password 与 password 不一致
    resp_mismatch = requests.post(f"{BASE_URL}/api/auth/register", json={
        "username": f"mismatch_{timestamp}",
        "password": "testpass123",
        "confirm_password": "differentpass"
    })
    mismatch_pass = resp_mismatch.status_code == 400
    details = f"HTTP {resp_mismatch.status_code}"
    if not print_result("密码不一致 → 400", mismatch_pass, details):
        all_passed = False
        try:
            print(f"  响应详情: {json.dumps(resp_mismatch.json(), ensure_ascii=False, indent=2)}")
        except:
            print(f"  响应详情: {resp_mismatch.text}")

    # ===== 最终结论 =====
    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 Task 2 全部通过！")
    else:
        print("⚠️ Task 2 存在未通过项，请检查以上 FAIL 项目")
    print("=" * 60)
    return all_passed

if __name__ == "__main__":
    success = run_tests()
    sys.exit(0 if success else 1)
