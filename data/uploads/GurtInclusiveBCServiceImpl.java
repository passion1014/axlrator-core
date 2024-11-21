/**
 * Copyright (c) 2010 CG. All rights reserved.
 *
 * This software is the confidential and proprietary information of CG. You
 * shall not disclose such Confidential Information and shall use it only in
 * accordance with the terms of the license agreement you entered into with CG.
 */
package com.cg.sa.gu.gurtinclusive.service.impl;

/**
 * 업무 그룹명 : com.cg.sa.gu.gurtinclusive.bc
 * 서브 업무명 : GurtInclusiveBC.java
 * 작성자 : Park. Ki-Seok
 * 작성일 : 2012.04.26
 * 설 명 : 포괄보증에서 처리하는 내용을 관리하는 클래스이다.
 */
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.Map;
import java.util.StringTokenizer;

import javax.annotation.Resource;

import org.springframework.stereotype.Service;

import com.cg.cu.cb.common.CUCBConstants;
import com.cg.custom.cmmn.exception.CgAppUserException;
import com.cg.custom.cmmn.util.MapDataUtil;
import com.cg.custom.cmmn.util.UserHeaderUtil;
import com.cg.sa.gu.common.SAGUConstants;
import com.cg.sa.gu.gurtinclusive.service.GurtInclusiveBCService;
import com.cg.sys.ums.adaptor.MessageAdaptor;
import com.cg.sys.ums.vo.MessageVO;
import com.inswave.elfw.exception.ElException;
import com.inswave.elfw.log.AppLog;
import com.inswave.ext.cg.util.CodeUtil;
import com.inswave.ext.cg.util.DateUtil;

/**
 * 포괄보증에서 처리하는 내용을 관리하는 클래스이다.
 */
@Service("gurtInclusiveBCServiceImpl")
public class GurtInclusiveBCServiceImpl implements GurtInclusiveBCService {

    /**
     * 포괄-개별보증의 보증금액을 산출한다.
     */
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

    /**
     * <<TITLE>>
     * 건설공사대장 수신 후 개별보증신청내역에 자료를 입력한다.
     * <<LOGIC>>
     * 1. 개별보증신청대상에대해 개별보증신청내역을 등록한다.
     * 2. 결과리턴
     * @param pDoc
     * @return
     * @throws Exception
     */
    public Map insertIndvApltDtl(Map pDoc) throws ElException, Exception {
        AppLog.info("GurtInclusiveBC.java insertIndvApltDtl START!!!! >>>>>>>>>>>>>>>>\n[" +  ("") /* 주석처리(as-is) XMLUtil.indent(pDoc)*/ + "]");
        /**
         * 1.Document 변수의 정의
         *
         * XDA 결과 변수 result
         */
        Map result = null;
        Map bizInDoc = null;
        ArrayList<Map> bizOutDoc = null;
        
        Map bizLogicInDoc = null;
        ArrayList<Map> bizLogicOutDoc = null;
        Map bizLogicOutDocMap = null;
        String currTimestamp = null;
        String userId = null;
        // 지분별분할관리번호
        String quotCbyPrttMnno = null;
        // 자동알림 통보시 사용할 공사ID
        String atmnWrksId = "";
        // 자동알림 통보시 사용할 통보차수
        String atmnNtfcOrseq = "";
        currTimestamp = com.inswave.ext.cg.util.DateUtil.getTimestamp();
        // MCI연계로 들어온경우 세션값이 없기때문에 세션을 만들어준다. (서비스 호출에서 필요한경우 세션이 없으면 오류가 발생됨)
        String currDate = currTimestamp.substring(0, 8);
//        UserSession userSession = new UserSession();
        // 사용자ID
//        userSession.setUsr_id("MCI") ---> (해당 라인의 소스는 ContextUtil 변환을 지원하지 않습니다. / setUsr_id);
        // 사원번호
//        userSession.setEmpNo("MCI") ---> (해당 라인의 소스는 ContextUtil 변환을 지원하지 않습니다. / setEmpNo);
        // 사원명
//        userSession.setEmp_nm("MCI") ---> (해당 라인의 소스는 ContextUtil 변환을 지원하지 않습니다. / setEmp_nm);
        // 영업일자
//        userSession.setBzda(currDate) ---> (해당 라인의 소스는 ContextUtil 변환을 지원하지 않습니다. / setBzda);
        // 현재일자(금일)
//        userSession.setTday(currDate) ---> (해당 라인의 소스는 ContextUtil 변환을 지원하지 않습니다. / setTday);
//        userSession.setHdbr_dscd("H") ---> (해당 라인의 소스는 ContextUtil 변환을 지원하지 않습니다. / setHdbr_dscd);
//        userSession.setDpCd("11000") ---> (해당 라인의 소스는 ContextUtil 변환을 지원하지 않습니다. / setDpCd);
//        userSession.setDpNm("정보시스템부") ---> (해당 라인의 소스는 ContextUtil 변환을 지원하지 않습니다. / setDpNm);
//        userSession.setRsof_cd("") ---> (해당 라인의 소스는 ContextUtil 변환을 지원하지 않습니다. / setRsof_cd);
//        userSession.setTrmn_no("") ---> (해당 라인의 소스는 ContextUtil 변환을 지원하지 않습니다. / setTrmn_no);
//        userSession.setAcng_dpcd("11000") ---> (해당 라인의 소스는 ContextUtil 변환을 지원하지 않습니다. / setAcng_dpcd);
//        userSession.setAcng_dpnm("정보시스템부") ---> (해당 라인의 소스는 ContextUtil 변환을 지원하지 않습니다. / setAcng_dpnm);
//        userSession.setHdbr_cd("10000") ---> (해당 라인의 소스는 ContextUtil 변환을 지원하지 않습니다. / setHdbr_cd);
//        userSession.setHdbr_nm("본부") ---> (해당 라인의 소스는 ContextUtil 변환을 지원하지 않습니다. / setHdbr_nm);
        // userSession Set
//        ContextUtil.setUserData("userSession", userSession) ---> (해당 라인의 소스는 ContextUtil 변환을 지원하지 않습니다. / setUserData);
//        ContextUtil.setUserData("empno", "MCI") ---> (해당 라인의 소스는 ContextUtil 변환을 지원하지 않습니다. / setUserData);
//        ContextUtil.setUserData("timestamp", com.inswave.ext.cg.util.DateUtil.getTimestamp()) ---> (해당 라인의 소스는 ContextUtil 변환을 지원하지 않습니다. / setUserData);
        // -- 세션처리 여기까지..
        try {
            //XDA xda = XDAFactory.getXDA(Constants.KEEP_CONNECTION);
            userId = "MCI";
            // List추출 후 확인
            ArrayList<Map> bascListArry = (ArrayList)MapDataUtil.getList(pDoc, "ZGU_INDV_APLT_DTL");
            Iterator<Map> bascListItr = bascListArry.iterator();
            Map bascDoc = null;
            Map bascNewDoc = null;
            /**
             * 개별보증 신청내역이 1인명의 이면서 포괄보증 발급정보가 각자명의인경우
             * 개별보증 신청내역에 각자명의로 분리하여 넣어줘야 한다.
             * (1개의 신청내역을 N개의 신청내역으로 지분율만큼 분할)
             */
            ArrayList<Map> listArry = new ArrayList<Map>();
            ArrayList tmpLst = null;
            Map lstDoc = null;
            for (int j = 0; j < bascListArry.size(); j++) {
                bascDoc = (Map) bascListArry.get(j);
                AppLog.info("insertIndvApltDtlProc(bascDoc) [" + j + "] >>>>>" +  ("") /* 주석처리(as-is) XMLUtil.indent(bascDoc)*/);
                if (j == 0) {
                    // 자동알림 통보시 사용할 공사ID
                    atmnWrksId = MapDataUtil.getString(bascDoc, "WRKS_ID");
                    // 자동알림 통보시 사용할 통보차수
                    atmnNtfcOrseq = MapDataUtil.getString(bascDoc, "NTFC_ORSEQ");
                }
                // 계약금액이 4000만원 미만인경우에는 보증제외대상이다.
                if (MapDataUtil.getLong(bascDoc, "CNAMT") < 40000000) {
                    continue;
                }
                // 1인 단독 명의 계약여부
                if (MapDataUtil.getString(bascDoc, "CMCM_CNRC_YN").equals("N")) {
                    bizLogicInDoc = new HashMap();
                    // 공사관리번호
                    MapDataUtil.setString(bizLogicInDoc, "WRKS_MNNO", MapDataUtil.getString(bascDoc, "WRKS_MNNO"));
                    // 보증상태코
                    MapDataUtil.setString(bizLogicInDoc, "GURT_STCD", MapDataUtil.getString(bascDoc, "GURT_STCD"));
                    // 도급자사업자번호
                    MapDataUtil.setString(bizLogicInDoc, "CUNO", MapDataUtil.getString(bascDoc, "CTRR_BZRNO"));
                    // 발급된 포괄보증서가 1인명의인지 조회한다.
                    AppLog.info("com.cg.sa.gu.gurtinclusive.xda.gu_zgu_guas_so0014 >>>>>\n[" +  ("") /* 주석처리(as-is) XMLUtil.indent(bizLogicInDoc)*/ + "]");
                    bizLogicOutDocMap = comCgSaGuGurtinclusiveGuzguguasDAO.gu_zgu_guas_so0014(bizLogicInDoc);
                    // 포괄보증서가 1인명의 발급이라면 분할해줄 필요 없다.
                    if (MapDataUtil.getString(bizLogicOutDocMap, "ISSU_SHPE_DSCD").equals("1")) {
                        // 지분별분할여부
                        MapDataUtil.setString(bascDoc, "QUOT_CBY_PRTT_YN", "");
                        // 지분별분할관리번호
                        MapDataUtil.setString(bascDoc, "QUOT_CBY_PRTT_MNNO", "");
                        AppLog.info("insertIndvApltDtlProc(bascDoc) 1>>>>>" +  ("") /* 주석처리(as-is) XMLUtil.indent(bascDoc)*/);
                        // listArry.add(bascDoc);	//신청내역저장리스트에 추가
                        // 신청내역저장
                        insertIndvApltDtlProc(bascDoc);
                    } else {
                        if (MapDataUtil.getString(bascDoc, "COMPREHS_GB").equals("COMPREHS")) {
                            // 1인명의 개별보증 내역을 각자명의처럼 만들어준다.
                            AppLog.info("com.cg.sa.gu.gurtinclusive.xda.gu_zsm_inlv_sbcn_sbcm_log_so0001 >>>>>\n[" +  ("") /* 주석처리(as-is) XMLUtil.indent(bascDoc)*/ + "]");
                            bizLogicOutDoc = comCgSaGuGurtinclusiveGuzsminlvsbcnsbcmlogDAO.gu_zsm_inlv_sbcn_sbcm_log_so0001(bascDoc);
                            tmpLst = bizLogicOutDoc; //* 수동가이드 예정 (as-is) XMLUtil.toArrayList(bizLogicOutDoc)*/;
                        } else {
                            // 1인명의 개별보증 내역을 각자명의처럼 만들어준다.
                            AppLog.info("com.cg.sa.gu.gurtinclusive.xda.gu_zsm_kiscon_ptcp_infm_addlog_so0001 >>>>>\n[" +  ("") /* 주석처리(as-is) XMLUtil.indent(bascDoc)*/ + "]");
                            bizLogicOutDoc = comCgSaGuGurtinclusiveGuzsmkisconptcpinfmaddlogDAO.gu_zsm_kiscon_ptcp_infm_addlog_so0001(bascDoc);
                            tmpLst = bizLogicOutDoc; //* 수동가이드 예정 (as-is) XMLUtil.toArrayList(bizLogicOutDoc)*/;
                        }
                        AppLog.info("분할정보 ::: " +  ("") /* 주석처리(as-is) XMLUtil.indent(bizLogicOutDoc)*/);
                        // 지분별분할관리번호 = (공사ID^통보차수^개별보증구분코드(보증채권자구분)^도급자번호^하수급자번호^재하수급번호^건설기계대여업체번호^부품제작납품업체번호)
                        quotCbyPrttMnno = MapDataUtil.getString(bascDoc, "WRKS_ID") + "^" + MapDataUtil.getString(bascDoc, "NTFC_ORSEQ") + "^" + MapDataUtil.getString(bascDoc, "INDV_GURT_DSCD") + "^" + MapDataUtil.getString(bascDoc, "CTRR_NO") + "^" + MapDataUtil.getString(bascDoc, "SBCM_NO") + "^" + MapDataUtil.getString(bascDoc, "RSBC_NO") + "^" + MapDataUtil.getString(bascDoc, "CNMC_LNDN_ENTR_NO") + "^" + MapDataUtil.getString(bascDoc, "CMMF_LNDN_ENTR_NO");
                        for (int i = 0; i < tmpLst.size(); i++) {
                            lstDoc = (Map) tmpLst.get(i);
                            bascDoc = (Map) bascListArry.get(j);
                            AppLog.info("분할정보  lstDoc ::: " +  ("") /* 주석처리(as-is) XMLUtil.indent(lstDoc)*/);
                            // 수신받은 도급자의 경우에는 대표로 셋팅
                            // 대표여부
                            MapDataUtil.setString(bascDoc, "RPRS_YN", "");
                            AppLog.info("CTRR_BZRNO ::: " + MapDataUtil.getString(bascDoc, "CTRR_BZRNO"));
                            AppLog.info("BZRNO ::: " + MapDataUtil.getString(lstDoc, "BZRNO"));
                            if (MapDataUtil.getString(bascDoc, "CTRR_BZRNO").equals(MapDataUtil.getString(lstDoc, "BZRNO"))) {
                                // 대표여부
                                MapDataUtil.setString(bascDoc, "RPRS_YN", "Y");
                            }
                            // 지분별분할여부
                            MapDataUtil.setString(bascDoc, "QUOT_CBY_PRTT_YN", "Y");
                            // 지분별분할관리번호
                            MapDataUtil.setString(bascDoc, "QUOT_CBY_PRTT_MNNO", quotCbyPrttMnno);
                            // 도급자당사자번호
                            MapDataUtil.setString(bascDoc, "CTRR_BZRNO", MapDataUtil.getString(lstDoc, "BZRNO"));
                            // 도급자당사자번호
                            MapDataUtil.setString(bascDoc, "CTRR_PTNO", MapDataUtil.getString(lstDoc, "PTNO"));
                            // 건설업체명(도급자상호명)
                            MapDataUtil.setString(bascDoc, "CNEN_NM", MapDataUtil.getString(lstDoc, "CNEN_NM"));
                            // 포괄보증계약관리번호
                            MapDataUtil.setString(bascDoc, "INLV_CNRC_MNNO", MapDataUtil.getString(lstDoc, "CNRC_MNNO"));
                            // 포괄보증서번호
                            MapDataUtil.setString(bascDoc, "INLV_GUAS_NO", MapDataUtil.getString(lstDoc, "GUAS_NO"));
                            // 발급지점
                            MapDataUtil.setString(bascDoc, "ISSU_BRCD", MapDataUtil.getString(lstDoc, "ISSU_BRCD"));
                            // CNAMT
                            MapDataUtil.setString(bascDoc, "CNAMT", MapDataUtil.getString(lstDoc, "CNAMT"));
                            // 지분율 (도급자)
                            MapDataUtil.setString(bascDoc, "QTRT", MapDataUtil.getString(lstDoc, "QTRT"));
                            // GU0086(발급형태구분코드)
                            MapDataUtil.setString(bascDoc, "CMCM_CNRC_YN", "Y");
                            // 선급금액
                            MapDataUtil.setString(bascDoc, "PRPT_AMT", MapDataUtil.getString(lstDoc, "PRPT_AMT"));
                            // 기성금지급금액
                            MapDataUtil.setString(bascDoc, "RDPC_PAAMT", MapDataUtil.getString(lstDoc, "RDPC_PAAMT"));
                            bascNewDoc = new HashMap();
                            AppLog.info("분할정보  bascDoc ::: " +  ("") /* 주석처리(as-is) XMLUtil.indent(bascDoc)*/);
                            // listArry.add(bascDoc);	//신청내역저장리스트에 추가
                            // 신청내역저장
                            insertIndvApltDtlProc(bascDoc);
                        }
                    }
                } else {
                    // 지분별분할여부
                    MapDataUtil.setString(bascDoc, "QUOT_CBY_PRTT_YN", "");
                    // 지분별분할관리번호
                    MapDataUtil.setString(bascDoc, "QUOT_CBY_PRTT_MNNO", "");
                    // listArry.add(bascDoc);	//신청내역저장리스트에 추가
                    AppLog.info("insertIndvApltDtlProc(bascDoc) 2>>>>>\n[" +  ("") /* 주석처리(as-is) XMLUtil.indent(bascDoc)*/ + "]");
                    // 신청내역저장
                    insertIndvApltDtlProc(bascDoc);
                }
            }
            /*
             * 개별보증이 신청된 지점코드를 조회해 자동알림을 호출한다.               
             */
            bizInDoc = new HashMap();
            // 자동알림 통보시 사용할 공사ID
            MapDataUtil.setString(bizInDoc, "WRKS_ID", atmnWrksId);
            // 자동알림 통보시 사용할 통보차수
            MapDataUtil.setString(bizInDoc, "NTFC_ORSEQ", atmnNtfcOrseq);
            AppLog.info("com.cg.sa.gu.gurtinclusive.xda.gu_zgu_indv_aplt_dtl_so0005 parameter>>>>>\n[" +  ("") /* 주석처리(as-is) XMLUtil.indent(bizInDoc)*/ + "]");
            bizOutDoc = comCgSaGuGurtinclusiveGuzguindvapltdtlDAO.gu_zgu_indv_aplt_dtl_so0005(bizInDoc);
            AppLog.info("com.cg.sa.gu.gurtinclusive.xda.gu_zgu_indv_aplt_dtl_so0005 result>>>>>\n[" +  ("") /* 주석처리(as-is) XMLUtil.indent(bizOutDoc)*/ + "]");
            ArrayList aryAtmnList = bizOutDoc; //* 수동가이드 예정 (as-is) XMLUtil.toArrayList(bizOutDoc)*/;
            Iterator<Map> atmnItr = aryAtmnList.iterator();
            Map atmnListDoc = null;
            String atmnNotcRsltCnts = null;
            String currDay = null;
            currDay = com.inswave.ext.cg.util.DateUtil.getCurrentDate("yyyyMMdd");
            // 자동알림 내용 셋팅
            atmnNotcRsltCnts = "개별대금지급보증 신청내역이 있습니다.";
            while (atmnItr.hasNext()) {
                atmnListDoc = atmnItr.next();
                try {
                    /**
                     * ============ START#자동알림 =============
                     */
                    bizInDoc = new HashMap();
                    // 발생일자
                    MapDataUtil.setString(bizInDoc, "OCRN_BZDA", currDay);
                    // 항목ID
                    MapDataUtil.setString(bizInDoc, "ATMN_NOTC_ITEM_ID", "GU0010");
                    // 발생내용
                    MapDataUtil.setString(bizInDoc, "ATMN_NOTC_RSLT_CNTS", atmnNotcRsltCnts);
                    // 발생부서
                    MapDataUtil.setString(bizInDoc, "DPCD", MapDataUtil.getString(atmnListDoc, "ISSU_BRCD"));
                    // 최종변경일시
                    MapDataUtil.setString(bizInDoc, "LAST_CHNG_DTTM", currTimestamp);
                    // 최종수정자ID
                    MapDataUtil.setString(bizInDoc, "LAST_CHNR_ID", userId);
                    AppLog.info("개별보증신청내역 자동알림  ::: " +  ("") /* 주석처리(as-is) XMLUtil.indent(bizInDoc)*/);
//                    bizOutDoc = atmnNoticeSCService.insertAtmnNotice(bizInDoc);
                    atmnNoticeSCService.insertAtmnNotice(bizInDoc);
                    AppLog.info("개별보증신청내역 자동알림 호출 후 ::: " +  ("") /* 주석처리(as-is) XMLUtil.indent(bizOutDoc)*/);
                    /**
                     * ============ END#자동알림 =============
                     */
                } catch (ElException ignored) {
                    AppLog.warn(ignored.getMessage(), ignored);
                }
            }
        } catch (ElException e) {
            /**
             * 3.Exception 처리
             *  Framework Level Exception을 catch하여 임의 가공 처리 할 경우 Warning 객체 정의
             *  Exception 객체 상속구조: Throwable<-Exceltion<-Warning<-FrameworkWarning
             */
            if (AppLog.isWarnEnabled()) {
                AppLog.warn(e.getMessage(), e);
            }
            throw new CgAppUserException("CG_ERROR", 0, e.getMessage(), "SPLT0003", e);
        }
        AppLog.info("GurtInclusiveBC.java insertIndvApltDtl END!!!! >>>>>>>>>>>>>>>>\n[" +  ("") /* 주석처리(as-is) XMLUtil.indent(result)*/ + "]");
        /**
         * 4.결과 반환
         */
        return result;
    }

