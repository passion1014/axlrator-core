#!/bin/bash

# 변경된 파일을 복사할 대상 디렉토리 (사용자가 원하는 경로로 수정 가능)
DEST_DIR="changed_files"

# 복사 대상 폴더가 없으면 생성
mkdir -p "$DEST_DIR"

# Git에서 변경된 파일 목록 가져오기 (기준 커밋은 사용자가 수정)
BASE_COMMIT="c78aa6e" # 기준 커밋 (현재는 바로 직전 커밋)
CURRENT_COMMIT="3a227f2" # 현재 커밋

echo "기준 커밋: $BASE_COMMIT"
echo "현재 커밋: $CURRENT_COMMIT"

# 변경된 파일 목록 저장
git diff --name-only "$BASE_COMMIT" "$CURRENT_COMMIT" > changed_files.txt

# 변경된 파일 복사
while read -r file; do
    # 파일이 실제 존재하는지 확인
    if [[ -f "$file" ]]; then
        echo "복사 중: $file"
        mkdir -p "$DEST_DIR/$(dirname "$file")" # 하위 디렉토리 생성
        cp "$file" "$DEST_DIR/$file"
    else
        echo "존재하지 않는 파일: $file (아마도 삭제된 파일일 가능성)"
    fi
done < changed_files.txt

# 완료 메시지
echo "모든 변경된 파일이 $DEST_DIR 디렉토리에 복사되었습니다."
