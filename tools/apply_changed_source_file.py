import os
import shutil
from pathlib import Path

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
                shutil.move(str(dst_file), str(backup_file))
                print(f"Backed up: {dst_file} -> {backup_file}")
            
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