    /**
     * <<TITLE>>
     * 건설공사대장 수신 후 개별보증신청내역에 자료를 입력한다. (자료처리)
     * <<LOGIC>>
     * 1. 개별보증신청대상에대해 개별보증신청내역을 등록한다. (자료처리)
     * 2. 결과리턴
     * @param pDoc
     * @return
     * @throws Exception
     */
    public Map insertIndvApltDtlProc(Map pDoc) throws ElException, Exception {
        AppLog.info("GurtInclusiveBC.java insertIndvApltDtlProc START!!!! >>>>>>>>>>>>>>>>\n[" +  ("") /* 주석처리(as-is) XMLUtil.indent(pDoc)*/ + "]");
        /**
         * 1.Document 변수의 정의
         *
         * XDA 결과 변수 result
         */
        Map result = null;
        Map bizInput = null;
        Map bizInDoc = null;
        Map bizOutDoc = null;
        Map bizSaveInput = null;
        Map bizSaveBasicInput = null;
        Map bizSaveAdrsInput = null;
        Map bizLogicInDoc = null;
        Map bizLogicOutDoc = null;
        Map bascDoc = null;
        // 당사자주소처리
        ArrayList<Map> vecAdrsList = null;
        String currTimestamp = null;
        String userId = null;
        // 하수급업체 법인당사자번호
        String ptno = null;
        // 하수급업체 사업자당사자번호
        String bzrPtno = null;
        // 지분별분할관리번호
        String quotCbyPrttMnno = null;
        // 지분율
        String qtrt = null;
        // 자동알림 통보시 사용할 공사ID
        String atmnWrksId = "";
        // 자동알림 통보시 사용할 통보차수
        String atmnNtfcOrseq = "";
        long bnamt = 0;
        currTimestamp = com.inswave.ext.cg.util.DateUtil.getTimestamp();
        try {
            //XDA xda = XDAFactory.getXDA(Constants.KEEP_CONNECTION);
            userId = "MCI";
            bascDoc = pDoc;
            AppLog.info("개별보증신청내역  bascDoc ::: " +  ("") /* 주석처리(as-is) XMLUtil.indent(bascDoc)*/);
            // 개별보증채권자 (하수급업체, 건설기계대여업체 등 )가  고객에 등록되어 있지않으면 고객에 등록해줘야한다.
            /**
             * 2012.06.20 박기석
             * 당사자취득방법개선
             * 1. 사업자번호로 당사자번호를 등록한다.
             * 2. 법인번호로 당사자를 등록하면서 사업자와 당사자관계를 맺을 수 있도록 해준다.
             */
            /**
             * 사업자 당사자 등록
             */
            // 사업자번호로 하수급인의 PTNO를 조회해온다.
            bizInDoc = new HashMap();
            // 확약인(개별보증채권자) 사업자번호
            MapDataUtil.setString(bizInDoc, "CUNO", MapDataUtil.getString(bascDoc, "BZRNO"));
            AppLog.info("com.cg.sa.gu.gurtinclusive.xda.gu_zcu_party_so0001 >>>>>>>>\n[" +  ("") /* 주석처리(as-is) XMLUtil.indent(bizInDoc)*/ + "]");
            bizOutDoc = comCgSaGuGurtinclusiveGuzcupartyDAO.gu_zcu_party_so0001(bizInDoc);
            if (bizOutDoc == null) {
                // 고객에 등록되어 있지 않은 경우에 고객등록 인터페이스 호출
                try {
                    bizSaveInput = new HashMap();
                    // 당사자기본정보
                    bizSaveBasicInput = new HashMap();
                    // 등록:2 수정:1
                    MapDataUtil.setAttribute(bizSaveBasicInput, "status", "2");
                    MapDataUtil.setString(bizSaveBasicInput, "CALL_DSCD", "IA00");
                    // 사업자 4
                    MapDataUtil.setString(bizSaveBasicInput, "PRTY_TPCD", "4");
                    // 사업자번호
                    MapDataUtil.setString(bizSaveBasicInput, "CUNO", MapDataUtil.getString(bascDoc, "BZRNO"));
                    // 업체명
                    MapDataUtil.setString(bizSaveBasicInput, "PRTY_NM", MapDataUtil.getString(bascDoc, "ETNM"));
                    // 사업자등록번호 21
                    MapDataUtil.setString(bizSaveBasicInput, "CUNO_KNCD", "21");
                    // 고객여부
                    MapDataUtil.setString(bizSaveBasicInput, "CUST_YN", "N");
                    bizSaveInput.putAll(bizSaveBasicInput);
                    AppLog.info("사업자당사자 인터페이스 호출 ::: " +  ("") /* 주석처리(as-is) XMLUtil.indent(bizSaveInput)*/);
                    bizOutDoc = custMgmtSCService.saveCustReg(bizSaveInput);
                    bzrPtno = MapDataUtil.getString(bizOutDoc, "PTNO");
                } catch (ElException ignored) {
                    AppLog.warn(ignored.getMessage(), ignored);
                    // 당사자 인터페이스시 오류가 나도 무시한다.
                    bzrPtno = "";
                }
            } else {
                bzrPtno = MapDataUtil.getString(bizOutDoc, "PTNO");
            }
            /**
             * 법인 당사자 등록
             */
            // 법인번호로 하수급인의 PTNO를 조회해온다.
            bizInDoc = new HashMap();
            // 2012.06.11 박기석 - 개별보증채권자 당사자는 법인번호로 사용하도록 처리
            // 확약인(개별보증채권자) 법인번호
            MapDataUtil.setString(bizInDoc, "CUNO", MapDataUtil.getString(bascDoc, "CRNO"));
            AppLog.info("com.cg.sa.gu.gurtinclusive.xda.gu_zcu_party_so0001 >>>>>>>>\n[" +  ("") /* 주석처리(as-is) XMLUtil.indent(bizInDoc)*/ + "]");
            bizOutDoc = comCgSaGuGurtinclusiveGuzcupartyDAO.gu_zcu_party_so0001(bizInDoc);
            AppLog.info("법인 하수급인조회   bizOutDoc ::: " +  ("") /* 주석처리(as-is) XMLUtil.indent(bizOutDoc)*/);
           	if (bizOutDoc == null) {
                // 고객에 등록되어 있지 않은 경우에 고객등록 인터페이스 호출
                try {
                    // 고객고유번호종류코드
                    String cunoKncd = "";
                    // 당사자유형코드
                    String prtyTpcd = "";
                    // 법인번호에 맞는 당사자 유형 셋팅
                    cunoKncd = isRrno(MapDataUtil.getString(bascDoc, "CRNO"));
                    // 당사자유형코드 = "1":법인
                    if ("11".equals(cunoKncd))
                        prtyTpcd = "1";
                    // 당사자유형코드 = "4":사업자
                    if ("21".equals(cunoKncd))
                        prtyTpcd = "4";
                    // 당사자유형코드 = "2":개인
                    if ("31".equals(cunoKncd) || "32".equals(cunoKncd))
                        prtyTpcd = "2";
                    bizSaveInput = new HashMap();
                    // 당사자기본정보
                    bizSaveBasicInput = new HashMap();
                    // 등록:2 수정:1
                    MapDataUtil.setAttribute(bizSaveBasicInput, "status", "2");
                    MapDataUtil.setString(bizSaveBasicInput, "CALL_DSCD", "IA00");
                    // [M] CU0035(당사자유형코드)당사자유형코드 [1 법인, 2 개인, 3 기타단체, 4 사업자, 5 내부조직, 6 직원]
                    MapDataUtil.setString(bizSaveBasicInput, "PRTY_TPCD", prtyTpcd);
                    // 법인등록번호
                    MapDataUtil.setString(bizSaveBasicInput, "CUNO", MapDataUtil.getString(bascDoc, "CRNO"));
                    // 업체명
                    MapDataUtil.setString(bizSaveBasicInput, "PRTY_NM", MapDataUtil.getString(bascDoc, "ETNM"));
                    // [M] CU0096(고객고유번호종류코드)고객고유번호종류코드 [11 법인등록번호, 21 사업자등록번호, 31 주민등록번호, 32 외국인등록번호, 41 국가기관등록번호, 42 고유번호, 51 부서코드, 61 사원번호, 71 국가기관등록번호]
                    MapDataUtil.setString(bizSaveBasicInput, "CUNO_KNCD", cunoKncd);
                    // 법인유형코드 (CU0058) [07:민간법인]
                    MapDataUtil.setString(bizSaveBasicInput, "CRPT_TPCD", "07");
                    // 고객여부
                    MapDataUtil.setString(bizSaveBasicInput, "CUST_YN", "N");
                    bizSaveInput.putAll(bizSaveBasicInput);
                    // 주소가 있는경우에는 당사자 주소정보를 같이 셋팅해준다.
                    if (!("").equals(MapDataUtil.getString(bascDoc, "POST_CODE")) && !("").equals(MapDataUtil.getString(bascDoc, "ENTR_ADRS"))) {
                        // 당사자주소정보
                        vecAdrsList = new ArrayList<Map>();
                        bizSaveAdrsInput = new HashMap();
                        // 사업자 당사자번호셋팅 (관계를 맺어주기 위해)
                        MapDataUtil.setString(bizSaveAdrsInput, "PTNO", bzrPtno);
                        // [M] 고객주소유형코드 [01 소재지, 02 연락처]
                        MapDataUtil.setString(bizSaveAdrsInput, "CUST_ADRS_TPCD", "01");
                        // [M] 우편번호
                        MapDataUtil.setString(bizSaveAdrsInput, "ZPCD", MapDataUtil.getString(bascDoc, "POST_CODE").replaceAll("-", ""));
                        // [M] 기본주소
                        MapDataUtil.setString(bizSaveAdrsInput, "BASC_ADRS", MapDataUtil.getString(bascDoc, "ENTR_ADRS"));
                        // [O] 상세주소
                        MapDataUtil.setString(bizSaveAdrsInput, "DTL_ADRS", "");
                        // [M] 전체주소
                        MapDataUtil.setString(bizSaveAdrsInput, "ALL_ADRS", MapDataUtil.getString(bascDoc, "ENTR_ADRS"));
                        vecAdrsList.add(bizSaveAdrsInput);
                        // 주소정보
                        //MapDataUtil.setVector(bizSaveInput, "PARTY_ADRS", /* 주석처리(as-is) XMLUtil.toXML(vecAdrsList)*/);
                        MapDataUtil.setList(bizSaveInput, "PARTY_ADRS", vecAdrsList);
                    }
                    AppLog.info("법인 당사자 인터페이스 호출 ::: " +  ("") /* 주석처리(as-is) XMLUtil.indent(bizSaveInput)*/);
                    bizOutDoc = custMgmtSCService.saveCustReg(bizSaveInput);
                    ptno = MapDataUtil.getString(bizOutDoc, "PTNO");
                    // 당사자 등록 후에는 당사자관계를 맺어준다.
                    // 고객_당사자관계정보 세팅
                    if (!"".equals(bzrPtno)) {
                        bizInput = new HashMap();
                        // 당사자번호
                        MapDataUtil.setString(bizInput, "PTNO", ptno);
                        // 당사자관계유형코드 : 법인사업자
                        MapDataUtil.setString(bizInput, "PRTY_RLTN_TPCD", CUCBConstants.PRTY_RLTN_TP_BZMN);
                        // 상대당사자번호
                        MapDataUtil.setString(bizInput, "PATR_PTNO", bzrPtno);
                        // 대표사업자여부
                        MapDataUtil.setString(bizInput, "RPRS_BZMN_YN", CUCBConstants.YN_YES);
                        // 최종변경자ID
                        MapDataUtil.setString(bizInput, "LAST_CHNR_ID", "MCI");
                        AppLog.info("com.cg.cu.cb.customermgmt.xda.cb_zcu_prty_rltn_io0001 >>>>>>>>\n[" +  ("") /* 주석처리(as-is) XMLUtil.indent(bizInput)*/ + "]");
//                        bizOutDoc = comCgCuCbCustomermgmtCbzcuprtyrltnDAO.cb_zcu_prty_rltn_io0001(bizInput);
                        comCgCuCbCustomermgmtCbzcuprtyrltnDAO.cb_zcu_prty_rltn_io0001(bizInput);
                        // 2017.11.01 김원호 - 당사자관계일련번호관리 테이블에 기존 ptno, prty_rltn_tpcd 존재여부확인 후
                        // 신규시에는 당사자관계일련번호관리 table에 insert, 그 이외에는 update하여 당사자관계 테이블 최대 srno와 동기화
                        comCgCuCbCustomermgmtCbzcuprtyrltnsrnomngmDAO.cb_zcu_prty_rltn_srno_mngm_mo0001(bizInput);
                        /*
	                     * 고객_당사자관계 이력로그 등록
	                     */
                        // 
                        MapDataUtil.setString(bizInput, "LOG_HDLR_EMPNO", "MCI");
                        // 
                        MapDataUtil.setString(bizInput, "LOG_HNDL_BRCD", "11000");
                        // 로그 작업구분 : I/U/D
                        MapDataUtil.setString(bizInput, "LOG_WRK_DSCD", "I");
                        // 로그 처리일자 : 영업일
                        MapDataUtil.setString(bizInput, "LOG_HNDL_DATE", MapDataUtil.getString(bascDoc, "APDA"));
                        // *화면ID
                        MapDataUtil.setString(bizInput, "LOG_PAGE_ID", "MCI");
                        // *서비스ID
                        MapDataUtil.setString(bizInput, "LOG_SVC_ID", "MCI");
                        AppLog.info("com.cg.cu.cb.customermgmt.xda.cb_zcu_prty_rltn_l_io0001 >>>>>>>>\n[" +  ("") /* 주석처리(as-is) XMLUtil.indent(bizInput)*/ + "]");
                        comCgCuCbCustomermgmtCbzcuprtyrltnlDAO.cb_zcu_prty_rltn_l_io0001(bizInput);
                    }
                } catch (ElException ignored) {
                    AppLog.warn(ignored.getMessage(), ignored);
                    // 당사자 인터페이스시 오류가 나도 무시한다.
                    ptno = "";
                }
            } else {
                ptno = MapDataUtil.getString(bizOutDoc, "PTNO");
            }
            // 당사자번호(확약인)
            MapDataUtil.setString(bascDoc, "PTNO", ptno);
            // 1인명의 여부 테이블에 맞도록 설정
            if (MapDataUtil.getString(bascDoc, "CMCM_CNRC_YN").equals("N")) {
                // 1인명의
                MapDataUtil.setString(bascDoc, "ISSU_SHPE_DSCD", "1");
            } else {
                // 각자명의
                MapDataUtil.setString(bascDoc, "ISSU_SHPE_DSCD", "2");
            }
            // 보증금액 산출
            AppLog.info(" 보증금액산출전 !! ");
            // 보증금액산출시 에러는 무시..!! (인터페이스이기때문에... 에러나도 처리가 되야한다.)
            try {
                bnamt = calcIndvBnamt(bascDoc);
            } catch (ElException ignored) {
                AppLog.warn(ignored.getMessage(), ignored);
                // 오류가나면 보증금액은 0이다.
                bnamt = 0;
            }
            MapDataUtil.setLong(bascDoc, "BNAMT", bnamt);
            /*
             * 수수료계산호출
             */
            // 사업자번호로 도급인의 PTNO를 조회해온다.
            bizInDoc = new HashMap();
            // 도급자사업자번호
            MapDataUtil.setString(bizInDoc, "CUNO", MapDataUtil.getString(bascDoc, "CTRR_BZRNO"));
            AppLog.info("com.cg.sa.gu.gurtinclusive.xda.gu_zcu_party_so0001 >>>>>>>>\n[" +  ("") /* 주석처리(as-is) XMLUtil.indent(bizInput)*/ + "]");
            bizOutDoc = comCgSaGuGurtinclusiveGuzcupartyDAO.gu_zcu_party_so0001(bizInDoc);
            if (bizOutDoc == null || bnamt == 0) {
                // 당사자번호를 알지못하면 수수료계산을 할 수 없다. || 보증금액이 0이면 수수료계산할 수 없다.
                MapDataUtil.setString(bascDoc, "PRMM", "0");
            } else {
                // 도급자 법인 당자사번호
                MapDataUtil.setString(bizInDoc, "PTNO", MapDataUtil.getString(bizOutDoc, "CRNO_PTNO"));
                // 보증상태코드
                MapDataUtil.setString(bizInDoc, "GURT_STCD", MapDataUtil.getString(bascDoc, "GURT_STCD"));
                // 신청일자
                MapDataUtil.setString(bizInDoc, "APDA", MapDataUtil.getString(bascDoc, "APDA"));
                // 보증기간시작일자
                MapDataUtil.setString(bizInDoc, "GURT_PROD_STDA", MapDataUtil.getString(bascDoc, "GURT_PROD_STDA"));
                // 보증기간종료일자
                MapDataUtil.setString(bizInDoc, "GURT_PROD_ENDA", MapDataUtil.getString(bascDoc, "GURT_PROD_ENDA"));
                // 계약형태코드
                MapDataUtil.setString(bizInDoc, "CNRC_SHCD", MapDataUtil.getString(bascDoc, "ISSU_SHPE_DSCD"));
                // 보증금액
                MapDataUtil.setString(bizInDoc, "BNAMT", MapDataUtil.getString(bascDoc, "BNAMT"));
                // 공사관리번호
                MapDataUtil.setString(bizInDoc, "WRKS_MNNO", MapDataUtil.getString(bascDoc, "WRKS_MNNO"));
                // 수수료계산시 오류가 나도 무시되도록 처리
                try {
                    AppLog.info("수수료금액산출 전  bizInDoc ::: " +  ("") /* 주석처리(as-is) XMLUtil.indent(bizInDoc)*/);
                    bizOutDoc = gurtCommonSCService.calculatePremiumIndvPrcePayn(bizInDoc);
                    AppLog.info("수수료금액산출 후  bizOutDoc ::: " +  ("") /* 주석처리(as-is) XMLUtil.indent(bizOutDoc)*/);
                    // 계산된 수수료 셋팅
                    MapDataUtil.setString(bascDoc, "PRMM", MapDataUtil.getString(bizOutDoc, "PRMM"));
                } catch (ElException ignored) {
                    AppLog.warn(ignored.getMessage(), ignored);
                    // 수수료계산시 오류가 발생하면 수수료는 0원으로 셋팅
                    MapDataUtil.setString(bascDoc, "PRMM", "0");
                    // 수수료계산시에 throw로인해 contection이 끊어진경우에는 다시 연결해줘야한다.
//                    xda = null;
                    //xda = XDAFactory.getXDA(Constants.KEEP_CONNECTION);
                }
            }
            // 개별보증신청내역 등록
            MapDataUtil.setString(bascDoc, "LAST_CHNG_DTTM", currTimestamp);
            MapDataUtil.setString(bascDoc, "LAST_CHNR_ID", userId);
            AppLog.info("개별보증신청내역 등록 ::: " +  ("") /* 주석처리(as-is) XMLUtil.indent(bascDoc)*/);
            // 등록
            comCgSaGuGurtinclusiveGuzguindvapltdtlDAO.gu_zgu_indv_aplt_dtl_io0001(bascDoc);
        } catch (ElException e) {
            /**
             * 3.Exception 처리
             *  Framework Level Exception을 catch하여 임의 가공 처리 할 경우 Warning 객체 정의
             *  Exception 객체 상속구조: Throwable<-Exceltion<-Warning<-FrameworkWarning
             */
            if (AppLog.isWarnEnabled()) {
                AppLog.warn(e.getMessage(), e);
            }
            throw new CgAppUserException("CG_ERROR", 0, e.getMessage(), "SPLT0003", e);
        }
        AppLog.info("GurtInclusiveBC.java insertIndvApltDtlProc END!!!! >>>>>>>>>>>>>>>>\n[" +  ("") /* 주석처리(as-is) XMLUtil.indent(result)*/ + "]");
        /**
         * 4.결과 반환
         */
        return result;
    }

