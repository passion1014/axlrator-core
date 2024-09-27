import os

def merge_txt_files(directory, output_file):
    # 지정된 디렉토리 내의 모든 txt 파일 목록을 가져옵니다.
    txt_files = [f for f in os.listdir(directory) if f.endswith('.txt')]
    # 파일 이름순으로 정렬합니다.
    txt_files.sort()
    with open(output_file, 'w', encoding='utf-8') as outfile:
        for filename in txt_files:
            print(filename)
            filepath = os.path.join(directory, filename)
            with open(filepath, 'r', encoding='euc-kr') as infile:
                # 파일의 내용을 읽어서 출력 파일에 씁니다.
                outfile.write(infile.read())
                # 각 파일의 내용 사이에 줄 바꿈을 추가할 수 있습니다.
                outfile.write('\n')



if __name__ == '__main__':
    
    merge_txt_files('/Users/passion1014/Downloads/bible/text', '/Users/passion1014/Downloads/bible/bible_개역개정.txt')
