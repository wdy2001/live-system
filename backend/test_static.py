"""TR-12.3 测试 Flask 单进程服务静态资源"""
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
os.chdir(os.path.dirname(os.path.abspath(__file__)))

from app import create_app

app = create_app()
client = app.test_client()

DIST_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), '..', 'dist'))
ASSETS_DIR = os.path.join(DIST_DIR, 'assets')

results = {}

print("=" * 60)
print("TR-12.3 Flask 静态资源服务测试")
print("=" * 60)
print(f"dist 目录: {DIST_DIR}")
print(f"dist 存在: {os.path.exists(DIST_DIR)}")

# a. GET / → 200
resp = client.get('/')
results['a_root_200'] = resp.status_code == 200
body_text = resp.get_data(as_text=True)
has_title = '<title>' in body_text or '<div id="root">' in body_text
results['a_root_has_structure'] = has_title
print(f"\na) GET / → status={resp.status_code}, 含<title>/root: {has_title}")
print(f"   body 前 200 字: {body_text[:200]!r}")

# b. GET /favicon.svg → 200
resp = client.get('/favicon.svg')
results['b_favicon_200'] = resp.status_code == 200
results['b_favicon_len_gt0'] = len(resp.data) > 0
print(f"\nb) GET /favicon.svg → status={resp.status_code}, len={len(resp.data)}")

# c. GET /assets/<filename> → 200
js_files = [f for f in os.listdir(ASSETS_DIR) if f.endswith('.js') and not f.endswith('.map')] if os.path.isdir(ASSETS_DIR) else []
css_files = [f for f in os.listdir(ASSETS_DIR) if f.endswith('.css')] if os.path.isdir(ASSETS_DIR) else []
print(f"\n  assets 下文件: js={js_files}, css={css_files}")
results['c_has_js_css'] = bool(js_files) and bool(css_files)

test_file = js_files[0] if js_files else (css_files[0] if css_files else None)
if test_file:
    resp = client.get(f'/assets/{test_file}')
    results['c_asset_200'] = resp.status_code == 200
    results['c_asset_len_gt0'] = len(resp.data) > 0
    print(f"c) GET /assets/{test_file} → status={resp.status_code}, len={len(resp.data)}")
else:
    results['c_asset_200'] = False
    results['c_asset_len_gt0'] = False
    print("c) 没有可测试的 asset 文件")

print("\n--- 结果汇总 ---")
all_pass = all(results.values())
for k, v in results.items():
    print(f"  {k}: {'PASS' if v else 'FAIL'}")
print(f"\nTR-12.3 总体: {'PASS' if all_pass else 'FAIL'}")
print(f"EXIT={'0' if all_pass else '1'}")
sys.exit(0 if all_pass else 1)