    /**
     * <<TITLE>>
     * 고객고유번호종류코드 유형을 리턴한다.
     * <<LOGIC>>
     * 1. 10자리일 경우 "21"(사업자번호) 리턴
     * 2. 주민등록번호이면서 한국인일 경우 "31"(주민등록번호) 리턴
     * 3. 주민등록번호이면서 외국인일 경우 "32"(외국인 주민등록번호) 리턴
     * 4. 주민등록번호가 아닐 경우 "11"(법인등록번호) 리턴
     * @param String tpciCd
     * @return String tpciCd
     * @throws Exception
     */
    private static String isRrno(String cuno) {
        boolean isKorean = true;
        int check = 0;
        if (cuno == null)
            return "";
        else // 사업자번호
        if (cuno.length() == 10)
            return "21";
        // 주민등록번호(1 - 6) -> 년월일 체크, 주민등록번호(7) -> 1 ~ 4 추가(2010.8.23)
        // 주민등록번호가 아닐 경우 법인등록번호
        int month = Integer.parseInt(cuno.substring(2, 4));
        int day = Integer.parseInt(cuno.substring(4, 6));
        int dscd = Integer.parseInt(cuno.substring(6, 7));
        if (month < 1 || month > 12)
            return "11";
        else if (day < 1 || day > 31)
            return "11";
        else if (dscd < 1 || dscd > 8)
            return "11";
        if (dscd > 4 && dscd < 9) {
            isKorean = false;
        }
        for (int i = 0; i < 12; i++) {
            if (isKorean)
                check += ((i % 8 + 2) * Character.getNumericValue(cuno.charAt(i)));
            else
                check += ((9 - i % 8) * Character.getNumericValue(cuno.charAt(i)));
        }
        if (isKorean) {
            check = 11 - (check % 11);
            check %= 10;
        } else {
            int remainder = check % 11;
            if (remainder == 0)
                check = 1;
            else if (remainder == 10)
                check = 0;
            else
                check = remainder;
            int check2 = check + 2;
            if (check2 > 9)
                check = check2 - 10;
            else
                check = check2;
        }
        if (check == Character.getNumericValue(cuno.charAt(12))) {
            if (// 주민등록번호
            isKorean == true)
                // 주민등록번호
                return "31";
            else
                // 외국인 주민등록번호
                return "32";
        } else
            // 법인등록번호
            return "11";
    }

