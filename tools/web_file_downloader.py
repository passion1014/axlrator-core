import os
import requests

# 다운로드할 파일과 해당 파일의 저장 경로를 딕셔너리로 정의
files_to_download = {
    "https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/css/bootstrap.min.css": "static/css/bootstrap.min.css",
    "https://code.jquery.com/jquery-3.5.1.slim.min.js": "static/js/jquery-3.5.1.slim.min.js",
    "https://cdn.jsdelivr.net/npm/@popperjs/core@2.5.2/dist/umd/popper.min.js": "static/js/popper.min.js",
    "https://stackpath.bootstrapcdn.com/bootstrap/4.5.2/js/bootstrap.min.js": "static/js/bootstrap.min.js",
    "https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/prism.min.js": "static/js/prism.min.js",
    "https://cdnjs.cloudflare.com/ajax/libs/prism/1.29.0/themes/prism.min.css": "static/css/prism.min.css",
}

# 파일을 다운로드하고 저장하는 함수
def download_files(files):
    for url, path in files.items():
        os.makedirs(os.path.dirname(path), exist_ok=True)  # 디렉토리 생성
        response = requests.get(url)
        if response.status_code == 200:
            with open(path, 'wb') as file:
                file.write(response.content)
            print(f"Downloaded {url} to {path}")
        else:
            print(f"Failed to download {url}")

# 파일 다운로드 실행
download_files(files_to_download)