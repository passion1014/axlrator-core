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
        if dp[-1]:
            results = []
            for path in dp[-1]:
                korean_result = path
                english_result = [dictionary[word] for word in path]
                results.append({"korean": korean_result, "english": english_result})
            return results
        else:
            # 분리 불가능한 경우, 원래 단어 반환
            return [{"korean": [word], "english": [dictionary.get(word, "UNKNOWN")]}]