    /**
     * <<TITLE>>
     * 포괄보증 해제시에 포괄보증의 보증잔액과 수수료잔액을 수정한다.
     * <<LOGIC>>
     * 1. 포괄보증 해제시에 포괄보증의 보증잔액과 수수료잔액을 수정한다.
     * 2. 결과리턴
     * @param pDoc
     * @return
     * @throws Exception
     */
    public Map updateInlvReleasePrmmGurtBaln(Map pDoc) throws ElException, Exception {
        /**
         * 1.Document 변수의 정의
         *
         * XDA 결과 변수 result
         */
        Map result = null;
        Map inDoc = null;
        Map outDoc = null;
        //UserSession userSession = null;
        String errCd;
        String gurtStcd = "";
        // 업무승인상태코드 (B1:승인완료, B2:승인취소)
        String bsapStcd = "";
        // 업무승인상태에따른 곱하기 값 (승인취소시에는 반대로 처리해야한다. )
        int stcdAmt = 1;
        try {
            // 포괄보증 수수료잔액
            long inlvPrmmBaln = 0;
            // 포괄보증 보증금액
            long inlvGurtBaln = 0;
            // 포괄보증 수수료잔액 Temp
            long inlvPrmmBalnTemp = 0;
            // 포괄보증 보증금액  Temp
            long inlvGurtBalnTemp = 0;
            //userSession = (UserSession) ContextUtil.getUserData("userSession") ---> (해당 라인의 소스는 ContextUtil 변환을 지원하지 않습니다. / getUserData);
            //XDA xda = XDAFactory.getXDA(Constants.KEEP_CONNECTION);
            inDoc = new HashMap();
            MapDataUtil.setString(inDoc, "CNRC_MNNO", MapDataUtil.getString(pDoc, "CNRC_MNNO"));
            gurtStcd = MapDataUtil.getString(pDoc, "GURT_STCD");
            bsapStcd = MapDataUtil.getString(pDoc, "BSAP_STCD");
            // 포괄보증 직접 잔액관리는 해제/해제취소시에만 발생된다. (잘못 호출된 경우에도 처리되지 않도록 return)
            if (!gurtStcd.equals("F") && !gurtStcd.equals("I")) {
                result = new HashMap();
                return result;
            }
            // 승인취소라면 승인시와 반대로 금액을 처리해줘야한다. (-1)*기존로직
            if (bsapStcd.equals(SAGUConstants.BSAP_STCD_B2)) {
                stcdAmt = -1;
            }
            // 포괄보증 해제/해제취소시 포괄보증 잔액관리를 위해 대상 및 금액을 추출
            outDoc = comCgSaGuGurtinclusiveGuzguguasDAO.gu_zgu_guas_so0013(inDoc);
            // 포괄보증 수수료잔액
            inlvPrmmBaln = MapDataUtil.getLong(outDoc, "INLV_PRMM_BALN");
            // 포괄보증 보증금액
            inlvGurtBaln = MapDataUtil.getLong(outDoc, "INLV_GURT_BALN");
            if (gurtStcd.equals("F")) {
                // 해제인경우
                // 해제금액
                inlvGurtBalnTemp = MapDataUtil.getLong(outDoc, "RLSE_EXCA_AMT");
                // 해제취소금액
                inlvPrmmBalnTemp = MapDataUtil.getLong(outDoc, "PRMM");
            } else {
                // 해제취소인경우
                // 해제취소인경우는 반대금액으로 처리해야한다.
                // 해제금액
                inlvGurtBalnTemp = (-1) * MapDataUtil.getLong(outDoc, "RLSE_EXCA_AMT");
                // 해제취소금액
                inlvPrmmBalnTemp = (-1) * MapDataUtil.getLong(outDoc, "PRMM");
            }
            // 포괄보증잔액
            inlvGurtBaln = inlvGurtBaln - ((stcdAmt) * inlvGurtBalnTemp);
            // 포괄수수료잔액 (해제수수료는 환불수수료이기때문에 더해주는것이 빼주는 것이다.)
            inlvPrmmBaln = inlvPrmmBaln + ((stcdAmt) * inlvPrmmBalnTemp);
            // 포괄보증의 보증잔액과 수수료잔액을 수정한다.
            inDoc = new HashMap();
            MapDataUtil.setString(pDoc, "INLV_PRMM_BALN", "" + inlvPrmmBaln);
            MapDataUtil.setString(pDoc, "INLV_GURT_BALN", "" + inlvGurtBaln);
            MapDataUtil.setString(pDoc, "LAST_CHNG_DTTM", (String) UserHeaderUtil.getInstance().getTimestamp());
            MapDataUtil.setString(pDoc, "LAST_CHNR_ID", UserHeaderUtil.getInstance().getEmpno());
            MapDataUtil.setString(pDoc, "PATY_TPCD", "100");
            MapDataUtil.setString(pDoc, "PATY_TYPE_SRNO", MapDataUtil.getString(outDoc, "CHNG_SRNO"));
            MapDataUtil.setString(pDoc, "CNRC_MNNO", MapDataUtil.getString(outDoc, "CHNG_DSGN_TRGT_CNRC_MNNO"));
            AppLog.info("\n" + "com.cg.sa.gu.gurtinclusive.xda.gu_zgu_cnrc_prty_gurt_aplt_uo0001 XML INPUT -----------------------------");
//             AppLog.info(/* 주석처리(as-is) XMLUtil.serialize(pDoc)*/);
            comCgSaGuGurtinclusiveGuzgucnrcprtygurtapltDAO.gu_zgu_cnrc_prty_gurt_aplt_uo0001(pDoc);
        } catch (ElException e) {
            /**
             * 3.Exception 처리
             *  Framework Level Exception을 catch하여 임의 가공 처리 할 경우 Warning 객체 정의
             *  Exception 객체 상속구조: Throwable<-Exceltion<-Warning<-FrameworkWarning
             */
            if (AppLog.isWarnEnabled()) {
                AppLog.warn(e.getMessage(), e);
            }
            throw new CgAppUserException("CG_ERROR", 0, e.getMessage(), "SPLT0003", e);
        }
        /**
         * 4.결과 반환
         */
        return result;
    }

    /**
     * <<TITLE>>
     * 포괄(개별)대금지급보증에 대한 키스콘 전송상태를 조회한다.
     * <<LOGIC>>
     * 1. 포괄(개별)대금지급보증에 대한 키스콘 전송상태 조회
     * >(XDA 수행 : com.cg.sa.gu.gurtinclusive.xda.gu_zgu_guas_h_so0001)
     * 2. 결과리턴
     * @param pDoc
     * @return
     * @throws Exception
     */
    public ArrayList<Map> selectInclusiveGuasKisconTnsmStat(Map pDoc) throws ElException, Exception {
        /**
         * 1.Document 변수의 정의
         *
         * XDA 결과 변수 result
         */
        ArrayList<Map> result = null;
        try {
            /**
             * 2.XDA를 실행합니다.
             * 호출하려는 XDAID를 입력합니다.
             */
            //XDA xda = XDAFactory.getXDA(Constants.KEEP_CONNECTION);
            // 설계건의 신청자조회
            result = comCgSaGuGurtinclusiveGuzguguashDAO.gu_zgu_guas_h_so0001(pDoc);
        } catch (ElException e) {
            /**
             * 3.Exception 처리
             *  Framework Level Exception을 catch하여 임의 가공 처리 할 경우 Warning 객체 정의
             *  Exception 객체 상속구조: Throwable<-Exceltion<-Warning<-FrameworkWarning
             */
            if (AppLog.isWarnEnabled()) {
                AppLog.warn(e.getMessage(), e);
            }
            throw new CgAppUserException("CG_ERROR", 0, e.getMessage(), "SPLT0003", e);
        }
        /**
         * 4.결과 반환
         */
        return result;
    }

    /**
     * <<TITLE>>
     * 개별대금지급보증 목록조회
     * <<LOGIC>>
     * 1. 포괄(개별)대금지급보증에 대한 키스콘 전송상태 조회
     * >(XDA 수행 : com.cg.sa.gu.gurtinclusive.xda.gu_zgu_indv_aplt_dtl_so0001)
     * 2. 결과리턴
     * @param pDoc
     * @return
     * @throws Exception
     */
    public ArrayList<Map> selectIndvApltDtl(Map pDoc) throws ElException, Exception {
        /**
         * 1.Document 변수의 정의
         *
         * XDA 결과 변수 result
         */
        ArrayList<Map> result = null;
        try {
            /**
             * 2.XDA를 실행합니다.
             * 호출하려는 XDAID를 입력합니다.
             */
            //XDA xda = XDAFactory.getXDA(Constants.KEEP_CONNECTION);
            // 개별대금지급보증 목록조회
            result = comCgSaGuGurtinclusiveGuzguindvapltdtlDAO.gu_zgu_indv_aplt_dtl_so0001(pDoc);
        } catch (ElException e) {
            /**
             * 3.Exception 처리
             *  Framework Level Exception을 catch하여 임의 가공 처리 할 경우 Warning 객체 정의
             *  Exception 객체 상속구조: Throwable<-Exceltion<-Warning<-FrameworkWarning
             */
            if (AppLog.isWarnEnabled()) {
                AppLog.warn(e.getMessage(), e);
            }
            throw new CgAppUserException("CG_ERROR", 0, e.getMessage(), "SPLT0003", e);
        }
        /**
         * 4.결과 반환
         */
        return result;
    }

