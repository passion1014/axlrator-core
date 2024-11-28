from app.process.compound_word_splitter import CompoundWordSplitter


if __name__ == '__main__':
    result = CompoundWordSplitter.split_compound_word("복합단어분리")
    print(f"### {result}")

    result = CompoundWordSplitter.split_compound_word("전이율")
    print(f"### {result}")
    
    result = CompoundWordSplitter.split_compound_word("보증특기사항")
    print(f"### {result}")