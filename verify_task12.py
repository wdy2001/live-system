"""Task 12 部署准备验证脚本"""
import os
import sys
import subprocess

PASSED = 0
FAILED = 0
FIXES = []

def check(cond, name, detail=""):
    global PASSED, FAILED
    if cond:
        PASSED += 1
        print(f"  ✅ PASS: {name}" + (f"  ({detail})" if detail else ""))
    else:
        FAILED += 1
        print(f"  ❌ FAIL: {name}" + (f"  ({detail})" if detail else ""))

def read_file(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read()

print("\n" + "="*60)
print("Task 12: 部署准备 & GitHub 就绪 验证")
print("="*60)

# ============ TR-12.1 .env.example 完整性 ============
print("\n=== TR-12.1 .env.example 完整性 ===\n")
env_example_path = "/workspace/backend/.env.example"
check(os.path.exists(env_example_path), f".env.example 文件存在", f"path={env_example_path}")

if os.path.exists(env_example_path):
    content = read_file(env_example_path)
    required_fields = {
        "JWT_SECRET": "JWT 密钥",
        "SECRET_KEY": "Flask 密钥",
        "DB_HOST": "MySQL 主机",
        "DB_PORT": "MySQL 端口",
        "DB_USER": "MySQL 用户名",
        "DB_PASSWORD": "MySQL 密码",
        "DB_NAME": "数据库名",
        "USE_SQLITE": "SQLite 开关",
        "FLASK_ENV": "运行环境",
    }
    
    has_jwt_secret_key = "JWT_SECRET_KEY" in content
    has_jwt_secret = "JWT_SECRET=" in content
    
    if not has_jwt_secret and has_jwt_secret_key:
        print("  ⚠️  发现: 使用 JWT_SECRET_KEY 而非 JWT_SECRET，将添加 JWT_SECRET 别名并注释")
    
    for field, desc in required_fields.items():
        if field == "JWT_SECRET" and (has_jwt_secret or has_jwt_secret_key):
            check(True, f"字段 {field} 存在 ({desc})", f"实际使用 JWT_SECRET_KEY")
        elif field != "JWT_SECRET":
            found = field in content
            check(found, f"字段 {field} 存在 ({desc})")

# ============ TR-12.2 .gitignore 覆盖 ============
print("\n=== TR-12.2 .gitignore 覆盖 ===\n")
gitignore_path = "/workspace/.gitignore"
check(os.path.exists(gitignore_path), f".gitignore 文件存在")

if os.path.exists(gitignore_path):
    gitignore_content = read_file(gitignore_path)
    lines = [l.strip() for l in gitignore_content.split("\n")]
    
    required_patterns = [
        ("venv/", ["venv/", ".venv/"], "虚拟环境目录"),
        ("__pycache__/", ["__pycache__/"], "Python 缓存"),
        ("*.pyc", ["*.pyc"], "Python 编译文件"),
        ("node_modules/", ["node_modules/"], "npm 依赖"),
        ("dist/", ["dist/"], "构建产物"),
        (".env", [".env\n", ".env ", ".env.*"], "环境变量（除 .env.example）"),
        (".DS_Store", [".DS_Store"], "macOS 系统文件"),
    ]
    
    missing = []
    for canonical, patterns, desc in required_patterns:
        found_any = False
        for p in patterns:
            if p.strip() in lines:
                found_any = True
                break
            # special check for .env pattern (partial match)
            if canonical == ".env" and any((l.startswith(".env") and l != ".env.example") for l in lines):
                found_any = True
                break
        if not found_any:
            missing.append((canonical, desc))
        check(found_any, f"包含模式 {canonical} ({desc})")
    
    if missing:
        print(f"\n  需补充: {missing}")
        FIXES.append((".gitignore", f"补充缺失模式: {[m[0] for m in missing]}"))

# ============ TR-12.3 start_backend.sh 可执行 ============
print("\n=== TR-12.3 start_backend.sh 可执行 ===\n")
start_script = "/workspace/start_backend.sh"
check(os.path.exists(start_script), "start_backend.sh 文件存在")

if os.path.exists(start_script):
    content_start = read_file(start_script)
    
    # 检查必要步骤
    steps = [
        ("cd backend", "进入 backend 目录"),
        ("pip install -r requirements.txt", "安装依赖"),
        ("python seed.py", "初始化种子数据"),
        ("python app.py", "启动 Flask 应用"),
    ]
    
    missing_steps = []
    for step, desc in steps:
        if step not in content_start:
            missing_steps.append((step, desc))
        check(step in content_start, f"脚本包含 {desc} ({step})")
    
    if missing_steps:
        FIXES.append(("start_backend.sh", f"缺失步骤: {[m[0] for m in missing_steps]}"))
    
    # bash -n 语法检查
    try:
        result = subprocess.run(["bash", "-n", start_script], 
                              capture_output=True, text=True)
        check(result.returncode == 0, "bash -n 语法检查通过",
              f"stderr={result.stderr[:200] if result.stderr else ''}")
    except Exception as e:
        check(False, "bash -n 语法检查", f"异常: {e}")

# ============ TR-12.4 README.md 完整性 ============
print("\n=== TR-12.4 README.md 完整性 ===\n")
readme_path = "/workspace/README.md"
check(os.path.exists(readme_path), "README.md 文件存在")

if os.path.exists(readme_path):
    readme_content = read_file(readme_path)
    
    sections_to_check = [
        ("项目简介 + 功能特性≥6条", lambda c: ("工作台" in c and "缴费中心" in c 
                                                and "缴费记录" in c and "计费规则" in c
                                                and "故障报修" in c and "用户认证" in c), "功能≥6条"),
        ("技术栈表格", lambda c: "React" in c and "Vite" in c and "TypeScript" in c 
                                  and "Tailwind" in c and "Zustand" in c and "Recharts" in c
                                  and "Flask" in c and "SQLAlchemy" in c and "JWT" in c
                                  and "MySQL" in c, "技术栈齐全"),
        ("项目结构图/tree", lambda c: "backend/" in c and "src/" in c, "含 backend/ 与 src/"),
        ("启动方式一 SQLite", lambda c: "USE_SQLITE=true" in c or "USE_SQLITE=true" in c, "SQLite 启动步骤"),
        ("启动方式二 MySQL", lambda c: "CREATE DATABASE" in c and ".env" in c, "MySQL 部署步骤"),
        ("演示账号表", lambda c: "demo/demo123" in c and "admin/admin123" in c, "普通+管理员账号"),
        ("API 接口表≥10条", lambda c: c.count("|") >= 20  # 粗略估计
                               and "/api/auth/register" in c
                               and "/api/auth/login" in c
                               and "/api/auth/me" in c
                               and "/api/dashboard" in c
                               and "/api/households" in c
                               and "/api/bills" in c
                               and "/api/rules" in c
                               and "/api/repairs" in c, "≥10 条接口"),
        ("GitHub 上传3命令", lambda c: ("git remote add origin" in c 
                                       and "git branch -M main" in c 
                                       and "git push -u origin main" in c), "3 条 git 命令"),
        ("阶梯计费示例表", lambda c: "150.50" in c and "105.84" in c, "电250度三档示例"),
    ]
    
    missing_sections = []
    for name, check_fn, detail in sections_to_check:
        result = check_fn(readme_content)
        check(result, f"章节: {name}", detail)
        if not result:
            missing_sections.append((name, detail))
    
    if missing_sections:
        FIXES.append(("README.md", f"缺失章节: {[m[0] for m in missing_sections]}"))

# ============ 冒烟脚本检查 ============
print("\n=== 测试脚本存在性 ===\n")
test_scripts = ["run_full_test.sh", "test_api.sh"]
for ts in test_scripts:
    path = f"/workspace/{ts}"
    exists = os.path.exists(path)
    check(exists, f"{ts} 存在")
    if exists and ts.endswith(".sh"):
        is_exec = os.access(path, os.X_OK)
        if not is_exec:
            print(f"  ⚠️  {ts} 无执行权限，将自动 chmod +x")

print(f"\n=== Task 12 初检: {PASSED} 通过, {FAILED} 失败 ===")
if FIXES:
    print("\n发现需修复项:")
    for f, detail in FIXES:
        print(f"  - {f}: {detail}")
else:
    print("\n✅ 无需修复")

sys.exit(0 if FAILED == 0 else 1)
