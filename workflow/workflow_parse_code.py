import asyncio
from datetime import datetime
import os
import luigi

from app.process.content_chunker import file_chunk_and_save
from app.db_model.database import get_async_session, get_async_session_CTX
from app.vectordb.bm25_search import create_elasticsearch_bm25_index


class FindFiles(luigi.Task):
    project_dir = luigi.Parameter()
    output_dir = luigi.Parameter()

    extensions = ['.java', '.xml', '.js', '.ddl_simple']

    def output(self):
        return luigi.LocalTarget(f'{self.output_dir}/found_files.txt')

    def run(self):
        file_list = []
        for root, _, files in os.walk(self.project_dir):
            for file in files:
                if file.endswith(tuple(self.extensions)):
                    file_list.append(os.path.join(root, file))

        with self.output().open('w') as f:
            for file_path in file_list:
                f.write(file_path + '\n')


# Luigi Task: 각 파일 파싱
class ParseFile(luigi.Task):
    file_path = luigi.Parameter()
    output_dir = luigi.Parameter()

    def output(self):
        output_file = f'{self.output_dir}/parsed_{os.path.basename(self.file_path)}.txt' 
        return luigi.LocalTarget(output_file)

    def run(self):
        try:
            # asyncio.run()을 사용하여 비동기 함수 실행
            asyncio.run(self.async_run())
        except Exception as e:
            print(f"### Error processing file {self.file_path}: {e}")
            raise e 

    async def async_run(self):
        async with get_async_session_CTX() as session: 
            # 파일을 청크로 분할하고 DB에 저장
            org_resrc, chunk_list = await file_chunk_and_save(self.file_path, session=session)

            # Elasticsearch 저장
            create_elasticsearch_bm25_index(index_name='cg_code_assist', org_resrc=org_resrc, chunk_list=chunk_list)

            # 파일로 작성
            with self.output().open('w') as f:
                for item in chunk_list:
                    f.write(item.content + '\n==============================')


class ProcessAllFiles(luigi.Task):
    project_dir = luigi.Parameter()
    output_path = ''

    def requires(self):
        if not self.output_path:
            self.output_path = self.output_dir()

        return FindFiles(self.project_dir, output_dir=self.output_path)

    def output(self):
        return luigi.LocalTarget(f'{self.output_path}/all_files_parsed.txt')

    def output_dir(self):
        # 오늘 날짜 + 시분초로 중간 디렉토리 생성
        current_time = datetime.now().strftime('%Y%m%d_%H%M%S')
        output_dir = f'workflow/working/{current_time}'

        # 디렉토리가 없으면 생성
        os.makedirs(output_dir, exist_ok=True)

        self.output_path = output_dir

        return output_dir

    def run(self):
        # FindFiles 작업에서 생성한 파일 목록을 읽어들임
        find_files_task = self.requires()

        # 파일 목록을 읽기
        with find_files_task.output().open('r') as f:
            for file_path in f:
                file_path = file_path.strip()
                parse_task = ParseFile(file_path=file_path, output_dir=self.output_path)
                luigi.build([parse_task], local_scheduler=True)

        # 모든 파일 처리가 완료되면 완료 파일 생성
        with self.output().open('w') as f:
            f.write('All files have been parsed.\n')


# Luigi 실행
if __name__ == "__main__":
    dir = "/Users/passion1014/project/langchain/rag_server/data/input/sample2"
    luigi.build([ProcessAllFiles(project_dir=dir)], local_scheduler=True)
