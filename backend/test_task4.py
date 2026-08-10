"""Task 4 验证脚本"""
import sys
import json

sys.path.insert(0, "/workspace/backend")

from app import create_app
from extensions import db
from models import Bill, Household, User

app = create_app("development")
client = app.test_client()


def login_demo():
    resp = client.post(
        "/api/auth/login",
        json={"username": "demo", "password": "demo123"},
    )
    assert resp.status_code == 200, f"登录失败: {resp.status_code} {resp.get_json()}"
    data = resp.get_json()
    return data["token"]


def test_households_mine(token):
    print("\n===== TR-4.1 GET /api/households/mine =====")
    resp = client.get(
        "/api/households/mine",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200, f"状态码错误: {resp.status_code}"
    data = resp.get_json()
    print(f"响应: {json.dumps(data, ensure_ascii=False, indent=2)}")

    households = data["households"]
    print(f"households 长度: {len(households)}")
    assert len(households) >= 1, "households 数组长度应 >= 1"

    h0 = households[0]
    meters = h0["meters"]
    print(f"第一个 household 的 meters 长度: {len(meters)}")
    assert len(meters) == 3, "meters 数组长度应为 3"

    meter_types = sorted([m["type"] for m in meters])
    print(f"meter.type 排序后: {meter_types}")
    assert meter_types == ["electricity", "gas", "water"], "meter 类型排序后应等于 ['electricity','gas','water']"

    for m in meters:
        assert "meter_no" in m and m["meter_no"], f"meter {m['type']} 缺少 meter_no"
        assert "current_reading" in m, f"meter {m['type']} 缺少 current_reading"
        print(f"  {m['type']}: meter_no={m['meter_no']}, current_reading={m['current_reading']}")

    print("✅ TR-4.1 PASSED")
    return True


def test_rules_electricity():
    print("\n===== TR-4.2 GET /api/rules?type=electricity =====")
    resp = client.get("/api/rules?type=electricity")
    assert resp.status_code == 200, f"状态码错误: {resp.status_code}"
    data = resp.get_json()
    print(f"响应: {json.dumps(data, ensure_ascii=False, indent=2)}")

    rules = data["rules"]
    print(f"rules 长度: {len(rules)}")
    assert len(rules) == 3, f"电价规则应为 3 条，实际 {len(rules)}"
    tiers = sorted([r["tier"] for r in rules])
    assert tiers == [1, 2, 3], f"电价 tier 应为 1,2,3，实际 {tiers}"

    print(f"rules[0].unit_price: {rules[0]['unit_price']}")
    assert abs(rules[0]["unit_price"] - 0.588) < 0.0001, "rules[0].unit_price 应为 0.588"

    example = data["example"]
    print(f"example.usage: {example['usage']}")
    assert example["usage"] == 250, "电价 example.usage 应为 250"

    print(f"example.amount: {example['amount']}")
    assert abs(example["amount"] - 150.50) < 0.02, f"example.amount 应≈150.50，实际 {example['amount']}"

    print(f"example.breakdown 长度: {len(example['breakdown'])}")
    assert len(example["breakdown"]) >= 2, "breakdown 长度应 >= 2"

    print("✅ TR-4.2 electricity PASSED")
    return True


def test_rules_water():
    print("\n===== TR-4.2 GET /api/rules?type=water =====")
    resp = client.get("/api/rules?type=water")
    assert resp.status_code == 200
    data = resp.get_json()
    print(f"响应: {json.dumps(data, ensure_ascii=False, indent=2)}")

    rules = data["rules"]
    print(f"rules 长度: {len(rules)}")
    assert len(rules) == 2, f"水价规则应为 2 条，实际 {len(rules)}"

    example = data["example"]
    print(f"example.usage: {example['usage']}")
    assert example["usage"] == 15, "水价 example.usage 应为 15"
    print(f"example.amount: {example['amount']}")

    print("✅ TR-4.2 water PASSED")
    return True


def test_rules_gas():
    print("\n===== TR-4.2 GET /api/rules?type=gas =====")
    resp = client.get("/api/rules?type=gas")
    assert resp.status_code == 200
    data = resp.get_json()
    print(f"响应: {json.dumps(data, ensure_ascii=False, indent=2)}")

    rules = data["rules"]
    print(f"rules 长度: {len(rules)}")
    assert len(rules) == 3, f"气价规则应为 3 条，实际 {len(rules)}"

    example = data["example"]
    print(f"example.usage: {example['usage']}")
    assert example["usage"] == 350, "气价 example.usage 应为 350"
    print(f"example.amount: {example['amount']}")

    print("✅ TR-4.2 gas PASSED")
    return True


def test_dashboard(token):
    print("\n===== TR-4.3 GET /api/dashboard =====")
    resp = client.get(
        "/api/dashboard",
        headers={"Authorization": f"Bearer {token}"},
    )
    assert resp.status_code == 200, f"状态码错误: {resp.status_code}"
    data = resp.get_json()
    print(f"响应: {json.dumps(data, ensure_ascii=False, indent=2)}")

    with app.app_context():
        demo_user = User.query.filter_by(username="demo").first()
        demo_households = Household.query.filter(
            Household.user_id == demo_user.id
        ).all()
        hids = [h.id for h in demo_households]
        unpaid_bills = Bill.query.filter(
            Bill.household_id.in_(hids), Bill.status == "unpaid"
        ).all()
        expected_unpaid_total = sum(float(b.amount) for b in unpaid_bills)
        expected_unpaid_count = len(unpaid_bills)
        print(f"\nDB 查询 demo 的 unpaid 账单:")
        print(f"  数量: {expected_unpaid_count}")
        for b in unpaid_bills:
            print(f"    {b.period} {b.type}: amount={float(b.amount)}")
        print(f"  总和: {expected_unpaid_total}")

    print(f"\nAPI 返回:")
    print(f"  unpaid_total: {data['unpaid_total']}")
    print(f"  unpaid_count: {data['unpaid_count']}")
    assert abs(data["unpaid_total"] - expected_unpaid_total) < 0.01, (
        f"unpaid_total 应为 {expected_unpaid_total}，实际 {data['unpaid_total']}"
    )
    assert data["unpaid_count"] == expected_unpaid_count, (
        f"unpaid_count 应为 {expected_unpaid_count}，实际 {data['unpaid_count']}"
    )
    assert data["unpaid_count"] == 6, f"unpaid_count 应为 6，实际 {data['unpaid_count']}"

    print(f"\n  repair_stats: {data['repair_stats']}")
    rs = data["repair_stats"]
    assert "pending" in rs and rs["pending"] >= 1, f"repair_stats.pending 应 >= 1，实际 {rs.get('pending')}"
    assert "processing" in rs and rs["processing"] >= 1, f"repair_stats.processing 应 >= 1，实际 {rs.get('processing')}"
    assert "resolved" in rs and rs["resolved"] >= 1, f"repair_stats.resolved 应 >= 1，实际 {rs.get('resolved')}"

    print(f"\n  this_month_usage keys: {list(data['this_month_usage'].keys())}")
    tmu = data["this_month_usage"]
    assert "electricity" in tmu, "this_month_usage 缺少 electricity"
    assert "water" in tmu, "this_month_usage 缺少 water"
    assert "gas" in tmu, "this_month_usage 缺少 gas"

    trends = data["trends"]
    print(f"\n  trends 长度: {len(trends)}")
    assert len(trends) == 6, f"trends 长度应为 6，实际 {len(trends)}"
    import re
    for i, t in enumerate(trends):
        period = t["period"]
        print(f"    [{i}] period={period}, usage={t['usage']}")
        assert re.match(r"^\d{4}-\d{2}$", period), f"period 格式应为 YYYY-MM，实际 {period}"
        assert "electricity" in t["usage"]
        assert "water" in t["usage"]
        assert "gas" in t["usage"]

    print("✅ TR-4.3 PASSED")
    return True


if __name__ == "__main__":
    with app.app_context():
        db.create_all()

    print("=" * 60)
    print("Task 4 验证开始")
    print("=" * 60)

    token = login_demo()
    print(f"登录成功，token: {token[:30]}...")

    all_passed = True
    all_passed &= test_households_mine(token)
    all_passed &= test_rules_electricity()
    all_passed &= test_rules_water()
    all_passed &= test_rules_gas()
    all_passed &= test_dashboard(token)

    print("\n" + "=" * 60)
    if all_passed:
        print("🎉 所有验证通过!")
    else:
        print("❌ 部分验证失败!")
        sys.exit(1)
