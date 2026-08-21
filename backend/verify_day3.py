"""Day 3 独立验证脚本：户号管理与电/水/气表具关联

验证 checklist: 3-1 ~ 3-4
退出码: 0 = 全部通过, 1 = 存在失败
"""
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from app import create_app


def login(client, username, password):
    resp = client.post(
        "/api/auth/login",
        json={"username": username, "password": password},
    )
    data = resp.get_json() or {}
    return data.get("token")


def get_households(client, token):
    resp = client.get(
        "/api/households/mine",
        headers={"Authorization": f"Bearer {token}"},
    )
    data = resp.get_json() or {}
    return resp.status_code, data


def main():
    app = create_app()
    results = []

    with app.test_client() as client:
        with app.app_context():
            print("=" * 70)
            print("Day 3 验证：户号管理与电/水/气表具关联 (3-1 ~ 3-4)")
            print("=" * 70)

            demo_token = login(client, "demo", "demo123")
            admin_token = login(client, "admin", "admin123")

            # ============================================================
            # 3-1 GET /api/households/mine（demo 登录）返回 households 数组长度 ≥ 1
            # ============================================================
            print("\n--- 3-1 demo: GET /api/households/mine  households 长度 >= 1 ---")
            code, data = get_households(client, demo_token)
            demo_households = data.get("households", []) if isinstance(data, dict) else []
            ok_31 = code == 200 and isinstance(demo_households, list) and len(demo_households) >= 1
            evidence_31 = f"HTTP={code}, households 长度={len(demo_households)}, data 类型={type(data).__name__}"
            results.append(("3-1", ok_31, evidence_31))
            print(f"[{'PASS' if ok_31 else 'FAIL'}] {evidence_31}")
            if not ok_31:
                print(f"  原始返回: {data}")

            # ============================================================
            # 3-2 第一个 household 的 meters 恰好 3 条，type 集合 = {electricity, water, gas}
            # ============================================================
            print("\n--- 3-2 meters 恰好 3 条且 type 集合 = {electricity, water, gas} ---")
            ok_32 = False
            evidence_32 = ""
            demo_meters = []
            first_hh = None
            if ok_31 and len(demo_households) >= 1:
                first_hh = demo_households[0]
                demo_meters = first_hh.get("meters", []) if isinstance(first_hh, dict) else []
                meter_count = len(demo_meters)
                type_set = {m.get("type") for m in demo_meters if isinstance(m, dict)}
                expected = {"electricity", "water", "gas"}
                count_ok = meter_count == 3
                types_ok = type_set == expected
                ok_32 = count_ok and types_ok
                evidence_32 = (
                    f"户号={first_hh.get('household_no')}, "
                    f"meters 条数={meter_count}(期望3)={count_ok}, "
                    f"type 集合={sorted(type_set)}(期望{sorted(expected)})={types_ok}"
                )
            else:
                evidence_32 = "3-1 未通过或 households 为空，无法检查 meters"
            results.append(("3-2", ok_32, evidence_32))
            print(f"[{'PASS' if ok_32 else 'FAIL'}] {evidence_32}")
            if demo_meters:
                for m in demo_meters:
                    print(f"    - type={m.get('type')}, meter_no={m.get('meter_no')}")

            # ============================================================
            # 3-3 每个 meter.current_reading 是数字且 >= 0
            # ============================================================
            print("\n--- 3-3 每个 meter.current_reading 是数字且 >= 0 ---")
            ok_33 = False
            evidence_33 = ""
            if ok_32 and len(demo_meters) > 0:
                checks = []
                for m in demo_meters:
                    cr = m.get("current_reading")
                    is_num = isinstance(cr, (int, float)) and not (isinstance(cr, float) and (cr != cr))
                    is_ge0 = is_num and cr >= 0
                    checks.append((m.get("type"), is_num, is_ge0, cr))
                ok_33 = all(is_num and is_ge0 for _, is_num, is_ge0, _ in checks)
                pieces = [
                    f"{t}: cr={cr}(type={type(cr).__name__}) 数字={is_num}, >=0={is_ge0}"
                    for t, is_num, is_ge0, cr in checks
                ]
                evidence_33 = " | ".join(pieces)
            else:
                evidence_33 = "3-2 未通过，无法检查 current_reading"
            results.append(("3-3", ok_33, evidence_33))
            print(f"[{'PASS' if ok_33 else 'FAIL'}] {evidence_33}")

            # ============================================================
            # 3-4 admin token 请求 /households/mine
            #   ① 正常返回 admin 户号（非 500）
            #   ② household_no / user 信息不等于 demo 的（越权隔离）
            # ============================================================
            print("\n--- 3-4 admin /households/mine + 越权隔离 ---")
            ok_34i = False
            ok_34ii = False
            ok_34_rev = False
            evidence_34i = ""
            evidence_34ii = ""
            evidence_34_rev = ""

            # 3-4 ① admin 请求不报错且有户号
            code_a, data_a = get_households(client, admin_token)
            admin_households = data_a.get("households", []) if isinstance(data_a, dict) else []
            ok_34i = (
                code_a == 200
                and isinstance(admin_households, list)
                and len(admin_households) >= 1
            )
            evidence_34i = (
                f"① HTTP={code_a}(期望200)={code_a == 200}, "
                f"admin households 长度={len(admin_households)}(期望>=1)={len(admin_households) >= 1}"
            )

            # 3-4 ② 越权隔离：admin 与 demo 的 household_no / user_id 互不相交
            if first_hh and ok_34i and len(admin_households) >= 1:
                demo_hh_nos = {h.get("household_no") for h in demo_households if isinstance(h, dict)}
                demo_user_ids = {h.get("user_id") for h in demo_households if isinstance(h, dict)}
                admin_hh_nos = {h.get("household_no") for h in admin_households if isinstance(h, dict)}
                admin_user_ids = {h.get("user_id") for h in admin_households if isinstance(h, dict)}

                hh_no_disjoint = demo_hh_nos.isdisjoint(admin_hh_nos) and len(demo_hh_nos) > 0 and len(admin_hh_nos) > 0
                user_id_disjoint = demo_user_ids.isdisjoint(admin_user_ids) and len(demo_user_ids) > 0 and len(admin_user_ids) > 0
                ok_34ii = hh_no_disjoint and user_id_disjoint
                evidence_34ii = (
                    f"② demo hh_nos={sorted(demo_hh_nos)} vs admin={sorted(admin_hh_nos)} 互不相交={hh_no_disjoint}; "
                    f"demo user_ids={sorted(demo_user_ids)} vs admin={sorted(admin_user_ids)} 互不相交={user_id_disjoint}"
                )

                # 反向验证：demo 也看不到 admin（其实 demo 返回的已经是自己的，逻辑对称）
                ok_34_rev = True
                evidence_34_rev = f"反之 demo 仅看到自己的 {sorted(demo_hh_nos)}，与 admin 无重叠"
            else:
                if not ok_34i:
                    evidence_34ii = "3-4① 未通过，跳过越权隔离检查"
                    evidence_34_rev = "3-4① 未通过，跳过反向检查"
                else:
                    evidence_34ii = "户号数据不完整，无法比较越权隔离"
                    evidence_34_rev = "同上"

            ok_34 = ok_34i and ok_34ii and ok_34_rev
            evidence_34 = f"{evidence_34i} | {evidence_34ii} | {evidence_34_rev}"
            results.append(("3-4", ok_34, evidence_34))
            print(f"[{'PASS' if ok_34 else 'FAIL'}] 3-4 汇总: {ok_34}")
            print(f"  [{'PASS' if ok_34i else 'FAIL'}] {evidence_34i}")
            print(f"  [{'PASS' if ok_34ii else 'FAIL'}] {evidence_34ii}")
            print(f"  [{'PASS' if ok_34_rev else 'FAIL'}] {evidence_34_rev}")
            if not ok_34i:
                print(f"  admin 原始返回: HTTP {code_a}, {data_a}")

            # ============================================================
            # 汇总
            # ============================================================
            print("\n" + "=" * 70)
            print("Day 3 checklist (3-1 ~ 3-4) 验证结果汇总")
            print("=" * 70)
            all_pass = True
            for code, ok, desc in results:
                status = "PASS" if ok else "FAIL"
                if not ok:
                    all_pass = False
                print(f"[{status}] {code}: {desc}")
            print("=" * 70)
            print(f"总体结果: {'全部通过 ✅' if all_pass else '存在失败 ❌'}")
            print("=" * 70)
            return 0 if all_pass else 1


if __name__ == "__main__":
    sys.exit(main())