    /**
     * <<TITLE>>
     * 확약서번호 생성
     * <<LOGIC>>
     * 1. 확약서번호 생성
     * >(XDA 수행 : com.cg.sa.gu.gurtinclusive.xda.gu_zgu_indv_aplt_dtl_uo0001)
     * 2. 결과리턴
     * @param pDoc
     * @return
     * @throws Exception
     */
    public Map createindvAgrmMnno(Map pDoc) throws ElException, Exception {
        /**
         * 1.Document 변수의 정의
         *
         * XDA 결과 변수 result
         */
        Map result = null;
        //UserSession userSession = null;
        // 계정약정번호(확약서번호)
        String indvAgrmMnno = "";
        try {
            //userSession = (UserSession) ContextUtil.getUserData("userSession") ---> (해당 라인의 소스는 ContextUtil 변환을 지원하지 않습니다. / getUserData);
            /**
             * 2.XDA를 실행합니다.
             * 호출하려는 XDAID를 입력합니다.
             */
            //XDA xda = XDAFactory.getXDA(Constants.KEEP_CONNECTION);
            // 계정약정번호(확약서번호) 조회
            result = comCgSaGuGurtinclusiveGuzagagrmindvafshDAO.gu_zag_agrm_indv_afsh_so0001(pDoc);
            // 계정약정번호(확약서번호)
            indvAgrmMnno = MapDataUtil.getString(result, "INDV_AGRM_MNNO");
            MapDataUtil.setString(pDoc, "INDV_AGRM_MNNO", indvAgrmMnno);
            MapDataUtil.setString(pDoc, "LAST_CHNR_ID", UserHeaderUtil.getInstance().getEmpno());
            MapDataUtil.setString(pDoc, "LAST_CHNG_DTTM", (String) UserHeaderUtil.getInstance().getTimestamp());
            // 공사관리번호
            MapDataUtil.setString(pDoc, "INDV_WRKS_MNNO", MapDataUtil.getString(pDoc, "WRKS_MNNO"));
            // 개별확약서 저장
            comCgSaGuGurtinclusiveGuzagagrmindvafshDAO.gu_zag_agrm_indv_afsh_io0001(pDoc);
            // 개별보증신청내역 확약서 update
            comCgSaGuGurtinclusiveGuzguindvapltdtlDAO.gu_zgu_indv_aplt_dtl_uo0001(pDoc);
            // 대표자여부
            String rprsYn = MapDataUtil.getString(pDoc, "RPRS_YN");
            if ("Y".equals(rprsYn)) {
                // 분할에 해당하는 나머지 업체들 일괄업데이트
                comCgSaGuGurtinclusiveGuzguindvapltdtlDAO.gu_zgu_indv_aplt_dtl_uo0006(pDoc);
            }
        } catch (ElException e) {
            /**
             * 3.Exception 처리
             *  Framework Level Exception을 catch하여 임의 가공 처리 할 경우 Warning 객체 정의
             *  Exception 객체 상속구조: Throwable<-Exceltion<-Warning<-FrameworkWarning
             */
            if (AppLog.isWarnEnabled()) {
                AppLog.warn(e.getMessage(), e);
            }
            throw new CgAppUserException("CG_ERROR", 0, e.getMessage(), "SPLT0003", e);
        }
        /**
         * 4.결과 반환
         */
        return result;
    }

    /**
     * <<TITLE>>
     * SMS을 발송한다
     * <<LOGIC>>
     * 1. 전화번호 조회
     * >(XDA 수행 : com.cg.sa.gu.gurtinclusive.xda.gu_zcu_cnpl_so0001)
     * 2. 결과리턴
     * @param pDoc
     * @return
     * @throws Exception
     */
    public int callSMS(Map pDoc) throws ElException, Exception {
        /**
         * 1.Document 변수의 정의
         *
         * XDA 결과 변수 result
         */
        int result = 0;
        Map outDoc = null;
        Map outDoc2 = null;
//        UserSession userSession = null;
        // 메세지
        String smsMsg = "";
        String cp1No = "";
        String cp2No = "";
        String cp3No = "";
        String rcTel1No = "";
        String rcTel2No = "";
        String rcTel3No = "";
        // 포괄보증번호
        String inlvGuasNo = "";
        // 확약서번호
        String indvAgrmMnno = "";
        // 1번일때는 개별대금지급보증 보증신청 조회 및 확약서 생성 화면(SAGUP020A00.xml)
        String gubun = "";
        // 2번일때는 포괄대금지급보증 잔액 및 수수료 관리 화면(SAGUP050A00.xml)
        try {
            //userSession = (UserSession) ContextUtil.getUserData("userSession") ---> (해당 라인의 소스는 ContextUtil 변환을 지원하지 않습니다. / getUserData);
            /**
             * 2.XDA를 실행합니다.
             * 호출하려는 XDAID를 입력합니다.
             */
            //XDA xda = XDAFactory.getXDA(Constants.KEEP_CONNECTION);
            MapDataUtil.setString(pDoc, "LAST_CHNR_ID", UserHeaderUtil.getInstance().getEmpno());
            MapDataUtil.setString(pDoc, "LAST_CHNG_DTTM", (String) UserHeaderUtil.getInstance().getTimestamp());
            // 전화번호 조회
            outDoc = comCgSaGuGurtinclusiveGuzcucnplDAO.gu_zcu_cnpl_so0001(pDoc);
           	if (outDoc == null) {
                throw new CgAppUserException("CG_ERROR", 0, "휴대폰번호가 미등록되어 있습니다. 입력 후 재 전송 해주세요", "E02005");
            } else {
                // 받는사람1
                cp1No = MapDataUtil.getString(outDoc, "BZMN_AENO");
                // 받는사람2
                cp2No = MapDataUtil.getString(outDoc, "TLNO_TONO");
                // 받는사람3
                cp3No = MapDataUtil.getString(outDoc, "TLNO_NO");
                // 보내는사람 전화번호
                outDoc2 = comCgSaGuGurtinclusiveGuzhrorgzDAO.gu_zhr_orgz_so0001(pDoc);
                // 보내는사람1
                rcTel1No = MapDataUtil.getString(outDoc2, "FIRSTNO");
                // 보내는는사람2
                rcTel2No = MapDataUtil.getString(outDoc2, "SECONDNO");
                // 보내는는사람3
                rcTel3No = MapDataUtil.getString(outDoc2, "THIRDNO");
                gubun = MapDataUtil.getString(pDoc, "GUBUN");
                // 개별대금지급보증 보증신청 조회 및 확약서 생성 화면(SAGUP020A00.xml)
                if ("1".equals(gubun)) {
                    // 포괄보증번호
                    inlvGuasNo = MapDataUtil.getString(pDoc, "INLV_GUAS_NO");
                    // 확약서번호
                    indvAgrmMnno = MapDataUtil.getString(pDoc, "INDV_AGRM_MNNO");
                    smsMsg = "포괄보증(" + inlvGuasNo + ")에 대한 연대채무확약서 번호는 <" + indvAgrmMnno + "> 입니다.";
                    // SMS발송여부 저장
                    result = comCgSaGuGurtinclusiveGuzagagrmindvafshDAO.gu_zag_agrm_indv_afsh_uo0001(pDoc);
                    // 포괄대금지급보증 잔액 및 수수료 관리 화면(SAGUP050A00.xml)
                } else if ("2".equals(gubun)) {
                    smsMsg = "수수료잔액 또는 보증잔액 소진율이 80%이상입니다.";
                }
                // SMS 발송
                MessageVO smsVO = MessageVO.setMessageVO("GU", "system", "system", smsMsg, // 받는사람
                cp1No, // 받는사람
                cp2No, // 받는사람
                cp3No, // 보내는사람
                rcTel1No, // 보내는사람
                rcTel2No, // 보내는사람
                rcTel3No, DateUtil.getCurrentDate("yyyy-MM-dd HH:mm:ss"),
                "", "", "", "", "", "", "");
                MessageAdaptor.callSMS(smsVO);
            }
        } catch (ElException e) {
            /**
             * 3.Exception 처리
             *  Framework Level Exception을 catch하여 임의 가공 처리 할 경우 Warning 객체 정의
             *  Exception 객체 상속구조: Throwable<-Exceltion<-Warning<-FrameworkWarning
             */
            if (AppLog.isWarnEnabled()) {
                AppLog.warn(e.getMessage(), e);
            }
            throw new CgAppUserException("CG_ERROR", 0, e.getMessage(), "SPLT0003", e);
        }
        /**
         * 4.결과 반환
         */
        return result;
    }

    /**
     * <<TITLE>>
     * 개별보증신청내역에 제출여부 및 기타 저장한다.
     * <<LOGIC>>
     * 1. 개별확약서에 제출여부확인 저장
     * >(XDA 수행 : com.cg.sa.gu.gurtinclusive.xda.gu_zag_agrm_indv_afsh_uo0002)
     * 2. 개별보증신청내역 저장
     * >(XDA 수행 : com.cg.sa.gu.gurtinclusive.xda.gu_zgu_indv_aplt_dtl_uo0002)
     * @param pDoc
     * @return
     * @throws Exception
     */
    public Map saveIndvApltDtl(Map pDoc) throws ElException, Exception {
        /**
         * 1.Document 변수의 정의
         *
         * XDA 결과 변수 result
         */
        Map result = null;
//        UserSession userSession = null;
        // 선택
        String chk = "";
        try {
            //userSession = (UserSession) ContextUtil.getUserData("userSession") ---> (해당 라인의 소스는 ContextUtil 변환을 지원하지 않습니다. / getUserData);
            /**
             * 2.XDA를 실행합니다.
             * 호출하려는 XDAID를 입력합니다.
             */
            //XDA xda = XDAFactory.getXDA(Constants.KEEP_CONNECTION);
            ArrayList aryList = (ArrayList<Map>) MapDataUtil.getList(pDoc, "result"); //* 수동가이드 예정 (as-is) XMLUtil.toArrayList(XMLUtil.getDocument(pDoc, "vector"))*/;
            Iterator<Map> itr = aryList.iterator();
            Map listDoc = null;
            while (itr.hasNext()) {
                listDoc = itr.next();
                // 선택
                chk = MapDataUtil.getString(listDoc, "CHK");
                // 체크된값만 저장
                if ("Y".equals(chk)) {
                    MapDataUtil.setString(listDoc, "LAST_CHNR_ID", UserHeaderUtil.getInstance().getEmpno());
                    MapDataUtil.setString(listDoc, "LAST_CHNG_DTTM", (String) UserHeaderUtil.getInstance().getTimestamp());
                    // 개별확약서에 제출여부확인 저장
                    comCgSaGuGurtinclusiveGuzagagrmindvafshDAO.gu_zag_agrm_indv_afsh_uo0002(listDoc);
                    // 개별보증신청내역 저장
                    comCgSaGuGurtinclusiveGuzguindvapltdtlDAO.gu_zgu_indv_aplt_dtl_uo0002(listDoc);
                    // 대표자여부
                    String rprsYn = MapDataUtil.getString(listDoc, "RPRS_YN");
                    if ("Y".equals(rprsYn)) {
                        // 분할에 해당하는 나머지 업체들 일괄업데이트
                        comCgSaGuGurtinclusiveGuzguindvapltdtlDAO.gu_zgu_indv_aplt_dtl_uo0006(listDoc);
                    }
                }
            }
        } catch (ElException e) {
            /**
             * 3.Exception 처리
             *  Framework Level Exception을 catch하여 임의 가공 처리 할 경우 Warning 객체 정의
             *  Exception 객체 상속구조: Throwable<-Exceltion<-Warning<-FrameworkWarning
             */
            if (AppLog.isWarnEnabled()) {
                AppLog.warn(e.getMessage(), e);
            }
            throw new CgAppUserException("CG_ERROR", 0, e.getMessage(), "SPLT0003", e);
        }
        /**
         * 4.결과 반환
         */
        return result;
    }

    /**
     * <<TITLE>>
     * 포괄보증 연대채무 확약서 신청인 정보 조회
     * <<LOGIC>>
     * 1. 포괄(개별)대금지급보증에 대한 키스콘 전송상태 조회
     * >(XDA 수행 : com.cg.sa.gu.gurtinclusive.xda.gu_zgu_indv_aplt_dtl_so0002)
     * 2. 결과리턴
     * @param pDoc
     * @return
     * @throws Exception
     */
    public Map selectIndvAgrmMnnoInfo(Map pDoc) throws ElException, Exception {
        /**
         * 1.Document 변수의 정의
         *
         * XDA 결과 변수 result
         */
        Map result = null;
        try {
            /**
             * 2.XDA를 실행합니다.
             * 호출하려는 XDAID를 입력합니다.
             */
            //XDA xda = XDAFactory.getXDA(Constants.KEEP_CONNECTION);
            // 포괄보증 연대채무 확약서 신청인 정보 조회
            result = comCgSaGuGurtinclusiveGuzguindvapltdtlDAO.gu_zgu_indv_aplt_dtl_so0002(pDoc);
        } catch (ElException e) {
            /**
             * 3.Exception 처리
             *  Framework Level Exception을 catch하여 임의 가공 처리 할 경우 Warning 객체 정의
             *  Exception 객체 상속구조: Throwable<-Exceltion<-Warning<-FrameworkWarning
             */
            if (AppLog.isWarnEnabled()) {
                AppLog.warn(e.getMessage(), e);
            }
            throw new CgAppUserException("CG_ERROR", 0, e.getMessage(), "SPLT0003", e);
        }
        /**
         * 4.결과 반환
         */
        return result;
    }

