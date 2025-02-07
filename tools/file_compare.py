import os
import difflib
import datetime

# 비교할 파일 확장자 및 필터링할 파일명 패턴 설정
ALLOWED_EXTENSIONS = {".py", ".html", ".css", ".ipynb"}
EXCLUDE_PREFIX = "_"  # _로 시작하는 파일 제외
EXCLUDE_PYTHON_MODULES = {"__init__.py", "__pycache__"}  # 파이썬 모듈 제외
EXCLUDE_DIRS = {"venv", "node_modules", "__pycache__"}  # 제외할 디렉토리 목록

def get_all_files(folder):
    """폴더 내 모든 파일 목록을 트리 구조로 반환 (필터 적용)"""
    files = {}
    tree_structure = []

    for root, _, filenames in os.walk(folder):
        relative_root = os.path.relpath(root, folder)
        if any(excluded in relative_root.split(os.sep) for excluded in EXCLUDE_DIRS):
            continue  # 특정 디렉토리 제외

        tree_structure.append(f"[{relative_root}]" if relative_root != "." else "[Root]")

        for filename in filenames:
            if (os.path.splitext(filename)[1] in ALLOWED_EXTENSIONS and
                not filename.startswith(EXCLUDE_PREFIX) and
                filename not in EXCLUDE_PYTHON_MODULES):  # 확장자 및 필터 적용
                full_path = os.path.join(root, filename)
                relative_path = os.path.relpath(full_path, folder)
                files[relative_path] = full_path
                tree_structure.append(f"  ├── {filename}")

    return files, "\n".join(tree_structure)

def read_file_safe(file_path):
    """파일을 안전하게 읽기 (인코딩 문제 방지)"""
    try:
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.readlines()
    except UnicodeDecodeError:
        return []  # 읽기 실패 시 빈 리스트 반환

def compare_files(file1, file2):
    """두 파일을 줄 단위로 비교"""
    lines1 = read_file_safe(file1)
    lines2 = read_file_safe(file2)

    diff = list(difflib.unified_diff(lines1, lines2, lineterm='', fromfile=file1, tofile=file2))
    return "\n".join(diff) if diff else None

def compare_folders(folder1, folder2):
    """폴더 비교 후 결과를 보고서 파일로 저장"""
    today = datetime.datetime.now().strftime("%y%m%d")
    os.makedirs("compare", exist_ok=True)
    file_list_report = os.path.join("compare", f"file_compare_list{today}.txt")

    files1, tree1 = get_all_files(folder1)
    files2, tree2 = get_all_files(folder2)

    common_files = set(files1.keys()) & set(files2.keys())
    only_in_folder1 = set(files1.keys()) - set(files2.keys())
    only_in_folder2 = set(files2.keys()) - set(files1.keys())

    report = []

    # 파일 목록 비교 보고서
    report.append("📂 폴더 비교 결과\n")
    report.append(f"📁 폴더1 ({folder1}):\n{tree1}\n")
    report.append(f"📁 폴더2 ({folder2}):\n{tree2}\n")

    if only_in_folder1:
        report.append("🟥 폴더1에만 있는 파일:\n" + "\n".join(f"  ├── {file}" for file in only_in_folder1) + "\n")
    if only_in_folder2:
        report.append("🟦 폴더2에만 있는 파일:\n" + "\n".join(f"  ├── {file}" for file in only_in_folder2) + "\n")

    # 파일 목록 비교 보고서 저장
    with open(file_list_report, "w", encoding="utf-8") as f:
        f.write("\n".join(report))
    print(f"✅ 파일 목록 비교 완료! 보고서 저장: {file_list_report}")

    # 파일 내용 비교 보고서 저장
    for file in common_files:
        diff_result = compare_files(files1[file], files2[file])
        if diff_result:
            diff_report_file = os.path.join("compare", f"{os.path.splitext(os.path.basename(file))[0]}_{today}.txt")
            with open(diff_report_file, "w", encoding="utf-8") as f:
                f.write(f"🔍 {file} 내용 변경:\n{diff_result}\n")
            print(f"✅ 파일 내용 비교 완료! 보고서 저장: {diff_report_file}")

# 비교할 폴더 경로 설정
folder1 = "/Users/passion1014/project/langchain/rag_server/app"
folder2 = "/Users/passion1014/project/langchain/temp/rag_server/app"

compare_folders(folder1, folder2)
