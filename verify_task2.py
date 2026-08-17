#!/usr/bin/env python3
"""Task2 验证脚本：用户认证系统"""
import requests
import json
import sys

BASE_URL = "http://localhost:5000"

results = {}


def print_result(name, passed, detail=""):
    status = "✅ 通过" if passed else "❌ 失败"
    results[name] = {"passed": passed, "detail": detail}
    print(f"{name}: {status} - {detail}")


print("=" * 60)
print("Task 2 验证：用户认证系统")
print("=" * 60)

# 1. 健康检查
print("\n【Checkpoint 2.1】健康检查")
try:
    resp = requests.get(f"{BASE_URL}/api/health", timeout=5)
    data = resp.json()
    passed = resp.status_code == 200 and data.get("status") == "ok"
    print_result("Checkpoint 2.1 健康检查", passed,
                 f"status={resp.status_code}, body={data}")
except Exception as e:
    print_result("Checkpoint 2.1 健康检查", False, f"异常: {e}")

# 2. 注册接口测试
print("\n【TR-2.1】注册接口测试")

# 2.1.1 合法注册
print("\n  TR-2.1.1 合法注册")
try:
    resp = requests.post(f"{BASE_URL}/api/auth/register", json={
        "username": "testuser99",
        "password": "123456",
        "confirm_password": "123456",
        "real_name": "测试用户",
        "phone": "13800000001"
    }, timeout=5)
    data = resp.json()
    has_token = "access_token" in data and bool(data.get("access_token"))
    has_user_id = "user" in data and "id" in (data.get("user") or {})
    passed = resp.status_code == 201 and has_token and has_user_id
    testuser99_token = data.get("access_token") if passed else None
    print_result("TR-2.1.1 合法注册", passed,
                 f"status={resp.status_code}, access_token={'有' if has_token else '无'}, user.id={'有' if has_user_id else '无'}")
except Exception as e:
    testuser99_token = None
    print_result("TR-2.1.1 合法注册", False, f"异常: {e}")

# 2.1.2 短用户名
print("\n  TR-2.1.2 短用户名（2位）")
try:
    resp = requests.post(f"{BASE_URL}/api/auth/register", json={
        "username": "ab",
        "password": "123456"
    }, timeout=5)
    data = resp.json()
    has_msg = "msg" in data
    msg_correct = "用户名长度至少 3 位" in (data.get("msg") or "")
    passed = resp.status_code == 400 and has_msg and msg_correct
    print_result("TR-2.1.2 短用户名", passed,
                 f"status={resp.status_code}, msg={data.get('msg') if has_msg else '缺失msg'}")
except Exception as e:
    print_result("TR-2.1.2 短用户名", False, f"异常: {e}")

# 2.1.3 短密码
print("\n  TR-2.1.3 短密码（3位）")
try:
    resp = requests.post(f"{BASE_URL}/api/auth/register", json={
        "username": "testx",
        "password": "123"
    }, timeout=5)
    data = resp.json()
    has_msg = "msg" in data
    msg_correct = "密码长度至少 6 位" in (data.get("msg") or "")
    passed = resp.status_code == 400 and has_msg and msg_correct
    print_result("TR-2.1.3 短密码", passed,
                 f"status={resp.status_code}, msg={data.get('msg') if has_msg else '缺失msg'}")
except Exception as e:
    print_result("TR-2.1.3 短密码", False, f"异常: {e}")

# 2.1.4 confirm不匹配
print("\n  TR-2.1.4 两次密码不一致")
try:
    resp = requests.post(f"{BASE_URL}/api/auth/register", json={
        "username": "testy",
        "password": "123456",
        "confirm_password": "000000"
    }, timeout=5)
    data = resp.json()
    has_msg = "msg" in data
    passed = resp.status_code == 400 and has_msg
    print_result("TR-2.1.4 两次密码不一致", passed,
                 f"status={resp.status_code}, msg={data.get('msg') if has_msg else '缺失msg'}")
except Exception as e:
    print_result("TR-2.1.4 两次密码不一致", False, f"异常: {e}")

# 2.1.5 重复用户名
print("\n  TR-2.1.5 重复用户名（testuser99）")
try:
    resp = requests.post(f"{BASE_URL}/api/auth/register", json={
        "username": "testuser99",
        "password": "123456",
        "confirm_password": "123456",
        "real_name": "测试用户",
        "phone": "13800000001"
    }, timeout=5)
    data = resp.json()
    has_msg = "msg" in data
    msg_correct = "用户名已存在" in (data.get("msg") or "")
    passed = resp.status_code == 409 and has_msg and msg_correct
    print_result("TR-2.1.5 重复用户名", passed,
                 f"status={resp.status_code}, msg={data.get('msg') if has_msg else '缺失msg'}")
except Exception as e:
    print_result("TR-2.1.5 重复用户名", False, f"异常: {e}")

