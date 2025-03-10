
# aifred workflow

apache airflow 사용 (https://airflow.apache.org/)

## 설치

### 가상환경
python -m venv aifred_wf
source aifred_wf/bin/activate


### AIRFLOW_HOME 설정 (workflow 디렉토리로 설정)
export AIRFLOW_HOME=./workflow (프로젝트 root 기준)

### 패키지 설치
pip install 'apache-airflow==2.10.5' \
 --constraint "https://raw.githubusercontent.com/apache/airflow/constraints-2.10.5/constraints-3.9.txt"


### 설정파일 
~/airflow/airflow.cg

### 데이터베이스 설정
airflow db migrate



# 2025-02-26 변경함
## luigi
https://github.com/spotify/luigi

pip install luigi
pip install javalang # 자바를 분석하기 위한 도구


```
import luigi

class HelloWorldTask(luigi.Task):
    # 태스크의 출력 정의
    def output(self):
        return luigi.LocalTarget('hello_world.txt')

    # 태스크의 실행 로직 정의
    def run(self):
        with self.output().open('w') as outfile:
            outfile.write('Hello, World!')

if __name__ == '__main__':
    luigi.run(['HelloWorldTask', '--local-scheduler'])
```