    /**
     * <<TITLE>>
     * 건설공사대장 수신 후 개별보증신청내역에 자료를 입력한다.
     * <<LOGIC>>
     * 1. 개별보증신청대상에대해 개별보증신청내역을 등록한다.
     * 2. 결과리턴
     * @param pDoc
     * @return
     * @throws Exception
     */
    public Map updateAgrmIndvAfshInfo(Map pDoc) throws ElException, Exception {
        /**
         * 1.Document 변수의 정의
         *
         * XDA 결과 변수 result
         */
        Map result = null;
        //UserSession userSession = null;
        try {
            //userSession = (UserSession) ContextUtil.getUserData("userSession") ---> (해당 라인의 소스는 ContextUtil 변환을 지원하지 않습니다. / getUserData);
            //XDA xda = XDAFactory.getXDA(Constants.KEEP_CONNECTION);
            // 포괄업무약정서 부가정보 저장
            MapDataUtil.setString(pDoc, "LAST_CHNG_DTTM", (String) UserHeaderUtil.getInstance().getTimestamp());
            MapDataUtil.setString(pDoc, "LAST_CHNR_ID", UserHeaderUtil.getInstance().getEmpno());
            comCgSaGuGurtinclusiveGuzagagrmindvafshDAO.gu_zag_agrm_indv_afsh_uo0003(pDoc);
            // 개별보증신청내역의 확약서 제출구분을 온라인으로 변경해준다.
            comCgSaGuGurtinclusiveGuzguindvapltdtlDAO.gu_zgu_indv_aplt_dtl_uo0004(pDoc);
        } catch (ElException e) {
            /**
             * 3.Exception 처리
             *  Framework Level Exception을 catch하여 임의 가공 처리 할 경우 Warning 객체 정의
             *  Exception 객체 상속구조: Throwable<-Exceltion<-Warning<-FrameworkWarning
             */
            if (AppLog.isWarnEnabled()) {
                AppLog.warn(e.getMessage(), e);
            }
            throw new CgAppUserException("CG_ERROR", 0, e.getMessage(), "SPLT0003", e);
        }
        /**
         * 4.결과 반환
         */
        return result;
    }

    /**
     * <<TITLE>>
     * 포괄대금지급보증 발급사실 공시를 조회
     * <<LOGIC>>
     * 1. 포괄대금지급보증 발급사실 공시를 조회
     * >(XDA 수행 : com.cg.sa.gu.gurtinclusive.xda.gu_zgu_guas_so0001)
     * 2. 결과리턴
     * @param pDoc
     * @return
     * @throws Exception
     */
    public ArrayList<Map> selectGuasNo(Map pDoc) throws ElException, Exception {
        /**
         * 1.Document 변수의 정의
         *
         * XDA 결과 변수 result
         */
        ArrayList<Map> result = null;
        try {
            /**
             * 2.XDA를 실행합니다.
             * 호출하려는 XDAID를 입력합니다.
             */
            //XDA xda = XDAFactory.getXDA(Constants.KEEP_CONNECTION);
            // 포괄대금지급보증 발급사실 공시를 조회
            result = comCgSaGuGurtinclusiveGuzguguasDAO.gu_zgu_guas_so0001(pDoc);
        } catch (ElException e) {
            /**
             * 3.Exception 처리
             *  Framework Level Exception을 catch하여 임의 가공 처리 할 경우 Warning 객체 정의
             *  Exception 객체 상속구조: Throwable<-Exceltion<-Warning<-FrameworkWarning
             */
            if (AppLog.isWarnEnabled()) {
                AppLog.warn(e.getMessage(), e);
            }
            throw new CgAppUserException("CG_ERROR", 0, e.getMessage(), "SPLT0003", e);
        }
        /**
         * 4.결과 반환
         */
        return result;
    }

    /**
     * <<TITLE>>
     * 개별대금지급보증 발급사실 공시를 조회한다.
     * <<LOGIC>>
     * 1. 포괄대금지급보증 발급사실 공시를 조회
     * >(XDA 수행 : com.cg.sa.gu.gurtinclusive.xda.gu_zgu_guas_so0001)
     * 2. 결과리턴
     * @param pDoc
     * @return
     * @throws Exception
     */
    public ArrayList<Map> selectPtno(Map pDoc) throws ElException, Exception {
        /**
         * 1.Document 변수의 정의
         *
         * XDA 결과 변수 result
         */
        ArrayList<Map> result = null;
        try {
            /**
             * 2.XDA를 실행합니다.
             * 호출하려는 XDAID를 입력합니다.
             */
            //XDA xda = XDAFactory.getXDA(Constants.KEEP_CONNECTION);
            // 개별대금지급보증 발급사실 공시를 조회
            result = comCgSaGuGurtinclusiveGuzguguasDAO.gu_zgu_guas_so0002(pDoc);
        } catch (ElException e) {
            /**
             * 3.Exception 처리
             *  Framework Level Exception을 catch하여 임의 가공 처리 할 경우 Warning 객체 정의
             *  Exception 객체 상속구조: Throwable<-Exceltion<-Warning<-FrameworkWarning
             */
            if (AppLog.isWarnEnabled()) {
                AppLog.warn(e.getMessage(), e);
            }
            throw new CgAppUserException("CG_ERROR", 0, e.getMessage(), "SPLT0003", e);
        }
        /**
         * 4.결과 반환
         */
        return result;
    }

    /**
     * <<TITLE>>
     * 기존보증서 발급정보 조회
     * <<LOGIC>>
     * 1. 기존보증서 발급정보 조회
     * >(XDA 수행 : com.cg.sa.gu.gurtinclusive.xda.gu_zgu_guas_so0001)
     * 2. 결과리턴
     * @param pDoc
     * @return
     * @throws Exception
     */
    public Map selectExistingGuasIssuInfm(Map pDoc) throws ElException, Exception {
        /**
         * 1.Document 변수의 정의
         *
         * XDA 결과 변수 result
         */
        Map result = null;
        ArrayList<Map> sqlResult = null;
        Map sqlResultMap = null;
        try {
            result = new HashMap();
            /**
             * 2.XDA를 실행합니다.
             * 호출하려는 XDAID를 입력합니다.
             */
            //XDA xda = XDAFactory.getXDA(Constants.KEEP_CONNECTION);
            // 보증서번호
            MapDataUtil.setString(pDoc, "INLV_GUAS_NO", MapDataUtil.getString(pDoc, "GUAS_NO"));
            // 포괄대금지급보증 발급정보를 조회한다.
            sqlResult = comCgSaGuGurtinclusiveGuzguguasDAO.gu_zgu_guas_so0004(pDoc);
            //MapDataUtil.setVector(result, "LIST1", sqlResult);
            MapDataUtil.setList(result, "LIST1", sqlResult);
            
            // 개별대금지급보증 발급정보를 조회한다.
            sqlResult = comCgSaGuGurtinclusiveGuzguguasDAO.gu_zgu_guas_so0005(pDoc);
            //MapDataUtil.setVector(result, "LIST2", sqlResult);
            MapDataUtil.setList(result, "LIST2", sqlResult);
            
            // 포괄보증 보증서번호로 포괄 및 개별대금 발급정보를 조회한다.
            sqlResultMap = comCgSaGuGurtinclusiveGuzguguasDAO.gu_zgu_guas_so0003(pDoc);
            result.putAll(sqlResultMap);
            
            // 키스콘 수신정보 (미발급된 개별대급지급보증 신청내역) 조회
            sqlResult = comCgSaGuGurtinclusiveGuzguguasDAO.gu_zgu_guas_so0006(pDoc);
            //MapDataUtil.setVector(result, "LIST3", sqlResult);
            MapDataUtil.setList(result, "LIST3", sqlResult);
        } catch (ElException e) {
            /**
             * 3.Exception 처리
             *  Framework Level Exception을 catch하여 임의 가공 처리 할 경우 Warning 객체 정의
             *  Exception 객체 상속구조: Throwable<-Exceltion<-Warning<-FrameworkWarning
             */
            if (AppLog.isWarnEnabled()) {
                AppLog.warn(e.getMessage(), e);
            }
            throw new CgAppUserException("CG_ERROR", 0, e.getMessage(), "SPLT0003", e);
        }
        /**
         * 4.결과 반환
         */
        return result;
    }

    /**
     * <<TITLE>>
     * 포괄보증 보증서번호로 포괄 및 개별대금 발급정보를 조회한다.
     * <<LOGIC>>
     * 1. 포괄보증 보증서번호로 포괄 및 개별대금 발급정보를 조회한다.
     * >(XDA 수행 : com.cg.sa.gu.gurtinclusive.xda.gu_zgu_guas_so0003)
     * 2. 결과리턴
     * @param pDoc
     * @return
     * @throws Exception
     */
    public Map selectInlvIndvAmt(Map pDoc) throws ElException, Exception {
        /**
         * 1.Document 변수의 정의
         *
         * XDA 결과 변수 result
         */
        Map result = null;
        try {
            /**
             * 2.XDA를 실행합니다.
             * 호출하려는 XDAID를 입력합니다.
             */
            //XDA xda = XDAFactory.getXDA(Constants.KEEP_CONNECTION);
            // 포괄보증 보증서번호로 포괄 및 개별대금 발급정보를 조회
            result = comCgSaGuGurtinclusiveGuzguguasDAO.gu_zgu_guas_so0003(pDoc);
        } catch (ElException e) {
            /**
             * 3.Exception 처리
             *  Framework Level Exception을 catch하여 임의 가공 처리 할 경우 Warning 객체 정의
             *  Exception 객체 상속구조: Throwable<-Exceltion<-Warning<-FrameworkWarning
             */
            if (AppLog.isWarnEnabled()) {
                AppLog.warn(e.getMessage(), e);
            }
            throw new CgAppUserException("CG_ERROR", 0, e.getMessage(), "SPLT0003", e);
        }
        /**
         * 4.결과 반환
         */
        return result;
    }

    /**
     * <<TITLE>>
     * 개별보증신청내역 조회
     * <<LOGIC>>
     * 1. 개별보증신청내역 조회
     * >(XDA 수행 : com.cg.sa.gu.gurtinclusive.xda.gu_zgu_indv_aplt_dtl_so0003)
     * 2. 결과리턴
     * @param pDoc
     * @return
     * @throws Exception
     */
    public ArrayList<Map> selectZguIndvApltDtl(Map pDoc) throws ElException, Exception {
        /**
         * 1.Document 변수의 정의
         *
         * XDA 결과 변수 result
         */
        ArrayList<Map> result = null;
        try {
            /**
             * 2.XDA를 실행합니다.
             * 호출하려는 XDAID를 입력합니다.
             */
            //XDA xda = XDAFactory.getXDA(Constants.KEEP_CONNECTION);
            // 개별대금지급보증 목록조회
            result = comCgSaGuGurtinclusiveGuzguindvapltdtlDAO.gu_zgu_indv_aplt_dtl_so0003(pDoc);
        } catch (ElException e) {
            /**
             * 3.Exception 처리
             *  Framework Level Exception을 catch하여 임의 가공 처리 할 경우 Warning 객체 정의
             *  Exception 객체 상속구조: Throwable<-Exceltion<-Warning<-FrameworkWarning
             */
            if (AppLog.isWarnEnabled()) {
                AppLog.warn(e.getMessage(), e);
            }
            throw new CgAppUserException("CG_ERROR", 0, e.getMessage(), "SPLT0003", e);
        }
        /**
         * 4.결과 반환
         */
        return result;
    }

    /**
     * <<TITLE>>
     * 포괄대금지급보증 잔액 및 수수료를 관리조회
     * <<LOGIC>>
     * 1. 포괄대금지급보증 잔액 및 수수료를 관리조회
     * >(XDA 수행 : com.cg.sa.gu.gurtinclusive.xda.gu_zgu_guas_so0007)
     * 2. 결과리턴
     * @param pDoc
     * @return
     * @throws Exception
     */
    public ArrayList<Map> selectBalnPrmmMngm(Map pDoc) throws ElException, Exception {
        /**
         * 1.Document 변수의 정의
         *
         * XDA 결과 변수 result
         */
        ArrayList<Map> result = null;
        try {
            /**
             * 2.XDA를 실행합니다.
             * 호출하려는 XDAID를 입력합니다.
             */
            //XDA xda = XDAFactory.getXDA(Constants.KEEP_CONNECTION);
            // 개별대금지급보증 목록조회
            result = comCgSaGuGurtinclusiveGuzguguasDAO.gu_zgu_guas_so0007(pDoc);
        } catch (ElException e) {
            /**
             * 3.Exception 처리
             *  Framework Level Exception을 catch하여 임의 가공 처리 할 경우 Warning 객체 정의
             *  Exception 객체 상속구조: Throwable<-Exceltion<-Warning<-FrameworkWarning
             */
            if (AppLog.isWarnEnabled()) {
                AppLog.warn(e.getMessage(), e);
            }
            throw new CgAppUserException("CG_ERROR", 0, e.getMessage(), "SPLT0003", e);
        }
        /**
         * 4.결과 반환
         */
        return result;
    }

