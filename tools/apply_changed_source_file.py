import os
import shutil
import difflib
from pathlib import Path

def read_file_safe(file):
    try:
        with open(file, 'r', encoding='utf-8') as f:
            return f.readlines()
    except Exception as e:
        print(f"Error reading {file}: {e}")
        return []

def compare_files(file1, file2):
    """두 파일을 줄 단위로 비교"""
    lines1 = read_file_safe(file1)
    lines2 = read_file_safe(file2)
    
    diff = list(difflib.unified_diff(lines1, lines2, lineterm='\n', fromfile=file1, tofile=file2))
    return "".join(diff) if diff else None

def copy_with_backup(src, dst, backup):
    src_path = Path(src).resolve()
    dst_path = Path(dst).resolve()
    backup_path = Path(backup).resolve()

    for root, _, files in os.walk(src_path):
        rel_path = Path(root).relative_to(src_path)
        dst_dir = dst_path / rel_path
        backup_dir = backup_path / rel_path
        dst_dir.mkdir(parents=True, exist_ok=True)
        backup_dir.mkdir(parents=True, exist_ok=True)

        for file in files:
            src_file = Path(root) / file
            dst_file = dst_dir / file
            backup_file = backup_dir / file
            
            if dst_file.exists():
                diff = compare_files(src_file, dst_file)
                if diff:
                    print(f"Differences found in {dst_file}:")
                    print(diff)
                    user_input = input(f"File {dst_file} already exists. Overwrite? (y/n): ").strip().lower()
                    if user_input == 'y':
                        shutil.move(str(dst_file), str(backup_file))
                        print(f"Backed up: {dst_file} -> {backup_file}")
                        shutil.copy2(str(src_file), str(dst_file))
                        print(f"Copied: {src_file} -> {dst_file}")
                    else:
                        print(f"Skipped: {src_file}")
                else:
                    print(f"이미 같은 내용의 파일이라 스킵합니다: {src_file}")
            else:
                shutil.copy2(str(src_file), str(dst_file))
                print(f"Copied: {src_file} -> {dst_file}")

if __name__ == "__main__":
    src_folder = input("변경파일폴더: ")
    dst_folder = input("대상폴더(빈값이면 'D:/project/rag_server') : ")
    backup_folder = input("백업폴더(빈값이면 '소스폴더/backup'): ")
    
    if not dst_folder:
        dst_folder = "D:/project/rag_server"

    if not backup_folder:
        backup_folder = src_folder + "/backup"

    copy_with_backup(src_folder, dst_folder, backup_folder)
    print("Operation completed!")
