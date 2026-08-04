"""API 冒烟测试脚本 - 使用 Flask test_client()
用法: USE_SQLITE=true python test_api.py
"""
import os
import sys
import json

os.environ.setdefault("USE_SQLITE", "true")

from app import create_app
from extensions import db


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
        FAILURES.append(name)


def auth_header(token):
    return {"Authorization": f"Bearer {token}"}


def json_of(resp):
    try:
        return resp.get_json()
    except Exception:
        try:
            return json.loads(resp.data.decode("utf-8"))
        except Exception:
            return {"_raw": resp.data[:500]}


def main():
    app = create_app()
    client = app.test_client()

    testuser01_token = None

    print("\n" + "=" * 60)
    print("  LIFE-SYSTEM BACKEND API SMOKE TESTS")
    print("=" * 60)

    # ======================================================================
    # a) 健康检查
    # ======================================================================
    print("\n[a] 健康检查 GET /api/health")
    r = client.get("/api/health")
    data = json_of(r)
    check("health 状态码 200", r.status_code == 200,
          f"got {r.status_code}, body={data}")
    check("health status=ok", data.get("status") == "ok",
          f"body={data}")
    check("health service=life-system", data.get("service") == "life-system",
          f"body={data}")

    # ======================================================================
    # b) 注册
    # ======================================================================
    print("\n[b] 注册 POST /api/auth/register")
    reg_payload = {
        "username": "testuser01",
        "password": "abc123",
        "real_name": "测试用户",
        "phone": "13800000001",
    }
    r = client.post("/api/auth/register", json=reg_payload)
    data = json_of(r)
    check("register 状态码 201", r.status_code == 201,
          f"got {r.status_code}, body={data}")
    if r.status_code == 201:
        check("register 含 token", "token" in data and bool(data["token"]),
              f"body={data}")
        check("register 含 user.id", "user" in data and "id" in data["user"],
              f"body={data}")
        testuser01_id = data["user"]["id"] if "user" in data else None
        testuser01_token = data.get("token")

    # 重复注册 409
    r2 = client.post("/api/auth/register", json=reg_payload)
    check("register 重复 409", r2.status_code == 409,
          f"got {r2.status_code}, body={json_of(r2)}")

    # 密码 5 位 -> 400
    r3 = client.post("/api/auth/register", json={
        "username": "testuser_short",
        "password": "12345",
    })
    check("register 密码 5 位 -> 400", r3.status_code == 400,
          f"got {r3.status_code}, body={json_of(r3)}")

    # ======================================================================
    # c) 登录
    # ======================================================================
    print("\n[c] 登录 POST /api/auth/login")
    r = client.post("/api/auth/login", json={
        "username": "demo",
        "password": "demo123",
    })
    data = json_of(r)
    check("login demo 状态码 200", r.status_code == 200,
          f"got {r.status_code}, body={data}")
    check("login demo 含 token", "token" in data and bool(data["token"]),
          f"body={data}")
    demo_token = data.get("token") if r.status_code == 200 else None

    # 错误密码 401
    r2 = client.post("/api/auth/login", json={
        "username": "demo",
        "password": "wrongpass",
    })
    check("login 错误密码 401", r2.status_code == 401,
          f"got {r2.status_code}, body={json_of(r2)}")

    # ======================================================================
    # d) /api/auth/me
    # ======================================================================
    print("\n[d] GET /api/auth/me")
    r = client.get("/api/auth/me", headers=auth_header(demo_token) if demo_token else {})
    data = json_of(r)
    check("me 带 token 状态码 200", r.status_code == 200,
          f"got {r.status_code}, body={data}")
    if r.status_code == 200:
        check("me 返回 user 字段", "user" in data, f"body={data}")
        if "user" in data:
            check("me user.username=demo", data["user"].get("username") == "demo",
                  f"user={data['user']}")

    # 无 token -> 401
    r2 = client.get("/api/auth/me")
    check("me 无 token -> 401", r2.status_code == 401,
          f"got {r2.status_code}, body={json_of(r2)}")

    # ======================================================================
    # e) /api/households/mine
    # ======================================================================
    print("\n[e] GET /api/households/mine")
    r = client.get("/api/households/mine", headers=auth_header(demo_token))
    data = json_of(r)
    check("households/mine 状态码 200", r.status_code == 200,
          f"got {r.status_code}, body={data}")
    households = data.get("households", []) if isinstance(data, dict) else []
    check("households 至少 1 户", len(households) >= 1,
          f"len={len(households)}")
    if households:
        h = households[0]
        check("household 含 household_no", bool(h.get("household_no")),
              f"h={h}")
        meters = h.get("meters", [])
        check("household 含 3 个 meters", len(meters) == 3,
              f"meters len={len(meters)}, meters={meters}")
        types = {m.get("type") for m in meters}
        check("meters 覆盖电水气", types == {"electricity", "water", "gas"},
              f"types={types}")
        for m in meters:
            check(f"meter[{m.get('type')}] meter_no 非空",
                  bool(m.get("meter_no")), f"meter={m}")

    # ======================================================================
    # f) /api/bills
    # ======================================================================
    print("\n[f] GET /api/bills")
    r = client.get("/api/bills?type=electricity&status=unpaid",
                   headers=auth_header(demo_token))
    data = json_of(r)
    check("bills?type=electricity&status=unpaid 状态码 200",
          r.status_code == 200, f"got {r.status_code}, body={data}")
    bills_electric_unpaid = data.get("bills", []) if isinstance(data, dict) else []
    check("返回 bills 数组", isinstance(bills_electric_unpaid, list),
          f"bills type={type(bills_electric_unpaid)}")
    for b in bills_electric_unpaid:
        for key in ("id", "type", "period", "usage_amount", "amount", "status"):
            check(f"bill[{b.get('id')}] 含 {key}", key in b,
                  f"bill keys={list(b.keys())}")

    # 无参请求检查 period 倒序
    r2 = client.get("/api/bills", headers=auth_header(demo_token))
    data2 = json_of(r2)
    bills_all = data2.get("bills", []) if isinstance(data2, dict) else []
    check("bills 无参 状态码 200", r2.status_code == 200,
          f"got {r2.status_code}, body={data2}")
    if len(bills_all) >= 2:
        periods = [b.get("period") for b in bills_all]
        check("bills period 倒序", periods == sorted(periods, reverse=True),
              f"periods={periods}")

    # ======================================================================
    # g) GET /api/bills/{bill_id}
    # ======================================================================
    print("\n[g] GET /api/bills/{bill_id} 详情")
    demo_unpaid_bill_id = None
    if bills_electric_unpaid:
        demo_unpaid_bill_id = bills_electric_unpaid[0]["id"]
    else:
        # fallback: search for any unpaid
        for b in bills_all:
            if b.get("status") == "unpaid":
                demo_unpaid_bill_id = b["id"]
                break

    check("存在 unpaid bill_id 可用于详情", demo_unpaid_bill_id is not None,
          f"unpaid bills electric={bills_electric_unpaid}, all_unpaid="
          f"{[b for b in bills_all if b.get('status')=='unpaid']}")

    if demo_unpaid_bill_id is not None:
        r = client.get(f"/api/bills/{demo_unpaid_bill_id}",
                       headers=auth_header(demo_token))
        data = json_of(r)
        check(f"bills/{demo_unpaid_bill_id} 状态码 200",
              r.status_code == 200, f"got {r.status_code}, body={data}")
        if r.status_code == 200:
            bill_wrap = data.get("bill", {})
            check("bill 详情含 breakdown",
                  "breakdown" in bill_wrap and isinstance(bill_wrap["breakdown"], list)
                  and len(bill_wrap["breakdown"]) > 0,
                  f"breakdown={bill_wrap.get('breakdown')}")
            check("bill 详情含 household", "household" in bill_wrap,
                  f"bill keys={list(bill_wrap.keys())}")
            check("bill 详情含 meter", "meter" in bill_wrap,
                  f"bill keys={list(bill_wrap.keys())}")
            check("bill 详情 payment 为 null（未付）",
                  "payment" not in bill_wrap or bill_wrap["payment"] is None,
                  f"payment={bill_wrap.get('payment')}")
            bd = bill_wrap.get("breakdown", [])
            for item in bd:
                for key in ("tier", "min_usage", "max_usage",
                            "unit_price", "usage_in_tier", "subtotal"):
                    check(f"breakdown 项含 {key}", key in item,
                          f"bd item keys={list(item.keys())}, item={item}")

    # ======================================================================
    # h) POST /api/bills/{bill_id}/pay
    # ======================================================================
    print("\n[h] POST /api/bills/{bill_id}/pay 支付")
    paid_bill_id = None
    if demo_unpaid_bill_id is not None:
        r = client.post(f"/api/bills/{demo_unpaid_bill_id}/pay",
                        headers=auth_header(demo_token), json={})
        data = json_of(r)
        check(f"pay bill {demo_unpaid_bill_id} 状态码 200",
              r.status_code == 200, f"got {r.status_code}, body={data}")
        if r.status_code == 200:
            tx_no = data.get("transaction_no")
            paid_at = data.get("paid_at")
            bill_back = data.get("bill", {})
            check("pay 返回 transaction_no 非空",
                  bool(tx_no), f"tx_no={tx_no}")
            check("pay 返回 paid_at 非空", bool(paid_at), f"paid_at={paid_at}")
            check("pay 返回 bill.status == paid",
                  bill_back.get("status") == "paid",
                  f"bill_back={bill_back}")
            paid_bill_id = demo_unpaid_bill_id

    # 重复支付同一 bill 400
    if paid_bill_id is not None:
        r2 = client.post(f"/api/bills/{paid_bill_id}/pay",
                         headers=auth_header(demo_token))
        check("重复支付 -> 400", r2.status_code == 400,
              f"got {r2.status_code}, body={json_of(r2)}")

    # ======================================================================
    # i) 横向越权
    # ======================================================================
    print("\n[i] 横向越权验证")
    # 注册 testuser02
    r = client.post("/api/auth/register", json={
        "username": "testuser02",
        "password": "abc1234",
        "real_name": "测试用户02",
        "phone": "13800000002",
    })
    data_reg2 = json_of(r)
    check("register testuser02 成功", r.status_code == 201,
          f"got {r.status_code}, body={data_reg2}")
    testuser02_token = data_reg2.get("token") if r.status_code == 201 else None

    if testuser02_token and demo_unpaid_bill_id is not None:
        # 用 testuser02 访问 demo 的 bill 详情
        r1 = client.get(f"/api/bills/{demo_unpaid_bill_id}",
                        headers=auth_header(testuser02_token))
        check("横向越权: GET bill -> 403", r1.status_code == 403,
              f"got {r1.status_code}, body={json_of(r1)}")
        # 如果 demo_unpaid_bill_id 已经支付, 找另外一个未付
        alt_unpaid = None
        for b in bills_all:
            if b.get("status") == "unpaid" and b["id"] != paid_bill_id:
                alt_unpaid = b["id"]
                break
        target_pay_id = alt_unpaid or (paid_bill_id if paid_bill_id else demo_unpaid_bill_id)
        if target_pay_id:
            r2 = client.post(f"/api/bills/{target_pay_id}/pay",
                             headers=auth_header(testuser02_token), json={})
            # 如果已经支付, 400 也算合理, 但优先 403
            ok_forbid = r2.status_code == 403
            already_paid_but_forbid_check = (r2.status_code == 400) and (paid_bill_id == target_pay_id)
            check("横向越权: POST pay -> 403 (或已付400但bill是已付)",
                  ok_forbid or already_paid_but_forbid_check,
                  f"got {r2.status_code}, body={json_of(r2)}, target_pay_id={target_pay_id}, paid_bill_id={paid_bill_id}")

    # ======================================================================
    # j) GET /api/rules
    # ======================================================================
    print("\n[j] GET /api/rules")
    r = client.get("/api/rules")
    data = json_of(r)
    check("rules 状态码 200", r.status_code == 200,
          f"got {r.status_code}, body={data}")
    rules = data.get("rules", []) if isinstance(data, dict) else []
    check("rules 长度为 8 (电3+水2+气3)", len(rules) == 8,
          f"len={len(rules)}, rules={rules}")

    r2 = client.get("/api/rules?type=water")
    data2 = json_of(r2)
    rules_water = data2.get("rules", []) if isinstance(data2, dict) else []
    check("rules?type=water 只返回 2 条", len(rules_water) == 2,
          f"len={len(rules_water)}, rules={rules_water}")
    for wr in rules_water:
        check("water rule type=water", wr.get("type") == "water",
              f"rule={wr}")

    # ======================================================================
    # k) POST /api/repairs 创建报修
    # ======================================================================
    print("\n[k] POST /api/repairs 创建报修")
    repair_payload = {
        "type": "electricity",
        "description": "测试报修-客厅灯不亮",
        "phone": "13900001111",
        "urgency": "normal",
    }
    r = client.post("/api/repairs", json=repair_payload,
                    headers=auth_header(demo_token))
    data = json_of(r)
    check("create repair 状态码 201", r.status_code == 201,
          f"got {r.status_code}, body={data}")
    if r.status_code == 201:
        new_repair = data.get("repair", {})
        new_repair_id = new_repair.get("id")
        check("repair 含 id", "id" in new_repair, f"repair={new_repair}")

    # 缺 description -> 400
    r2 = client.post("/api/repairs", json={
        "type": "electricity",
        "phone": "13900001111",
    }, headers=auth_header(demo_token))
    check("repair 缺 description -> 400", r2.status_code == 400,
          f"got {r2.status_code}, body={json_of(r2)}")

    # 缺 phone -> 400
    r3 = client.post("/api/repairs", json={
        "type": "electricity",
        "description": "测试",
    }, headers=auth_header(demo_token))
    check("repair 缺 phone -> 400", r3.status_code == 400,
          f"got {r3.status_code}, body={json_of(r3)}")

    # ======================================================================
    # l) GET /api/repairs 列表
    # ======================================================================
    print("\n[l] GET /api/repairs 列表")
    r = client.get("/api/repairs", headers=auth_header(demo_token))
    data = json_of(r)
    check("repairs 列表状态码 200", r.status_code == 200,
          f"got {r.status_code}, body={data}")
    repairs_list = data.get("repairs", []) if isinstance(data, dict) else []
    check("repairs 含新工单（至少 3+1 条种子+新）", len(repairs_list) >= 4,
          f"len={len(repairs_list)}")
    if len(repairs_list) >= 2:
        times = [r_.get("created_at") for r_ in repairs_list]
        check("repairs 按 created_at 倒序（首条最新）",
              times == sorted(times, reverse=True),
              f"times={times}")
    if repairs_list:
        check(f"首条 repair 状态 pending",
              repairs_list[0].get("status") == "pending",
              f"first repair={repairs_list[0]}")

    # ======================================================================
    # m) GET /api/dashboard
    # ======================================================================
    print("\n[m] GET /api/dashboard 概览")
    r = client.get("/api/dashboard", headers=auth_header(demo_token))
    data = json_of(r)
    check("dashboard 状态码 200", r.status_code == 200,
          f"got {r.status_code}, body={data}")
    if r.status_code == 200:
        check("dashboard 含 unpaid_total", "unpaid_total" in data,
              f"keys={list(data.keys())}")
        check("dashboard 含 unpaid_count", "unpaid_count" in data,
              f"keys={list(data.keys())}")
        tmu = data.get("this_month_usage", {})
        check("dashboard 含 this_month_usage（电水气）",
              isinstance(tmu, dict)
              and all(k in tmu for k in ("electricity", "water", "gas")),
              f"this_month_usage={tmu}")
        rs = data.get("repair_stats", {})
        check("dashboard repair_stats 含 pending/processing/resolved",
              isinstance(rs, dict)
              and all(k in rs for k in ("pending", "processing", "resolved")),
              f"repair_stats={rs}")
        trends = data.get("trends", [])
        check("dashboard trends 长度为 6", len(trends) == 6,
              f"trends len={len(trends)}, trends={trends}")
        for t in trends:
            check("trend 项含 period", "period" in t, f"t={t}")
            check("trend 项含 usage", "usage" in t, f"t={t}")

    # ======================================================================
    # n) testuser01 访问 demo 的 repair_id 横向越权
    # ======================================================================
    print("\n[n] 新增: testuser01 访问 demo repair_id 横向越权")
    # 用 testuser01 token
    tu01_r = client.post("/api/auth/login", json={
        "username": "testuser01",
        "password": "abc123",
    })
    tu01_data = json_of(tu01_r)
    testuser01_token = tu01_data.get("token") if tu01_r.status_code == 200 else None
    if not testuser01_token and "testuser01_token" in dir():
        testuser01_token = locals().get("testuser01_token")
    check("testuser01 可登录拿到 token", bool(testuser01_token),
          f"login resp={tu01_data}")

    if testuser01_token and repairs_list:
        demo_repair_id = repairs_list[0]["id"]
        r_forbid = client.get(f"/api/repairs/{demo_repair_id}",
                              headers=auth_header(testuser01_token))
        check("testuser01 访问 demo repair_id -> 403",
              r_forbid.status_code == 403,
              f"got {r_forbid.status_code}, body={json_of(r_forbid)}")

    # ======================================================================
    # 汇总
    # ======================================================================
    print("\n" + "=" * 60)
    print(f"  SUMMARY: PASS={PASS} / FAIL={FAIL}")
    print("=" * 60)
    if FAILURES:
        print("  失败用例:")
        for idx, f in enumerate(FAILURES, 1):
            print(f"    {idx}. {f}")
    print()
    sys.exit(0 if FAIL == 0 else 1)


if __name__ == "__main__":
    main()
