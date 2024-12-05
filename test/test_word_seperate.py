from app.process.compound_word_splitter import CompoundWordSplitter



if __name__ == '__main__':
    result = CompoundWordSplitter.split_compound_word("복합단어분리")
    print(f"### {result}")

    result = CompoundWordSplitter.split_compound_word("전이율")
    print(f"### {result}")
    
    result = CompoundWordSplitter.split_compound_word("보증특기사항")
    print(f"### {result}")
    
    words = """
    public int insertCnrcRltn(Map pDoc) throws CgAppUserException {
        int result = 0;
        try {
            /*
			 * 전이율 초과보증금내역 등록한다 보증상태
			 */
            //XDA xda = XDAFactory.getXDA(Constants.KEEP_CONNECTION);
            result = comCgSaGuGurtcommonGuzsacnrcrltnDAO.gu_zsa_cnrc_rltn_io0001(pDoc);
        } catch (ElException e) {
            if (AppLog.isWarnEnabled()) {
                AppLog.warn(e.getMessage(), e);
            }
            throw new CgAppUserException("CG_ERROR", 0, e.getMessage(), CodeUtil.getCodeValue("CGMsgCode", "E", "E10000"), e);
        }
        /*
		 * 결과리턴 보증특기사항 전이율
		 */
        return result;
    }
    """
    korean_words = CompoundWordSplitter.extract_korean_words(words)
    print(f">>>>>>>>> korean_words = {korean_words}")
    
    split_words = []
    for word in korean_words:
        result = CompoundWordSplitter.conv_compound_word(word)

        result = CompoundWordSplitter.split_compound_word(word)
        print(f">>> {word}: {result}")
        if result:
            k = "".join(result[0]['korean'])
            e = "_".join(result[0]['english'])

            split_words.append(result[0])
    
    print(f">>>>>>>>> split_words = {split_words}")
    
    merge = CompoundWordSplitter.merge_translations(split_words)
    print(f">>>>>>>>> merge = {merge}")

    context = ", ".join([f"{key}={value}" for key, value in merge.items()])
    print(f">>>>>>>>> context = {context}")