    /**
     * <<TITLE>>
     * 포괄보증 연대채무 확약서 조회
     * <<LOGIC>>
     * 1. 포괄보증 연대채무 확약서 조회
     * >(XDA 수행 : com.cg.sa.gu.gurtinclusive.xda.gu_zgu_indv_aplt_dtl_so0004)
     * 2. 결과리턴
     * @param pDoc
     * @return
     * @throws Exception
     */
    public ArrayList<Map> selectIndvApltDtlBzrno(Map pDoc) throws ElException, Exception {
        /**
         * 1.Document 변수의 정의
         *
         * XDA 결과 변수 result
         */
        ArrayList<Map> result = null;
        try {
            /**
             * 2.XDA를 실행합니다.
             * 호출하려는 XDAID를 입력합니다.
             */
            //XDA xda = XDAFactory.getXDA(Constants.KEEP_CONNECTION);
            // 개별대금지급보증 목록조회
            result = comCgSaGuGurtinclusiveGuzguindvapltdtlDAO.gu_zgu_indv_aplt_dtl_so0004(pDoc);
        } catch (ElException e) {
            /**
             * 3.Exception 처리
             *  Framework Level Exception을 catch하여 임의 가공 처리 할 경우 Warning 객체 정의
             *  Exception 객체 상속구조: Throwable<-Exceltion<-Warning<-FrameworkWarning
             */
            if (AppLog.isWarnEnabled()) {
                AppLog.warn(e.getMessage(), e);
            }
            throw new CgAppUserException("CG_ERROR", 0, e.getMessage(), "SPLT0003", e);
        }
        /**
         * 4.결과 반환
         */
        return result;
    }

    /**
     * <<TITLE>>
     * 포괄보증의 보증잔액과 수수료잔액을 조회
     * <<LOGIC>>
     * 1. 포괄보증의 보증잔액과 수수료잔액을 조회
     * >(XDA 수행 : com.cg.sa.gu.gurtinclusive.xda.gu_zgu_indv_aplt_dtl_so0004)
     * 2. 결과리턴
     * @param pDoc
     * @return
     * @throws Exception
     */
    public ArrayList<Map> selectInlvPrmmGurtBaln(Map pDoc) throws ElException, Exception {
        /**
         * 1.Document 변수의 정의
         *
         * XDA 결과 변수 result
         */
        ArrayList<Map> result = null;
        try {
            /**
             * 2.XDA를 실행합니다.
             * 호출하려는 XDAID를 입력합니다.
             */
            //XDA xda = XDAFactory.getXDA(Constants.KEEP_CONNECTION);
            // 포괄보증의 보증잔액과 수수료잔액을 조회
            result = comCgSaGuGurtinclusiveGuzguguasDAO.gu_zgu_guas_so0010(pDoc);
        } catch (ElException e) {
            /**
             * 3.Exception 처리
             *  Framework Level Exception을 catch하여 임의 가공 처리 할 경우 Warning 객체 정의
             *  Exception 객체 상속구조: Throwable<-Exceltion<-Warning<-FrameworkWarning
             */
            if (AppLog.isWarnEnabled()) {
                AppLog.warn(e.getMessage(), e);
            }
            throw new CgAppUserException("CG_ERROR", 0, e.getMessage(), "SPLT0003", e);
        }
        /**
         * 4.결과 반환
         */
        return result;
    }

    /**
     * <<TITLE>>
     * 포괄보증의 보증잔액과 수수료잔액을 수정한다.
     * <<LOGIC>>
     * 1. 포괄보증의 보증잔액과 수수료잔액을 수정한다.
     * 2. 결과리턴
     * @param pDoc
     * @return
     * @throws Exception
     */
    public Map updateInlvPrmmGurtBaln(Map pDoc) throws ElException, Exception {
        /**
         * 1.Document 변수의 정의
         *
         * XDA 결과 변수 result
         */
        Map result = null;
        Map inDoc = null;
        Map outDoc = null;
//        UserSession userSession = null;
        String errCd;
        String gurtStcd = "";
        // 업무승인상태코드 (B1:승인완료, B2:승인취소)
        String bsapStcd = "";
        // 업무승인상태에따른 곱하기 값 (승인취소시에는 반대로 처리해야한다. )
        int stcdAmt = 1;
        try {
            //userSession = (UserSession) ContextUtil.getUserData("userSession") ---> (해당 라인의 소스는 ContextUtil 변환을 지원하지 않습니다. / getUserData);
            //XDA xda = XDAFactory.getXDA(Constants.KEEP_CONNECTION);
            inDoc = new HashMap();
            MapDataUtil.setString(inDoc, "CNRC_MNNO", MapDataUtil.getString(pDoc, "CNRC_MNNO"));
            gurtStcd = MapDataUtil.getString(pDoc, "GURT_STCD");
            bsapStcd = MapDataUtil.getString(pDoc, "BSAP_STCD");
            // 승인취소라면 승인시와 반대로 금액을 처리해줘야한다. (-1)*기존로직
            if (bsapStcd.equals(SAGUConstants.BSAP_STCD_B2)) {
                stcdAmt = -1;
            }
            outDoc = gurtInclusiveSCService.selectInlvPrmmGurtBaln(inDoc);
            AppLog.info("\n updateInlvPrmmGurtBaln SAGUinclusive0019 XML INPUT -----------------------------");
//            AppLog.info("\n" + /* 주석처리(as-is) XMLUtil.serialize(pDoc)*/);
            AppLog.info("\n updateInlvPrmmGurtBaln SAGUinclusive0019 XML OUTPUT -----------------------------");
//            AppLog.info("\n" + /* 주석처리(as-is) XMLUtil.serialize(outDoc)*/);
            // outDoc = XMLUtil.getDocument(outDoc, "vector");
            ArrayList aryList = (ArrayList<Map>) MapDataUtil.getList(outDoc, "result"); //* 수동가이드 예정 (as-is) XMLUtil.toArrayList(outDoc)*/;
            Iterator<Map> itr = aryList.iterator();
            /**
             * 2-2.loop를 돌며 상태값을 조회,관련 Method 실행
             */
            Map listDoc = null;
            while (itr.hasNext()) {
                listDoc = itr.next();
                AppLog.info("\n updateInlvPrmmGurtBaln SAGUinclusive0019 ArrayList XML OUTPUT -----------------------------");
//                AppLog.info("\n" + /* 주석처리(as-is) XMLUtil.serialize(listDoc)*/);
                // 포괄수수료잔액
                long inlvPrmmBaln = MapDataUtil.getLong(listDoc, "INLV_PRMM_BALN");
                // 포괄보증잔액
                long inlvGurtBaln = MapDataUtil.getLong(listDoc, "INLV_GURT_BALN");
                // 수수료
                long prmm = MapDataUtil.getLong(listDoc, "PRMM");
                // 보증금
                long bnamt = MapDataUtil.getLong(listDoc, "BNAMT");
                // 해제정산금액
                long rlseExcaAmt = MapDataUtil.getLong(listDoc, "RLSE_EXCA_AMT");
                // 보증금액(신규설계)
                long newBnamt = MapDataUtil.getLong(listDoc, "NEW_BNAMT");
                // 수수료(신규설계)
                long newPrmm = MapDataUtil.getLong(listDoc, "NEW_PRMM");
                // 해제정산금액(신규설계)
                long newrRlseExcaAmt = MapDataUtil.getLong(listDoc, "NEW_RLSE_EXCA_AMT");
                if (SAGUConstants.GURT_STCD_CNCL.equals(gurtStcd)) {
                    inlvGurtBaln += (stcdAmt) * newBnamt;
                    inlvPrmmBaln += (stcdAmt) * newPrmm;
                } else if (SAGUConstants.GURT_STCD_NEW.equals(gurtStcd)) {
                    if (newBnamt > inlvGurtBaln) {
                        errCd = "E05366";
//                        throw new CgAppUserException("CG_ERROR", 0, CodeUtil.getCodeValue("CGMsgCode", "E", errCd, new String[] { "포괄보증잔액을 " }), errCd, new String[] { "포괄보증잔액 : " + inlvGurtBaln + "원, 개별보증금액 : " + inlvGurtBaln + "원" }, new String[] { "" });
                        throw new CgAppUserException("CG_ERROR", 0, CodeUtil.getCodeValue("CGMsgCode", "E", errCd, new String[] { "포괄보증잔액을 " }), errCd);
                    }
                    if (newPrmm > inlvPrmmBaln) {
                        errCd = "E05366";
//                        throw new CgAppUserException("CG_ERROR", 0, CodeUtil.getCodeValue("CGMsgCode", "E", errCd, new String[] { "포괄수수료잔액을 " }), errCd, new String[] { "포괄수수료잔액 : " + inlvGurtBaln + "원, 개별수수료 : " + inlvGurtBaln + "원" }, new String[] { "" });
                        throw new CgAppUserException("CG_ERROR", 0, CodeUtil.getCodeValue("CGMsgCode", "E", errCd, new String[] { "포괄수수료잔액을 " }), errCd);
                    }
                    inlvGurtBaln -= (stcdAmt) * newBnamt;
                    inlvPrmmBaln -= (stcdAmt) * newPrmm;
                } else if (SAGUConstants.GURT_STCD_RLSE.equals(gurtStcd)) {
                    // 해제인경우 처리 => 해제시에는 잔액을 늘려줘야한다.
                    inlvGurtBaln += (stcdAmt) * rlseExcaAmt;
                    inlvPrmmBaln += (stcdAmt) * prmm;
                } else if (SAGUConstants.GURT_STCD_RLSE_CNCL.equals(gurtStcd)) {
                    if (bnamt > inlvGurtBaln) {
                        errCd = "E05366";
//                        throw new CgAppUserException("CG_ERROR", 0, CodeUtil.getCodeValue("CGMsgCode", "E", errCd, new String[] { "포괄보증잔액을 " }), errCd, new String[] { "포괄보증잔액 : " + inlvGurtBaln + "원, 개별보증금액 : " + inlvGurtBaln + "원" }, new String[] { "" });
                        throw new CgAppUserException("CG_ERROR", 0, CodeUtil.getCodeValue("CGMsgCode", "E", errCd, new String[] { "포괄보증잔액을 " }), errCd);
                    }
                    if (prmm > inlvPrmmBaln) {
                        errCd = "E05366";
//                        throw new CgAppUserException("CG_ERROR", 0, CodeUtil.getCodeValue("CGMsgCode", "E", errCd, new String[] { "포괄수수료잔액을 " }), errCd, new String[] { "포괄수수료잔액 : " + inlvGurtBaln + "원, 개별수수료 : " + inlvGurtBaln + "원" }, new String[] { "" });
                        throw new CgAppUserException("CG_ERROR", 0, CodeUtil.getCodeValue("CGMsgCode", "E", errCd, new String[] { "포괄수수료잔액을 " }), errCd);
                    }
                    inlvGurtBaln -= (stcdAmt) * bnamt;
                    inlvPrmmBaln -= (stcdAmt) * prmm;
                }
                // 포괄보증의 보증잔액과 수수료잔액을 수정한다.
                MapDataUtil.setString(pDoc, "INLV_PRMM_BALN", "" + inlvPrmmBaln);
                MapDataUtil.setString(pDoc, "INLV_GURT_BALN", "" + inlvGurtBaln);
                MapDataUtil.setString(pDoc, "LAST_CHNG_DTTM", (String) UserHeaderUtil.getInstance().getTimestamp());
                MapDataUtil.setString(pDoc, "LAST_CHNR_ID", UserHeaderUtil.getInstance().getEmpno());
                MapDataUtil.setString(pDoc, "PATY_TPCD", MapDataUtil.getString(listDoc, "PATY_TPCD"));
                MapDataUtil.setString(pDoc, "PATY_TYPE_SRNO", MapDataUtil.getString(listDoc, "PATY_TYPE_SRNO"));
                MapDataUtil.setString(pDoc, "CNRC_MNNO", MapDataUtil.getString(listDoc, "CNRC_MNNO"));
                AppLog.info("\n" + "com.cg.sa.gu.gurtinclusive.xda.gu_zgu_cnrc_prty_gurt_aplt_uo0001 XML INPUT -----------------------------");
//                AppLog.info(/* 주석처리(as-is) XMLUtil.serialize(pDoc)*/);
                comCgSaGuGurtinclusiveGuzgucnrcprtygurtapltDAO.gu_zgu_cnrc_prty_gurt_aplt_uo0001(pDoc);
            }
        } catch (ElException e) {
            /**
             * 3.Exception 처리
             *  Framework Level Exception을 catch하여 임의 가공 처리 할 경우 Warning 객체 정의
             *  Exception 객체 상속구조: Throwable<-Exceltion<-Warning<-FrameworkWarning
             */
            if (AppLog.isWarnEnabled()) {
                AppLog.warn(e.getMessage(), e);
            }
            throw new CgAppUserException("CG_ERROR", 0, e.getMessage(), "SPLT0003", e);
        }
        /**
         * 4.결과 반환
         */
        return result;
    }

    /**
     * <<TITLE>>
     * 장기공사차수 포괄보증 조회
     * <<LOGIC>>
     * 1. 장기공사차수 포괄보증 조회
     * >(XDA 수행 : com.cg.sa.gu.gurtinclusive.xda.gu_zgu_guas_so0011)
     * 2. 결과리턴
     * @param pDoc
     * @return
     * @throws Exception
     */
    public ArrayList<Map> selectLntrCntcWrksOrseq(Map pDoc) throws ElException, Exception {
        /**
         * 1.Document 변수의 정의
         *
         * XDA 결과 변수 result
         */
        ArrayList<Map> result = null;
        try {
            /**
             * 2.XDA를 실행합니다.
             * 호출하려는 XDAID를 입력합니다.
             */
            //XDA xda = XDAFactory.getXDA(Constants.KEEP_CONNECTION);
            // 장기공사차수 포괄보증 조회
            result = comCgSaGuGurtinclusiveGuzguguasDAO.gu_zgu_guas_so0011(pDoc);
        } catch (ElException e) {
            /**
             * 3.Exception 처리
             *  Framework Level Exception을 catch하여 임의 가공 처리 할 경우 Warning 객체 정의
             *  Exception 객체 상속구조: Throwable<-Exceltion<-Warning<-FrameworkWarning
             */
            if (AppLog.isWarnEnabled()) {
                AppLog.warn(e.getMessage(), e);
            }
            throw new CgAppUserException("CG_ERROR", 0, e.getMessage(), "SPLT0003", e);
        }
        /**
         * 4.결과 반환
         */
        return result;
    }

