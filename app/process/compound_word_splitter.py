import re


class CompoundWordSplitter:
    # 클래스 변수 (모든 인스턴스가 공유)
    _cached_dictionary = None

    @classmethod
    def get_dictionary(cls):
        # 이미 메모리에 캐싱된 경우 캐싱된 값 반환
        if cls._cached_dictionary is not None:
            return cls._cached_dictionary

        # 파일에서 딕셔너리 읽기
        cls._cached_dictionary = {}
        with open("data/terms_20241112.terms", "r", encoding="utf-8") as file:
            for line in file:
                line = line.strip()  # Trim 처리
                if not line:  # 빈 줄 무시
                    continue
                key_value = line.split(":")
                if len(key_value) == 2:
                    key, value = key_value[0].strip(), key_value[1].strip()
                    cls._cached_dictionary[key] = value

        return cls._cached_dictionary

    @classmethod
    def conv_compound_word(cls, word):
        words = cls.split_compound_word(word)
        return cls.transform_result(words)


    @classmethod
    def split_compound_word(cls, word):
        dictionary = cls.get_dictionary()  # 딕셔너리 가져오기
        n = len(word)
        dp = [None] * (n + 1)
        dp[0] = [[]]  # 초기 상태: 빈 리스트를 포함한 리스트

        for i in range(1, n + 1):
            dp[i] = []  # i번째 위치에서 가능한 모든 분리 저장
            for j in range(0, i):
                sub_word = word[j:i]
                if sub_word in dictionary and dp[j] is not None:
                    for path in dp[j]:
                        dp[i].append(path + [sub_word])  # 이전 경로에 현재 단어 추가

        # 최종 결과 반환: 가능한 모든 분리 경로를 한글과 영어로 변환
        results = []
        if dp[-1]:
            for path in dp[-1]:
                korean_result = path
                english_result = [dictionary[word] for word in path]
                results.append({"korean": korean_result, "english": english_result})
            # return results
        # else:
        #     # 분리 불가능한 경우, 원래 단어 반환
        #     return [{"korean": [word], "english": [dictionary.get(word, "UNKNOWN")]}]
        
        return results

    @classmethod
    def transform_result(cls, result):
        transformed = []
        for item in result:
            korean_part = ";".join(item['korean'])
            english_part = "_".join(item['english'])
            camel_case = ''.join([word.capitalize() for word in item['english']])
            camel_case = camel_case[0].lower() + camel_case[1:]  # camelCase 변환
            transformed.append(f"{korean_part} = {english_part}({camel_case})")
        return transformed

    @classmethod
    def extract_korean_words(cls, text):
        """
        입력된 텍스트에서 한글 단어만 추출하는 함수
        :param text: 입력 텍스트 (str)
        :return: 한글 단어 리스트
        """
        korean_words = re.findall(r'[가-힣]+', text)
        return korean_words




    @classmethod
    def merge_translations(cls, data):
        """
        주어진 데이터를 한글-영어 매핑으로 통합하는 함수
        """
        result = {}
        for item in data:
            # item이 딕셔너리가 아닐 경우 예외 처리
            if not isinstance(item, dict):
                print(f"잘못된 데이터 형식: {item}")
                continue
            
            korean = item.get('korean', [])
            english = item.get('english', [])
            
            # korean과 english 길이 확인
            if len(korean) != len(english):
                print(f"키와 값의 길이가 다릅니다: {item}")
                continue
            
            k = "".join(item['korean'])
            e = "_".join(item['english'])

            if k not in result: # 중복제거
                result[k] = e
            
        return result