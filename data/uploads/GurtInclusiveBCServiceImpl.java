public long calcIndvBnamt(Map pDoc) throws ElException, Exception {
    Map bizInput = null;
    long bnamt = 0;
    double dBnamt = 0;
    bizInput = pDoc;
    // 계약금액
    long cnttAmt = 0;
    // 계약상선급금액
    long prptAmt = 0;
    // 보증기간일수
    int diffDay = 0;
    // 계약체결일자
    String cnrcCncsDate = "";
    // 보증시작일자
    String gurtProdStda = "";
    // 보증종료일자
    String gurtProdEnda = "";
    // 대금지급주기월수
    String prcePaynCyclMncnt = "";
    cnttAmt = MapDataUtil.getLong(bizInput, "CNAMT");
    prptAmt = MapDataUtil.getLong(bizInput, "PRPT_AMT");
    cnrcCncsDate = MapDataUtil.getString(bizInput, "CNRC_CNCS_DATE");
    gurtProdStda = MapDataUtil.getString(bizInput, "GURT_PROD_STDA");
    gurtProdEnda = MapDataUtil.getString(bizInput, "GURT_PROD_ENDA");
    prcePaynCyclMncnt = MapDataUtil.getString(bizInput, "PRCE_PAYN_CYCL_MMCNT");
    // 보증기간을 구한다.
    if (!gurtProdStda.equals("") && !gurtProdEnda.equals("")) {
        diffDay = DateUtil.getDays(gurtProdStda, gurtProdEnda);
        diffDay = diffDay + 1;
    } else {
        // 넘어온데이타가 없으면 보증금액 계산불가로 0원으로 리턴해준다.
        bnamt = 0;
        return bnamt;
    }
    // 계약금액이 넘어오지 않으며 계산 불가이다.
    if (cnttAmt < 1) {
        bnamt = 0;
        return bnamt;
    }
    /*
     * 보증금액 계산 
     */
    // 건설기계대여업체인경우에는 다음의 식으로 계산이 되야 한다. => (하도급금액 - 계약상 선급금) / 공사기간(월) * 4
    if ("3".equals(MapDataUtil.getString(bizInput, "INDV_GURT_DSCD")) || "5".equals(MapDataUtil.getString(bizInput, "INDV_GURT_DSCD"))) {
        dBnamt = ((cnttAmt - prptAmt) * 30 / diffDay) * 4;
    } else {
        // 4월미만 공사인경우에는 보증금액 : 계약금액 - 선급금액
        if (diffDay <= 120) {
            AppLog.info("4개월미만 공사 계산  :: " + cnttAmt + " : " + prptAmt);
            dBnamt = cnttAmt - prptAmt;
        } else {
            // 아래의 계산식일경우 기성주기가 없으면 계산할 수 없다.
            if (prcePaynCyclMncnt == null || prcePaynCyclMncnt.equals("")) {
                bnamt = 0;
                return bnamt;
            }
            /*
             * 4개월 이상공사 이면서, 기성주기가 2월 이내인 경우 
             * 		=> (하도급금액 - 계약상 선급금) / 공사기간(월) * 4
             * 4개월 이상공사 이면서, 기성주기가 2월 초과 
             *      => (하도급금액 - 계약상 선급금) / 공사기간(월) * 기성주기(월) * 2
             */
            if (Integer.parseInt(prcePaynCyclMncnt) <= 2) {
                dBnamt = ((cnttAmt - prptAmt) * 30 / diffDay) * 4;
            } else {
                dBnamt = ((cnttAmt - prptAmt) * 30 / diffDay) * Integer.parseInt(prcePaynCyclMncnt) * 2;
            }
        }
    }
    AppLog.info("보증수수료계산 :: ");
    AppLog.info("cnttAmt :: " + cnttAmt);
    AppLog.info("prptAmt :: " + prptAmt);
    AppLog.info("diffDay :: " + diffDay);
    AppLog.info("prcePaynCyclMncnt :: " + prcePaynCyclMncnt);
    AppLog.info("dBnamt :: " + dBnamt);
    // 10원단위 절사
    bnamt = Math.round(dBnamt);
    bnamt = (long) ((bnamt / 10) * 10);
    AppLog.info("\n bnamt :: " + bnamt);
    /**
     * 결과 반환
     */
    return bnamt;
}