    /**
     * <<TITLE>>
     * 공사이행보증 발급 유무 조회
     * <<LOGIC>>
     * 1. 공사이행보증 발급 유무 조회
     * >(XDA 수행 : com.cg.sa.gu.gurtinclusive.xda.gu_zgu_guas_so0012)
     * 2. 결과리턴
     * @param pDoc
     * @return
     * @throws Exception
     */
    public Map selectPfbnIssuXn(Map pDoc) throws ElException, Exception {
        /**
         * 1.Document 변수의 정의
         *
         * XDA 결과 변수 result
         */
        Map result = null;
        try {
            /**
             * 2.XDA를 실행합니다.
             * 호출하려는 XDAID를 입력합니다.
             */
            //XDA xda = XDAFactory.getXDA(Constants.KEEP_CONNECTION);
            // 장기공사차수 포괄보증 조회
            result = comCgSaGuGurtinclusiveGuzguguasDAO.gu_zgu_guas_so0012(pDoc);
        } catch (ElException e) {
            /**
             * 3.Exception 처리
             *  Framework Level Exception을 catch하여 임의 가공 처리 할 경우 Warning 객체 정의
             *  Exception 객체 상속구조: Throwable<-Exceltion<-Warning<-FrameworkWarning
             */
            if (AppLog.isWarnEnabled()) {
                AppLog.warn(e.getMessage(), e);
            }
            throw new CgAppUserException("CG_ERROR", 0, e.getMessage(), "SPLT0003", e);
        }
        /**
         * 4.결과 반환
         */
        return result;
    }

    /**
     * <<TITLE>>
     * 기발급보증서정보 조회
     * <<LOGIC>>
     * 1. 기발급보증서정보 조회
     * >(XDA 수행 : com.cg.sa.gu.gurtinclusive.xda.gu_zgu_indv_aplt_dtl_so0006)
     * 2. 결과리턴
     * @param pDoc
     * @return
     * @throws Exception
     */
    public ArrayList<Map> selectPrisGuasInfm(Map pDoc) throws ElException, Exception {
        /**
         * 1.Document 변수의 정의
         *
         * XDA 결과 변수 result
         */
        ArrayList<Map> result = null;
        try {
            /**
             * 2.XDA를 실행합니다.
             * 호출하려는 XDAID를 입력합니다.
             */
            //XDA xda = XDAFactory.getXDA(Constants.KEEP_CONNECTION);
            // 기발급보증서정보 조회
            result = comCgSaGuGurtinclusiveGuzguindvapltdtlDAO.gu_zgu_indv_aplt_dtl_so0006(pDoc);
        } catch (ElException e) {
            /**
             * 3.Exception 처리
             *  Framework Level Exception을 catch하여 임의 가공 처리 할 경우 Warning 객체 정의
             *  Exception 객체 상속구조: Throwable<-Exceltion<-Warning<-FrameworkWarning
             */
            if (AppLog.isWarnEnabled()) {
                AppLog.warn(e.getMessage(), e);
            }
            throw new CgAppUserException("CG_ERROR", 0, e.getMessage(), "SPLT0003", e);
        }
        /**
         * 4.결과 반환
         */
        return result;
    }

    /**
     * <<TITLE>>
     * 전문전송
     * <<LOGIC>>
     * 1. 전문전송
     * >(XDA 수행 : com.cg.sa.gu.gurtinclusive.xda.gu_zgu_indv_aplt_dtl_so0006)
     * 2. 결과리턴
     * @param pDoc
     * @return
     * @throws Exception
     */
    public Map processPrisGuasInfm(Map pDoc) throws ElException, Exception {
        Map result = null;
        // 기발급
        String pris = "";
        // 데이터불일치
        String dataDscr = "";
        // 잔액부족
        String unisBnamtRsnCrsp = "";
        // 기간초과
        String gurtProdEnda = "";
        // 기타사항
        String unisEtcRsnCrsp = "";
        String code = "";
        ArrayList<Map> vecDocument = new ArrayList();
        String currTimestamp = com.inswave.ext.cg.util.DateUtil.getTimestamp();
        String currDate = currTimestamp.substring(0, 14);
        // 기발급
        String prisYn = MapDataUtil.getString(pDoc, "PRIS_YN");
        // 데이터불일치
        String dataDscrYn = MapDataUtil.getString(pDoc, "DATA_DSCR_YN");
        // 잔액부족
        String unisBnamtRsnCrspYn = MapDataUtil.getString(pDoc, "UNIS_BNAMT_RSN_CRSP_YN");
        // 기간초과
        String gurtProdEndaYn = MapDataUtil.getString(pDoc, "GURT_PROD_ENDA_YN");
        // 기타사항
        String unisEtcRsnCrspYn = MapDataUtil.getString(pDoc, "UNIS_ETC_RSN_CRSP_YN");
        if ("Y".equals(prisYn)) {
            code = code + "30|";
        }
        if ("Y".equals(dataDscrYn)) {
            code = code + "40|";
        }
        if ("Y".equals(unisBnamtRsnCrspYn)) {
            code = code + "50|";
        }
        if ("Y".equals(gurtProdEndaYn)) {
            code = code + "51|";
        }
        if ("Y".equals(unisEtcRsnCrspYn)) {
            code = code + "99";
        }
        AppLog.info("<<<<<<<<<<<<<<<<" + code);
        StringTokenizer arr = new StringTokenizer(code, "|");
        while (arr.hasMoreTokens()) {
            Map detailsDoc = new HashMap();
            // 업무처리결과코드
            MapDataUtil.setString(detailsDoc, "Biz_Result_Code", arr.nextToken());
            // 업무처리결과비고
            MapDataUtil.setString(detailsDoc, "Biz_Result_Bigo", "");
            //vecDocument.addElement(detailsDoc);
            vecDocument.add(detailsDoc);
        }
        //MapDataUtil.setVector(pDoc, "Response_Details", vecDocument);
        MapDataUtil.setList(pDoc, "Response_Details", vecDocument);
        // 전송일시
        MapDataUtil.setString(pDoc, "Send_DateTime", currDate);
        AppLog.info("===========================================================" +  ("") /* 주석처리(as-is) XMLUtil.indent(pDoc)*/);
        return result;
    }

    /**
     * <<TITLE>>
     * 개별확정대여금액합계 조회한다.
     * <<LOGIC>>
     * 1. 개별확정대여금액합계 조회한다.
     * >(XDA 수행 : com.cg.sa.gu.gurtinclusive.xda.gu_zgu_guas_so0003)
     * 2. 결과리턴
     * @param pDoc
     * @return
     * @throws Exception
     */
    public Map selectInlvCnttAmt(Map pDoc) throws ElException, Exception {
        /**
         * 1.Document 변수의 정의
         *
         * XDA 결과 변수 result
         */
        Map result = null;
        try {
            /**
             * 2.XDA를 실행합니다.
             * 호출하려는 XDAID를 입력합니다.
             */
            //XDA xda = XDAFactory.getXDA(Constants.KEEP_CONNECTION);
            // 개별확정대여금액합계 조회
            result = comCgSaGuGurtinclusiveGuzgustecnmcindvcnrcDAO.gu_zgu_ste_cnmc_indv_cnrc_so0001(pDoc);
        } catch (ElException e) {
            /**
             * 3.Exception 처리
             *  Framework Level Exception을 catch하여 임의 가공 처리 할 경우 Warning 객체 정의
             *  Exception 객체 상속구조: Throwable<-Exceltion<-Warning<-FrameworkWarning
             */
            if (AppLog.isWarnEnabled()) {
                AppLog.warn(e.getMessage(), e);
            }
            throw new CgAppUserException("CG_ERROR", 0, e.getMessage(), "SPLT0003", e);
        }
        /**
         * 4.결과 반환
         */
        return result;
    }

    @Resource(name = "comCgSaGuGurtinclusiveGuzguguasDAO")
    private com.cg.sa.gu.gurtinclusive.dao.ComCgSaGuGurtinclusiveGuzguguasDAO comCgSaGuGurtinclusiveGuzguguasDAO;

    @Resource(name = "comCgSaGuGurtinclusiveGuzsminlvsbcnsbcmlogDAO")
    private com.cg.sa.gu.gurtinclusive.dao.ComCgSaGuGurtinclusiveGuzsminlvsbcnsbcmlogDAO comCgSaGuGurtinclusiveGuzsminlvsbcnsbcmlogDAO;

    @Resource(name = "comCgSaGuGurtinclusiveGuzsmkisconptcpinfmaddlogDAO")
    private com.cg.sa.gu.gurtinclusive.dao.ComCgSaGuGurtinclusiveGuzsmkisconptcpinfmaddlogDAO comCgSaGuGurtinclusiveGuzsmkisconptcpinfmaddlogDAO;

    @Resource(name = "comCgSaGuGurtinclusiveGuzguindvapltdtlDAO")
    private com.cg.sa.gu.gurtinclusive.dao.ComCgSaGuGurtinclusiveGuzguindvapltdtlDAO comCgSaGuGurtinclusiveGuzguindvapltdtlDAO;

    @Resource(name = "atmnNoticeSCServiceImpl")
    private com.cg.bs.co.automationnotice.service.AtmnNoticeSCService atmnNoticeSCService;

    @Resource(name = "comCgSaGuGurtinclusiveGuzcupartyDAO")
    private com.cg.sa.gu.gurtinclusive.dao.ComCgSaGuGurtinclusiveGuzcupartyDAO comCgSaGuGurtinclusiveGuzcupartyDAO;

    @Resource(name = "custMgmtSCServiceImpl")
    private com.cg.cu.cb.customermgmt.service.CustMgmtSCService custMgmtSCService;

    @Resource(name = "comCgCuCbCustomermgmtCbzcuprtyrltnDAO")
    private com.cg.cu.cb.customermgmt.dao.ComCgCuCbCustomermgmtCbzcuprtyrltnDAO comCgCuCbCustomermgmtCbzcuprtyrltnDAO;

    @Resource(name = "comCgCuCbCustomermgmtCbzcuprtyrltnsrnomngmDAO")
    private com.cg.cu.cb.customermgmt.dao.ComCgCuCbCustomermgmtCbzcuprtyrltnsrnomngmDAO comCgCuCbCustomermgmtCbzcuprtyrltnsrnomngmDAO;

    @Resource(name = "comCgCuCbCustomermgmtCbzcuprtyrltnlDAO")
    private com.cg.cu.cb.customermgmt.dao.ComCgCuCbCustomermgmtCbzcuprtyrltnlDAO comCgCuCbCustomermgmtCbzcuprtyrltnlDAO;

    @Resource(name = "gurtCommonSCServiceImpl")
    private com.cg.sa.gu.gurtcommon.service.GurtCommonSCService gurtCommonSCService;

    @Resource(name = "comCgSaGuGurtinclusiveGuzgucnrcprtygurtapltDAO")
    private com.cg.sa.gu.gurtinclusive.dao.ComCgSaGuGurtinclusiveGuzgucnrcprtygurtapltDAO comCgSaGuGurtinclusiveGuzgucnrcprtygurtapltDAO;

    @Resource(name = "comCgSaGuGurtinclusiveGuzguguashDAO")
    private com.cg.sa.gu.gurtinclusive.dao.ComCgSaGuGurtinclusiveGuzguguashDAO comCgSaGuGurtinclusiveGuzguguashDAO;

    @Resource(name = "comCgSaGuGurtinclusiveGuzagagrmindvafshDAO")
    private com.cg.sa.gu.gurtinclusive.dao.ComCgSaGuGurtinclusiveGuzagagrmindvafshDAO comCgSaGuGurtinclusiveGuzagagrmindvafshDAO;

    @Resource(name = "comCgSaGuGurtinclusiveGuzcucnplDAO")
    private com.cg.sa.gu.gurtinclusive.dao.ComCgSaGuGurtinclusiveGuzcucnplDAO comCgSaGuGurtinclusiveGuzcucnplDAO;

    @Resource(name = "comCgSaGuGurtinclusiveGuzhrorgzDAO")
    private com.cg.sa.gu.gurtinclusive.dao.ComCgSaGuGurtinclusiveGuzhrorgzDAO comCgSaGuGurtinclusiveGuzhrorgzDAO;

    @Resource(name = "gurtInclusiveSCServiceImpl")
    private com.cg.sa.gu.gurtinclusive.service.GurtInclusiveSCService gurtInclusiveSCService;

    @Resource(name = "comCgSaGuGurtinclusiveGuzgustecnmcindvcnrcDAO")
    private com.cg.sa.gu.gurtinclusive.dao.ComCgSaGuGurtinclusiveGuzgustecnmcindvcnrcDAO comCgSaGuGurtinclusiveGuzgustecnmcindvcnrcDAO;
}