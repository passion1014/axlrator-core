#!/bin/bash

# 변경된 파일을 복사할 대상 디렉토리 (사용자가 원하는 경로로 수정 가능)
DATE=$(date +"%Y%m%d") # 오늘 날짜를 yyyyMMdd 형식으로 가져옴
DEST_DIR="../changed_files/$DATE" # 경로 중간에 날짜 폴더 추가

# 복사 대상 폴더가 없으면 생성
mkdir -p "$DEST_DIR"

# Git에서 변경된 파일 목록 가져오기 (기준 커밋은 사용자가 수정)
BASE_COMMIT="5bbc4a6" # 기준 커밋 (현재는 바로 직전 커밋)
CURRENT_COMMIT="1d244ed" # 현재 커밋

echo "기준 커밋: $BASE_COMMIT"
echo "현재 커밋: $CURRENT_COMMIT"

# 변경된 파일 목록 저장 경로
CHANGED_FILES_LIST="$DEST_DIR/changed_files.txt"

# 변경된 파일 목록을 생성
git diff --name-only "$BASE_COMMIT" "$CURRENT_COMMIT" > "$CHANGED_FILES_LIST"


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
done < "$CHANGED_FILES_LIST"

# 완료 메시지
echo "모든 변경된 파일이 $DEST_DIR 디렉토리에 복사되었습니다."