# 3. 登录接口测试
print("\n【TR-2.2】登录接口测试")

# 2.2.1 正常登录
print("\n  TR-2.2.1 正常登录 demo/demo123")
try:
    resp = requests.post(f"{BASE_URL}/api/auth/login", json={
        "username": "demo",
        "password": "demo123"
    }, timeout=5)
    data = resp.json()
    has_token = "access_token" in data and bool(data.get("access_token"))
    passed = resp.status_code == 200 and has_token
    demo_token = data.get("access_token") if passed else None
    print_result("TR-2.2.1 正常登录", passed,
                 f"status={resp.status_code}, access_token={'有' if has_token else '无'}")
except Exception as e:
    demo_token = None
    print_result("TR-2.2.1 正常登录", False, f"异常: {e}")

# 2.2.2 错密码
print("\n  TR-2.2.2 错密码 demo/wrongpass")
try:
    resp = requests.post(f"{BASE_URL}/api/auth/login", json={
        "username": "demo",
        "password": "wrongpass"
    }, timeout=5)
    data = resp.json()
    has_msg = "msg" in data
    msg_correct = "用户名或密码错误" in (data.get("msg") or "")
    passed = resp.status_code == 401 and has_msg and msg_correct
    print_result("TR-2.2.2 错密码", passed,
                 f"status={resp.status_code}, msg={data.get('msg') if has_msg else '缺失msg'}")
except Exception as e:
    print_result("TR-2.2.2 错密码", False, f"异常: {e}")

# 4. JWT 鉴权测试
print("\n【TR-2.3】JWT鉴权测试")

# 2.3.1 不带token
print("\n  TR-2.3.1 不带 token 访问 /api/auth/me")
try:
    resp = requests.get(f"{BASE_URL}/api/auth/me", timeout=5)
    passed = resp.status_code == 401
    print_result("TR-2.3.1 不带token", passed,
                 f"status={resp.status_code}")
except Exception as e:
    print_result("TR-2.3.1 不带token", False, f"异常: {e}")

# 2.3.2 带正确token
print("\n  TR-2.3.2 带 Bearer <demo_token> 访问 /api/auth/me")
try:
    resp = requests.get(f"{BASE_URL}/api/auth/me", headers={
        "Authorization": f"Bearer {demo_token}"
    }, timeout=5) if demo_token else None
    if resp is None:
        print_result("TR-2.3.2 带token", False, "无demo_token（登录失败）")
    else:
        data = resp.json()
        username_ok = data.get("user", {}).get("username") == "demo"
        passed = resp.status_code == 200 and username_ok
        print_result("TR-2.3.2 带token", passed,
                     f"status={resp.status_code}, user.username={data.get('user', {}).get('username')}")
except Exception as e:
    print_result("TR-2.3.2 带token", False, f"异常: {e}")

# 5. 户号+表计自动创建
print("\n【TR-2.4】注册自动创建户号+3表计")

print("\n  TR-2.4 用 testuser99 token 请求 GET /api/households/mine")
try:
    resp = requests.get(f"{BASE_URL}/api/households/mine", headers={
        "Authorization": f"Bearer {testuser99_token}"
    }, timeout=5) if testuser99_token else None
    if resp is None:
        print_result("TR-2.4 户号+表计", False, "无testuser99_token（注册失败）")
    else:
        data = resp.json()
        households = data.get("households", [])
        hh_count_ok = len(households) == 1
        hh_no_ok = bool(households[0].get("household_no")) if hh_count_ok else False
        meters = households[0].get("meters", []) if hh_count_ok else []
        meters_count_ok = len(meters) == 3
        meter_types = sorted([m.get("type") for m in meters]) if meters_count_ok else []
        types_ok = meter_types == ["electricity", "gas", "water"]
        passed = resp.status_code == 200 and hh_count_ok and hh_no_ok and meters_count_ok and types_ok
        print_result("TR-2.4 户号+表计", passed,
                     f"status={resp.status_code}, households={len(households)}, "
                     f"household_no={'非空' if hh_no_ok else '空'}, "
                     f"meters={len(meters)}, types={meter_types}")
except Exception as e:
    print_result("TR-2.4 户号+表计", False, f"异常: {e}")

# 输出总结
print("\n" + "=" * 60)
print("验证结果汇总")
print("=" * 60)
all_passed = True
for name, result in results.items():
    symbol = "✅" if result["passed"] else "❌"
    if not result["passed"]:
        all_passed = False
    print(f"{symbol} {name}: {'通过' if result['passed'] else '失败'}")

print("\n" + "=" * 60)
if all_passed:
    print("🎉 Task 2 全部通过！")
else:
    print("⚠️  Task 2 存在失败项，需要修复")
print("=" * 60)

sys.exit(0 if all_passed else 1)
