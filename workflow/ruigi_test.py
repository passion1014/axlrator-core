import luigi

class HelloWorldTask(luigi.Task):
    # 태스크의 출력 정의
    def output(self):
        return luigi.LocalTarget('hello_world.txt')

    # 태스크의 실행 로직 정의
    def run(self):
        with self.output().open('w') as outfile:
            outfile.write('Hello, World!')

# if __name__ == '__main__':
#     luigi.run(['HelloWorldTask', '--local-scheduler'])
