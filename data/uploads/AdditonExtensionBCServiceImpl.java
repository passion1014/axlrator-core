/**
 * Copyright (c) 2010 CG. All rights reserved.
 *
 * This software is the confidential and proprietary information of CG. You
 * shall not disclose such Confidential Information and shall use it only in
 * accordance with the terms of the license agreement you entered into with CG.
 */
package com.cg.sa.ag.additonextensionmgmt.service.impl;

/**
 * 업무 그룹명	: com.cg.sa.ag.additonextensionmgmt.bc
 * 서브 업무명	: AdditonExtensionBC.java
 * 작성자	: 김성훈
 * 작성일	: 2010. 06. 15
 * 설 명    : 연대보증인 추가입보/동의서 관리를 위한 비즈니스 클래스이다.
 */
import java.util.ArrayList;
import java.util.HashMap;
import java.util.Iterator;
import java.util.List;
import java.util.Map;

import javax.annotation.Resource;

import org.springframework.stereotype.Service;
import org.springframework.util.ObjectUtils;

import com.cg.custom.cmmn.exception.CgAppUserException;
import com.cg.custom.cmmn.fw.util.DateUtil;
import com.cg.custom.cmmn.util.MapDataUtil;
import com.cg.custom.cmmn.util.UserHeaderUtil;
import com.cg.sa.ag.additonextensionmgmt.service.AdditonExtensionBCService;
import com.cg.sa.ag.common.SAAGConstants;
import com.cg.sa.gu.common.GUUtil;
import com.cg.sa.gu.common.SAGUConstants;
import com.inswave.elfw.exception.ElException;
import com.inswave.elfw.log.AppLog;
import com.inswave.ext.cg.util.CodeUtil;

/**
 * 연대보증인 추가입보/동의서 관리를 위한 비즈니스 클래스이다.
 */
@SuppressWarnings({ "rawtypes", "unchecked" })
@Service("additonExtensionBCServiceImpl")
public class AdditonExtensionBCServiceImpl implements AdditonExtensionBCService {

    /**
     * <<TITLE>>
     * 연대보증인 추가입보 및 동의서 업무승인 [최종승인] 처리를 한다.
     * <<LOGIC>>
     * 1. 추가입보연장동의 정보를 조회한다.
     * 1.1 추가입보연장동의등록 테이블을 조회한다.
     * > com.cg.sa.ag.additonextensionmgmt.bc.AdditonExtensionTblBC.selectZagAdGvsrExAgrnAplt
     * 1.2 추가입보연장동의대상보증서 테이블을 조회한다.
     * > com.cg.sa.ag.additonextensionmgmt.bc.AdditonExtensionTblBC.selectZagAdGvsrExAgrnApGaus
     * 1.3 추가입보연장동의연대보증인 테이블을 조회한다.
     * > com.cg.sa.ag.additonextensionmgmt.bc.AdditonExtensionTblBC.selectZagAdGvsrExAgrnApJnsrAll
     * 2. 연대보증인 수만큼 약정관련인테이블과 추가입보연장동의보증서 정보를 생성한다.
     * > LOOP(i <= size(추가입보동의한연대보증인수)) {
     * > 2.1 약정관련인테이블 정보를 생성한다.
     * > com.cg.sa.ag.additonextensionmgmt.bc.AdditonExtensionTblBC.insertZagAgrmRlpr
     * > 2.2 추가입보연장동의대상보증서 정보를 조회하여 추가입보연장동의보증서 정보 생성한다.
     * > com.cg.sa.ag.additonextensionmgmt.bc.AdditonExtensionTblBC.insertZagAdGvsrExAgrnGaus
     * > }
     * 3. 추가입보연장동의등록 테이블을 수정한다.(추가입보연장동의상태코드 := 처리완료)
     * > com.cg.sa.ag.additonextensionmgmt.bc.AdditonExtensionTblBC.updateZagAdGvsrExAgrnAplt
     * 4. 결과리턴
     * @param pDoc
     * @return
     * @throws Exception
     */
    public Map admitAdditionExtension(Map pDoc) throws ElException, Exception {
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
            //result = xda.execute("[ XDAID를 입력합니다]", pDoc);
        } catch (ElException e) {
        	AppLog.warn(e.getMessage(), e);
            /**
             * 3.Exception 처리
             *  Framework Level Exception을 catch하여 임의 가공 처리 할 경우 Warning 객체 정의
             *  Exception 객체 상속구조: Throwable<-Exceltion<-Warning<-FrameworkWarning
             */
            throw new CgAppUserException("CG_ERROR", 0, e.getMessage(), CodeUtil.getCodeValue("[코드항목]", "[코드카테고리]", "[에러코드번호]"), e);
        }
        /**
         * 4.결과 반환
         */
        return result;
    }

    /**
     * <<TITLE>>
     * 연대보증인 추가입보 및 동의서 업무승인 [업무승인요청][승인][기각][반려] 결재중 처리를 한다.
     * <<LOGIC>>
     * 1. 추가입보연장동의등록 테이블 조회한다.
     * >com.cg.sa.ag.additonextensionmgmt.bc.AdditonExtensionTblBC.selectZagAdGvsrExAgrnAplt
     * 2. 업무의뢰번호, 약정상태코드 등을 변경처리한다.
     * IF (업무승인상태코드 == 업무승인요청){추가입보연장동의상태코드:=승인, 업무의뢰번호 :=  }
     * ELSE IF (업무승인상태코드 == 승인) {추가입보연장동의상태코드 := 승인}
     * ELSE IF (업무승인상태코드 == 기각) {추가입보연장동의상태코드 := 기각}
     * ELSE IF (업무승인상태코드 == 반려) {추가입보연장동의상태코드 := 반려}
     * 3. 추가입보연장동의등록 테이블수정(UPDATE)한다.
     * >com.cg.sa.ag.additonextensionmgmt.bc.AdditonExtensionTblBC.updateZagAdGvsrExAgrnAplt
     * 4. 결과리턴
     * @param pDoc
     * @return
     * @throws Exception
     */
    public Map approveAdditionExtension(Map pDoc) throws ElException, Exception {
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
            //result = xda.execute("[ XDAID를 입력합니다]", pDoc);
        } catch (ElException e) {
        	AppLog.warn(e.getMessage(), e);
            /**
             * 3.Exception 처리
             *  Framework Level Exception을 catch하여 임의 가공 처리 할 경우 Warning 객체 정의
             *  Exception 객체 상속구조: Throwable<-Exceltion<-Warning<-FrameworkWarning
             */
            throw new CgAppUserException("CG_ERROR", 0, e.getMessage(), CodeUtil.getCodeValue("[코드항목]", "[코드카테고리]", "[에러코드번호]"), e);
        }
        /**
         * 4.결과 반환
         */
        return result;
    }

    /**
     * <<TITLE>>
     * 연대보증인 추가입보서 신청내용을 조회 한다.
     * <<LOGIC>>
     * 1. 약정번호와 보증서번호로 연대보증인 추가입보 신청내용을 조회한다.
     * >com.cg.sa.ag.additonextensionmgmt.bc.AdditonExtensionTblBC.selectZagAdGvsrExAgrnAplt
     * 2. 신청내용이 있는경우
     * 2.1. 추가입보연장동의방법이 개별인 경우 추가입보 연장동의 대상보증서 정보를 조회한다.
     * > IF (추가입보연장동의방법코드 == 개별) {
     * >com.cg.sa.ag.additonextensionmgmt.bc.AdditonExtensionTblBC.selectZagAdGvsrExAgrnApGaus
     * > }
     * 2.2. 추가입보 연장동의 연대보증인 정보를 조회한다.
     * >com.cg.sa.ag.additonextensionmgmt.bc.AdditonExtensionTblBC.selectZagAdGvsrExAgrnApJnsrAll
     * 3. 신청내용이 없는경우 해당 약정정보와 보증서정보를 조회한다.
     * 3.1 약정상세정보를 조회한다.
     * > com.cg.sa.ag.agreementinfomgmt.Iagreementinfomgmt.selectAgreementDtlbyPK
     * 3.2 추가입보연장동의방법이 개별인 경우 보증서정보를 조회한다.
     * > IF (추가입보연장동의방법코드 == 개별) {
     * > com.cg.sa.gu.guasinfminqr.Iguasinfminqr.selectGuaranteeSheetbyPK
     * > }
     * 3.3 현재 유효한 한도약정의 연대보증인을 조회한다.
     * > 1) 현재 유효한 한도약정의 약정관리번호를 조회한다.
     * >   (xda ???? : ag_zag_agmt_so1303)
     * > 2) 약정상세정보를 조회한다.
     * >  com.cg.sa.ag.agreementinfomgmt.Iagreementinfomgmt.selectAgreementDtlbyPK
     * 4. 결과리턴
     * @param pDoc
     * @return
     * @throws Exception
     */
    public Map selectAdditonGivingSuretybyPK_OLD(Map pDoc) throws ElException, Exception {
        /**
         * 1.Document 변수의 정의
         *
         * XDA 결과 변수 result
         */
        Map result = new HashMap();
        Map docRequest = new HashMap();
        Map docGuas = new HashMap();
        Map docAgmt = new HashMap();
        Map docOrignSurety = new HashMap();
        Map docOrignSuretyTwo = new HashMap();
        Map docAddSurety = new HashMap();
        Map listDoc = null;
        AppLog.info("\n== AdditonExtensionBC.selectAdditonGivingSuretybyPK start =======================");
        AppLog.info("\n== pDoc =======================");
        // Logger.info("\n" + XMLUtil.indent(pDoc));
        try {
            //XDA xda = XDAFactory.getXDA(Constants.KEEP_CONNECTION);
            AppLog.info("************************************");
            AppLog.info("1.고객정보 조회");
            AppLog.info("************************************");
            docRequest = new HashMap();
            MapDataUtil.setString(docRequest, "CUST_INQR_DSCD", "IA01");
            MapDataUtil.setString(docRequest, "CUST_INQR_COND_DSCD", MapDataUtil.getString(pDoc, "CUST_INQR_COND_DSCD"));
            MapDataUtil.setString(docRequest, "SRCH_KWRD", MapDataUtil.getString(pDoc, "AMNO"));
            /*
			Logger.info("********************************************");
			Logger.info("CUCBcustomermgmt0025 docRequest");
			Logger.info("********************************************");			
			Logger.info(docRequest);
			Logger.info("********************************************");
			*/
            result = MapDataUtil.getMap(custMgmtSCService.selectCustInfo(docRequest), "PRTY_BASC");
            AppLog.info("********************************************");
            AppLog.info("CUCBcustomermgmt0025 result");
            AppLog.info("********************************************");
            AppLog.info("" + result);
            AppLog.info("********************************************");
            if (MapDataUtil.getString(pDoc, "AMNO") == "") {
                String[] saveStatus = new String[] { "조합원번호" };
                // {0}이(가) 존재하지 않습니다.
                throw new CgAppUserException("CG_ERROR", 0, CodeUtil.getCodeValue("CGMsgCode", "I", "I03000", saveStatus), "I03000");
            }
            // 고객정보 /RSOA_LIST값을 가져온다.
            Map custResult = null;
            custResult = new HashMap();
            // 추가연대보증인
//            MapDataUtil.setVector(custResult, "RPL", /* 수동가이드 예정 (as-is) XMLUtil.getVectorDOM(result, "RSOA_LIST")*/);
            custResult.put("RPL", result.get("RSOA_LIST"));
            
            AppLog.info("**************************************");
            AppLog.info("[고객관련인정보]...custResult");
            AppLog.info("**************************************");
            // Logger.info(custResult);
            AppLog.info("**************************************");
            // XMLUtil.setString(pDoc, "CUNO", XMLUtil.getString(pDoc, "CUNO"));
            result = new HashMap();
            AppLog.info("추가입보방법 1.개별(보증서번호),2.일괄 ADDT_GVSR_EXTN_AGRN_MTCD[" + MapDataUtil.getString(pDoc, "ADDT_GVSR_EXTN_AGRN_MTCD") + "]");
            // 기약정조회시 존재시 계약관리번호 세팅.
            String lZagAddtExtnAgrmMnno = "";
            // 추가입보방법 : 개별(1)
            // if (XMLUtil.getString(pDoc, "ADDT_GVSR_EXTN_AGRN_MTCD").equals("1")) {
            if (MapDataUtil.getString(pDoc, "ADDT_GVSR_EXTN_AGRN_MTCD").equals(SAAGConstants.ADDT_GVSR_EXTN_AGRN_MTCD_1)) {
                AppLog.info("**************************************");
                AppLog.info("[개별]추가입보방법	개별 (보증서번호) 입니다.");
                AppLog.info("**************************************");
                AppLog.info("//////////////////////////////////////////////////");
                AppLog.info("// 당초보증정보 조회 (문언니)");
                AppLog.info("//////////////////////////////////////////////////");
                docRequest = new HashMap();
                // 계약관리번호
                MapDataUtil.setString(docRequest, "CNRC_MNNO", MapDataUtil.getString(pDoc, "CNRC_MNNO"));
                docGuas = guasInfmInqrSCService.selectGuaranteeSheetbyPK(docRequest);
                AppLog.info("\n== docGuas request =======================");
                // Logger.info("\n" + XMLUtil.indent(docRequest));
                AppLog.info("\n== docGuas =======================");
                // Logger.info("\n" + XMLUtil.indent(docGuas));
                AppLog.info("*************************************************");
                AppLog.info("***	[개별]보증서의 약정관리번호	[" + MapDataUtil.getString(docGuas, "AGRM_MNNO") + "]		**************");
                AppLog.info("*************************************************");
                // 약정관리번호
                MapDataUtil.setString(pDoc, "AGRM_MNNO", MapDataUtil.getString(docGuas, "AGRM_MNNO"));
                // 개별일때 기약정조회 .. 보증서(계약관리번호)로 등록된 내용이 있고, 변경일련번호가 없으면  등록된 자료 조회. START
                Map getZagAddtExtn = additonExtensionTblBCService.selectZagAdGvsrExAgrnApGaus(docGuas);
                // ag_zag_addt_extn_so3036
                AppLog.info("***********************************");
                AppLog.info("getZagAddtExtn");
                AppLog.info("***********************************");
                AppLog.info("" + getZagAddtExtn);
                AppLog.info("***********************************");
                int resultOneInt = Integer.parseInt(MapDataUtil.getAttribute(getZagAddtExtn, "result"));
                if (resultOneInt > 0) {
                    AppLog.info("***********************************");
                    AppLog.info("[개별]기등록된 추가입보연장동의 테이블이 존재합니다.");
                    AppLog.info("***********************************");
                    // 추가입보일자 	: ADDT_GVSR_EXTN_AGRN_DATE(추가입보연장동의일자)
                    MapDataUtil.setString(docGuas, "ADDT_GVSR_EXTN_AGRN_DATE", MapDataUtil.getString(getZagAddtExtn, "ADDT_GVSR_EXTN_AGRN_DATE"));
                    // [현재 테이블이 없음..]추가입보사유 	: ADDT_GVSR_RSN_CNTS(현재없음.)
                    MapDataUtil.setString(docGuas, "ADDT_GVSR_RSN_CNTS", MapDataUtil.getString(getZagAddtExtn, "ADDT_GVSR_RSN_CNTS"));
                    // 연장보증기한 	: EXTN_GURT_DLNN_DATE(연장보증기한일자)
                    MapDataUtil.setString(docGuas, "EXTN_GURT_DLNN_DATE", MapDataUtil.getString(getZagAddtExtn, "EXTN_GURT_DLNN_DATE"));
                    // ========================================================================
                    lZagAddtExtnAgrmMnno = MapDataUtil.getString(getZagAddtExtn, "AGRM_MNNO");
                    MapDataUtil.setString(docGuas, "NEW_AGRM_MNNO", lZagAddtExtnAgrmMnno);
                } else {
                    AppLog.info("[개별]기등록된 추가입보연장동의 테이블이 존재하지 않습니다.");
                }
                /*
				Logger.info("***********************************");
				Logger.info("docGuas");
				Logger.info("***********************************");
				Logger.info(docGuas);
				Logger.info("***********************************");
				*/
                // 개별일때 기약정조회 .. 보증서(계약관리번호)로 등록된 내용이 있고, 변경일련번호가 없으면  등록된 자료 조회. END
                AppLog.info("//////////////////////////////////////////////////");
                AppLog.info("// [개별]당초연대보증인정보 조회 (Change)");
                AppLog.info("//////////////////////////////////////////////////");
                docRequest = new HashMap();
                // 계약관리번호
                MapDataUtil.setString(docRequest, "CNRC_MNNO", MapDataUtil.getString(pDoc, "CNRC_MNNO"));
                // 500:개인연대보증인, 600:법인연대채무자
                MapDataUtil.setString(docRequest, "PATY_TPCD", "500");
                docOrignSurety = gurtPartyMgmtSCService.selectGurtParty(docRequest);
                // Logger.info("\n== docOrignSurety 1 =======================");
                // Logger.info("\n" + XMLUtil.indent(docOrignSurety));
                // 500:개인연대보증인, 600:법인연대채무자
                MapDataUtil.setString(docRequest, "PATY_TPCD", "600");
                docOrignSuretyTwo = gurtPartyMgmtSCService.selectGurtParty(docRequest);
                // Logger.info("\n== docOrignSurety 2 =======================");
                // Logger.info("\n" + XMLUtil.indent(docOrignSuretyTwo));
                List aryList 	= (List)docOrignSurety.get(GUUtil.ATTRIBUTE_RESULT);
                List aryListTwo	= (List)docOrignSuretyTwo.get(GUUtil.ATTRIBUTE_RESULT);
                // 500:개인연대보증인, 600:법인연대채무자으로 모두 데이터가 있을 경우 하나의 Vector로 합침.
                if (aryList.size() > 0) {
                    if (aryListTwo.size() > 0) {
                        Iterator<Map> itr = aryListTwo.iterator();
                        while (itr.hasNext()) {
                            listDoc = itr.next();
                            aryList.add(listDoc);
                        }
                    }
                } else {
                	aryList = aryListTwo;
                }
                // Logger.info("\n== docOrignSurety =======================");
                // Logger.info("\n" + XMLUtil.indent(docOrignSurety));
                // 당초보증정보
                result.putAll(docGuas);
                // 당초연대보증인정보
                result.put("LIST", docOrignSurety);
                AppLog.info("//////////////////////////////////////////////////");
                AppLog.info("// [개별]약정상세 : 당초약정정보 + 추가연대보증인 조회");
                AppLog.info("//////////////////////////////////////////////////");
                docRequest = new HashMap();
                // 약정관리번호
                MapDataUtil.setString(docRequest, "AGRM_MNNO", MapDataUtil.getString(pDoc, "AGRM_MNNO"));
                // 당초 약정관리번호
                MapDataUtil.setString(docRequest, "CHYN_AGRM_MNNO", MapDataUtil.getString(pDoc, "AGRM_MNNO"));
                // 약정관련자구분코드
                MapDataUtil.setString(docRequest, "CHYN_AGRM_RLPR_DSCD", "20");
                docAgmt = agreementInfoMgmtSCService.selectAgreementDtlbyPK(docRequest);
                // Logger.info("\n== 입력된 값 docRequest 1 =======================");
                // Logger.info("\n" + XMLUtil.indent(docRequest));
                // Logger.info("\n== 약정상세. 약정관련인 docAgmt 1 =======================");
                // Logger.info("\n" + XMLUtil.indent(docAgmt));
            }
            // 추가입보방법 : 일괄(2)
            // if (XMLUtil.getString(pDoc, "ADDT_GVSR_EXTN_AGRN_MTCD").equals("2")) {
            if (MapDataUtil.getString(pDoc, "ADDT_GVSR_EXTN_AGRN_MTCD").equals(SAAGConstants.ADDT_GVSR_EXTN_AGRN_MTCD_2)) {
                // 기등록건 조회 .
                AppLog.info("[일괄]추가입보방법 : 일괄(2)	기등록건 조회 .");
                docAgmt = additonExtensionTblBCService.selectZagAdGvsrExAgrnApJnsrAll(pDoc);
                List<Map> rplOutput = additonExtensionTblBCService.selectZagAgrmRlpr(pDoc);
                // com.cg.sa.ag.additonextensionmgmt.xda.ag_zag_agrm_rlpt_so3038 SAAG --> SAGU
                // 당초연대보증인정보
                result.put("LIST", rplOutput);
                // 추가연대보증인 원본(추가입보연장동의테이블)
                docAgmt.put("RPL", rplOutput);
                
                // if(XMLUtil.getAttribute(docAgmt, "result").equals("1")){
                if (MapDataUtil.getAttribute(docAgmt, "result").equals(SAAGConstants.RESULT_1)) {
                    AppLog.info("[일괄]기등록건이 존재합니다. ");
                } else {
                    AppLog.info("[일괄]기등록건이 존재하지 않습니다. ");
                    AppLog.info("//////////////////////////////////////////////////");
                    AppLog.info("// [일괄]약정상세 : 당초약정정보 + 추가연대보증인 조회");
                    AppLog.info("//////////////////////////////////////////////////");
                    docRequest = new HashMap();
                    // 약정관리번호
                    MapDataUtil.setString(docRequest, "AGRM_MNNO", MapDataUtil.getString(pDoc, "AGRM_MNNO"));
                    // 당초 약정관리번호
                    MapDataUtil.setString(docRequest, "CHYN_AGRM_MNNO", MapDataUtil.getString(pDoc, "AGRM_MNNO"));
                    // 약정관련자구분코드
                    MapDataUtil.setString(docRequest, "CHYN_AGRM_RLPR_DSCD", "20");
                    // docAgmt = BSEUtil.executeService(docRequest, "SAAGagreementinfo0201");
                    // 
                    // com.cg.sa.ag.agreementinfomgmt.xda.ag_zag_agmt_so1504
                    // com.cg.sa.ag.additonextensionmgmt.xda.ag_zag_agmt_so1504
                    // com.cg.sa.ag.agreementinfomgmt.xda.ag_zag_agrm_rlpr_so1507
                    // 당초약정정보
                    docAgmt = comCgSaAgAdditonextensionmgmtAgzagagmtDAO.ag_zag_agmt_so1504(docRequest);
                    // 당초연대보증인
                    ArrayList<Map> rplOutListSAGU = comCgSaAgAdditonextensionmgmtAgzagagrmrlprDAO.ag_zag_agrm_rlpr_so1508(docRequest);
                    // 당초연대보증인정보
                    result.put("LIST", rplOutListSAGU);
                    ArrayList<Map> rplOut = comCgSaAgAdditonextensionmgmtAgzagagrmrlprDAO.ag_zag_agrm_rlpr_so1507(docRequest);
                    // 추가연대보증인 원본 (약정원장정보)
                    docAgmt.put("RPL", rplOut);
                    AppLog.info("\n== 입력된 값 docRequest 1 =======================");
                    AppLog.info("\n" + docRequest);
                    AppLog.info("\n== 고객조회 . 약정관련인 docAgmt 1 =======================");
                    AppLog.info("\n" + docAgmt);
                }
                // 추가연대보증인
                result.put("LIST1", docAgmt.get("RPL"));
            }
            // 당초약정정보
            result.putAll(docAgmt);
            AppLog.info("**********************************");
            AppLog.info("3.END 당초연대보증인 .. result");
            AppLog.info("**********************************");
            AppLog.info("" + result);
            AppLog.info("**********************************");
            AppLog.info("//////////////////////////////////////////////////");
            AppLog.info("// 추가연대보증인");
            AppLog.info("//////////////////////////////////////////////////");
            /*				
			// 추가입보방법 : 개별(1)
			if (XMLUtil.getString(pDoc, "ADDT_GVSR_EXTN_AGRN_MTCD").equals("1")) {
				Logger.info("추가입보방법 : 개별(1)");
			
			// 추가입보방법 : 일괄(2)
			}else if (XMLUtil.getString(pDoc, "ADDT_GVSR_EXTN_AGRN_MTCD").equals("1")) {
				Logger.info("추가입보방법 : 일괄(2)");
			}
*/
            AppLog.info("**************************************");
            AppLog.info(" 추가연대보증인 ");
            AppLog.info("**************************************");
            // 동의서구분 - 2:연장, 3:취소재발급
            // => 약정상세조회서비스(SAAGagreementinfo0201)에서 받아온 연대보증인을 Return
            // if (XMLUtil.getString(pDoc, "ADDT_GVSR_EXTN_AGRN_DSCD").equals("2") || XMLUtil.getString(pDoc, "ADDT_GVSR_EXTN_AGRN_DSCD").equals("3")) {
            if (MapDataUtil.getString(pDoc, "ADDT_GVSR_EXTN_AGRN_DSCD").equals(SAAGConstants.ADDT_GVSR_EXTN_AGRN_DSCD_2) || MapDataUtil.getString(pDoc, "ADDT_GVSR_EXTN_AGRN_DSCD").equals(SAAGConstants.ADDT_GVSR_EXTN_AGRN_DSCD_3)) {
                AppLog.info("**************************************");
                AppLog.info("동의서구분 : 2.연장동의, 3.취소재발급동의 ");
                AppLog.info("**************************************");
                AppLog.info("1.당초약정번호의 연대보증인을 조회해서 보여줌.");
                // 추가연대보증인
                result.put("LIST1", docAgmt.get("RPL"));
            }
            // if(XMLUtil.getString(pDoc, "ADDT_GVSR_EXTN_AGRN_DSCD").equals("1")) {
            if (MapDataUtil.getString(pDoc, "ADDT_GVSR_EXTN_AGRN_DSCD").equals(SAAGConstants.ADDT_GVSR_EXTN_AGRN_DSCD_1)) {
                // - 추가입보연장동의구분코드 //동의서구분 : 1추가입보
                AppLog.info("**************************************");
                AppLog.info("동의서구분 : 1.추가연보 ");
                AppLog.info("**************************************");
                if ((lZagAddtExtnAgrmMnno != "") && (lZagAddtExtnAgrmMnno != null)) {
                    AppLog.info("*******************************************************");
                    AppLog.info("기존약정관계인 정보를 불러온다. docGuas");
                    AppLog.info("*******************************************************");
                    // Logger.info(docGuas);
                    // Logger.info("*******************************************************");
                    Map inputZagAgrmRlpr = null;
                    inputZagAgrmRlpr = new HashMap();
                    AppLog.info("새로채번 약정번호 NEW_AGRM_MNNO :" + MapDataUtil.getString(docGuas, "NEW_AGRM_MNNO"));
                    MapDataUtil.setString(inputZagAgrmRlpr, "AGRM_MNNO", MapDataUtil.getString(docGuas, "NEW_AGRM_MNNO"));
                    List<Map> rplOutput = additonExtensionTblBCService.selectZagAgrmRlprMsg(inputZagAgrmRlpr);
                    // agreementinfomgmt
                    // Logger.info("*******************************************************");
                    // Logger.info("rplOutput");
                    // Logger.info("*******************************************************");
                    // Logger.info(rplOutput);
                    // Logger.info("*******************************************************");
                    inputZagAgrmRlpr = new HashMap();
                    inputZagAgrmRlpr.put("RPL", rplOutput);
                    docAgmt = inputZagAgrmRlpr;
                    // Logger.info("\n== 기존약정관계인 docAgmt 2 =======================");
                    // Logger.info("\n" + XMLUtil.indent(docAgmt));
                }
                // 기존약정관련인정보가 없으므로
                if ((lZagAddtExtnAgrmMnno == "") || (lZagAddtExtnAgrmMnno == null)) {
                    AppLog.info("*******************************************************");
                    AppLog.info("기존약정관련인정보가 없다.");
                    AppLog.info("*******************************************************");
                    docRequest = new HashMap();
                    // 약정당사자번호
                    MapDataUtil.setString(docRequest, "AGRM_PTNO", MapDataUtil.getString(pDoc, "PTNO"));
                    // 영업일자
                    MapDataUtil.setString(docRequest, "AGRM_DATE", DateUtil.getCurrentDate("yyyymmdd"));
                    // 영업약정구분코드(10:개별 , 20:한도)
                    MapDataUtil.setString(docRequest, "SALS_AGRM_DSCD", "20");
                    // 약정형식구분코드(2:보증)
                    MapDataUtil.setString(docRequest, "AGRM_FORM_DSCD", "2");
                    AppLog.info("*******************************************************");
                    AppLog.info("docRequest");
                    AppLog.info("*******************************************************");
                    AppLog.info("" + docRequest);
                    AppLog.info("*******************************************************");
                    // 약정정보조회(한도약정,개별약정)
                    docAddSurety = agreementInfoMgmtSCService.selectAgreementHd(docRequest);
                    AppLog.info("*******************************************************");
                    AppLog.info("docAddSurety");
                    AppLog.info("*******************************************************");
                    AppLog.info("" + docAddSurety);
                    AppLog.info("*******************************************************");
                    // Logger.info("\n== [input]docRequest 약정정보조회(한도약정,개별약정) =======================");
                    // Logger.info("\n" + XMLUtil.indent(docRequest));
                    AppLog.info("\n== docAddSurety 약정정보조회(한도약정,개별약정) =======================");
                    AppLog.info("\n" + docAddSurety);
                    // [로직] . 입보면제여부 체크 1.입보 Y, 2.입보아님 N
                    String lGvsrDscd = MapDataUtil.getString(docAddSurety, "GVSR_DSCD");
                    // docRequest = XMLUtil.getDocument("<ROOT/>");
                    // if(lGvsrDscd.equals("Y")){
                    if (lGvsrDscd.equals(SAAGConstants.YES)) {
                        // 입보면제 1.Y	필요없다.
                        AppLog.info("=====================");
                        AppLog.info("입보면제여부[Y] 입니다.	고객 관련인정보를 조회..");
                        AppLog.info("=====================");
                        // 연대보증인 정보출력.
                        docAgmt.put("RPL", custResult.get("RPL"));
                        // XMLUtil.setString(inputZagAgrmRlpr,"AGRM_MNNO",XMLUtil.getString(docGuas,"NEW_AGRM_MNNO"));
                        // XMLUtil.setString(inputZagAgrmRlpr,"AGRM_MNNO",XMLUtil.getString(custResult,"NEW_AGRM_MNNO"));
                        // inputZagAgrmRlpr = BSEUtil.executeTask(inputZagAgrmRlpr,"com.cg.sa.ag.additonextensionmgmt.bc.AdditonExtensionTblBC", "selectZagAgrmRlpr");
                    } else // else if(lGvsrDscd.equals("N")){	// 입보면제 2.N
                    if (lGvsrDscd.equals(SAAGConstants.NO)) {
                        AppLog.info("=====================");
                        AppLog.info("입보면제여부[N] 가 아닙니다.한도약정 SAAGagreementinfo1507 연대보증인조회.");
                        AppLog.info("=====================");
                        AppLog.info("****************************");
                        AppLog.info("입보면제여부[N] 가 아닙니다.한도약정 SAAGagreementinfo1507 연대보증인조회. docAddSurety");
                        AppLog.info("****************************");
                        AppLog.info("" + docAddSurety);
                        AppLog.info("****************************");
                        // Document rplOutput = BSEUtil.executeTask(inputZagAgrmRlpr,"com.cg.sa.ag.additonextensionmgmt.bc.AdditonExtensionTblBC", "selectZagAgrmRlpr");
                        docAgmt.put("RPL", docAddSurety.get("AGRM_RLPR"));
                        // XMLUtil.setVector(inputZagAgrmRlpr, "RPL", XMLUtil.getVectorDOM(rplOutput,"RPL"));
                        // XMLUtil.setVector(custResult, "RPL", XMLUtil.getVectorDOM(result,"RSOA_LIST"));	// 추가연대보증인
                    }
                }
            }
            // 추가연대보증인
            result.put("LIST1", docAgmt.get("RPL"));
            AppLog.info("***********************");
            AppLog.info("result");
            AppLog.info("***********************");
            AppLog.info("" + result);
        } catch (ElException e) {
        	AppLog.warn(e.getMessage(), e);
            /**
             * 3.Exception 처리
             *  Framework Level Exception을 catch하여 임의 가공 처리 할 경우 Warning 객체 정의
             *  Exception 객체 상속구조: Throwable<-Exceltion<-Warning<-FrameworkWarning
             */
            throw new CgAppUserException("CG_ERROR", 0, e.getMessage(), "SPLT0003", e);
        }
        AppLog.info("\n== AdditonExtensionBC.selectAdditonGivingSuretybyPK end =======================");
        /**
         * 4.결과 반환
         */
        return result;
    }

    /**
     * <<TITLE>>
     * 연대보증인추가입보연장 신청정보를 조회한다.
     * <<LOGIC>>
     */
    public Map selectAdditonGivingSuretybyPK(Map pDoc) throws ElException, Exception {
        AppLog.info("selectAdditonGivingSuretybyPK (pDoc) = \n" + pDoc);
        Map result = new HashMap();
        MapDataUtil.setAttribute(pDoc, "totalCount", "yes");
        //XDA xda = XDAFactory.getXDA(Constants.KEEP_CONNECTION);
        String addtGvsrExtnAgrnMtcd = MapDataUtil.getString(pDoc, "ADDT_GVSR_EXTN_AGRN_MTCD");
        // 화면에서 넘어온 약정관리번호
        String addtAgrmMnno = MapDataUtil.getString(pDoc, "AGRM_MNNO");
        
        /**
         * ****************************
         *  추가입보연장동의 신청내역 조회
         * *****************************
         */
        Map resAddtExtn = null;
        if (SAAGConstants.ADDT_GVSR_EXTN_AGRN_MTCD_1.equals(addtGvsrExtnAgrnMtcd)) {
            resAddtExtn = comCgSaAgAdditonextensionmgmtAgzagaddtextnDAO.ag_zag_addt_extn_so3036(pDoc);
        } else {
            resAddtExtn = comCgSaAgAdditonextensionmgmtAgzagaddtextnDAO.ag_zag_addt_extn_so3041(pDoc);
        }
        
        if(!ObjectUtils.isEmpty(resAddtExtn)) {
        	result.putAll(resAddtExtn);
        	AppLog.info("추가입보연장동의 신청내역 조회 = \n" + resAddtExtn.toString());
        	AppLog.info("result = \n" + result);
        }
        
        /**
         * ****************************
         *  당초 약정정보 조회
         * *****************************
         */
        Map resAgmt = comCgSaAgAgreementinfomgmtAgzagagmtDAO.ag_zag_agmt_so1001(pDoc);
        
        if(!ObjectUtils.isEmpty(resAgmt)) {
        	result.putAll(resAgmt);
        	AppLog.info("당초 약정정보 조회 = \n" + resAgmt);
        	AppLog.info("result = \n" + result);
        }
        
        /**
         * ****************************
         *  당초 보증정보 조회
         * *****************************
         */
        Map 		resGuas 	= null;
        List<Map>	resGuasList	= null;
        
        // 2012.01.27 박기석 - 보증정보를 단건이 아닌 해당되는  신규보증서부터 전부 조회되도록 수정
        // Document resGuas = BSEUtil.executeService(pDoc, "SAGUguasinfminqr0001");
    	resGuasList = (List<Map>) guasInfmInqrSCService.selectGuaranteeSheetList(pDoc).get(GUUtil.ATTRIBUTE_RESULT); // SAGUguasinfminqr0023
        
        if(!ObjectUtils.isEmpty(resGuasList)) {
        	MapDataUtil.setList(result, "GUAS_LIST", resGuasList);
        	AppLog.info("당초 보증정보 조회 = \n" + resAgmt);
        	AppLog.info("result = \n" + result);
        } else {
        	MapDataUtil.setList(result, "GUAS_LIST", resGuasList);
        }
        
        /**
         * ****************************
         *  당초 연대보증인 조회
         * *****************************
         */
        Map reqGurtJnsr = new HashMap();
        // 계약관리번호, 변경일련번호
        // 2012.01.27 박기석 - 보증 단건을 조회해 계약관리번호와 변경일련번호만 셋팅한다.
        resGuas = guasInfmInqrSCService.selectGuaranteeSheetbyPK(pDoc);
        AppLog.info("당초 연대보증인 조회 = \n" + resGuas);

        // 계약관리번호, 변경일련번호
        MapDataUtil.setString(reqGurtJnsr, "CNRC_MNNO", MapDataUtil.getString(pDoc, "CNRC_MNNO"));
        MapDataUtil.setString(reqGurtJnsr, "CHNG_SRNO", MapDataUtil.getString(resGuas, "LAST_CHNG_SRNO"));

        // 개인연대보증 PATY_TPCD:500
        MapDataUtil.setString(reqGurtJnsr, "PATY_TPCD", SAGUConstants.PATY_PSNL_JNSR);
        List psnlList = (List) gurtPartyMgmtSCService.selectGurtParty(reqGurtJnsr).get(GUUtil.ATTRIBUTE_RESULT); // SAGUgurtpartymgmt0004
        AppLog.info("개인연대보증 = \n" + psnlList);
        
        // 법인연대보증 PATY_TPCD:600
        MapDataUtil.setString(reqGurtJnsr, "PATY_TPCD", SAGUConstants.PATY_CRPT_JNSR);
        List crptList = (List) gurtPartyMgmtSCService.selectGurtParty(reqGurtJnsr).get(GUUtil.ATTRIBUTE_RESULT); // SAGUgurtpartymgmt0004
        AppLog.info("법인연대보증 = \n" + crptList);
        
        /**
         * ****************************
         *  2011.06.17 박기석
         *  일괄일경우 약정관리번에 해당하는 연대보증인 조회
         * *****************************
         */
        // ----- 일괄일경우 START
        if (SAAGConstants.ADDT_GVSR_EXTN_AGRN_MTCD_2.equals(addtGvsrExtnAgrnMtcd)) {
            reqGurtJnsr = new HashMap();
            
            MapDataUtil.setString(reqGurtJnsr, "AGRM_MNNO", addtAgrmMnno);
            MapDataUtil.setString(reqGurtJnsr, "AGRM_RLPR_DSCD", SAAGConstants.AGRM_RLPR_DSCD_IN20);
            
            psnlList = comCgSaAgAgreementinfomgmtAgzagagmtDAO.ag_zag_agmt_so1512(reqGurtJnsr);
        }
        // ----- 일괄일경우 END

        ArrayList guasPartyList = new ArrayList();
        Map listDoc = null;
        Iterator<Map> itr = null;
        // 2011.06.15 박기석 - 추가입보자가 있을경우 판단을위해 당초연대보증인의 ptno를 담아둔다.
        String listPtno = "";
        
        if (null != psnlList) {
            itr = psnlList.iterator();
          
            while (itr.hasNext()) {
                listDoc = itr.next();
          
                // 추가입보자가 있을경우 판단을위해 당초연대보증인의 ptno를 담아둔다.
                if (!"".equals(listPtno)) {
                    listPtno = listPtno + "/";
                }
          
                listPtno = listPtno + MapDataUtil.getString(listDoc, "PTNO");
                guasPartyList.add(listDoc);
            }
        }
        
        if (null != crptList) {
            itr = crptList.iterator();
           
            while (itr.hasNext()) {
                listDoc = itr.next();
                // 추가입보자가 있을경우 판단을위해 당초연대보증인의 ptno를 담아둔다.
                if (!"".equals(listPtno)) {
                    listPtno = listPtno + "/";
                }
           
                listPtno = listPtno + MapDataUtil.getString(listDoc, "PTNO");
                guasPartyList.add(listDoc);
            }
        }
        
        /**
         *  2011.06.15 박기석
         *  기등록된 입보서가 있는경우.. 당초연대보증인에 추가연대보증인이 추가될 수 있기때문에 set해주는 위치를 다르게한다.
         */
//        int addtExtnCnt = Integer.parseInt(MapDataUtil.getAttribute(resAddtExtn, "result"));
        if (resAddtExtn == null) { // addtExtnCnt != 1 (조회하는 쿼리의 리턴 타입이 단건이므로 cnt가 1이 아닌경우 null로 판단)
            result.put("GURT_JNSR", guasPartyList);
            AppLog.info("기등록된 입보서가 있는경우.. \n" + guasPartyList);
            AppLog.info("result = \n" + result);
        }
        
        /**
         * ****************************
         *  추가 연대보증인 조회
         * *****************************
         */
        List<Map> resAddtJnsr = null;
        Map reqDoc = null;
        Map resDoc = null;
        // 추가입보연장동의 신청내역이 있던지 없던지.. 무조건 신규와 같이 불러온다. => 신청내역이 있는경우는 이 아래에서 추가해줌
        reqDoc = new HashMap();
        
        MapDataUtil.setString(reqDoc, "AGRM_PTNO", MapDataUtil.getString(pDoc, "PTNO"));
        MapDataUtil.setString(reqDoc, "SALS_AGRM_DSCD", SAAGConstants.SALS_AGRM_DSCD_20);
        MapDataUtil.setString(reqDoc, "AGRM_FORM_DSCD", SAAGConstants.AGRM_FORM_DSCD_2);
        
        Map hdAgrm = MapDataUtil.getMap(agreementInfoMgmtSCService.selectAgreementHd(reqDoc), "result"); // SAAGagreementinfo1507
        AppLog.info("추가 연대보증인 조회 = \n" + hdAgrm);
        
        // 약정관리번호
        String tmpAgrmMnno = MapDataUtil.getString(hdAgrm, "AGRM_MNNO");
        // 약정당사자번호
        String tmpAgrmPtno = MapDataUtil.getString(hdAgrm, "AGRM_PTNO");
        // 법인입보구분코드
        String tmpGvsrDscd = MapDataUtil.getString(hdAgrm, "GVSR_DSCD");
        // 개인입면제여부
        String tmpPsnlGvsrExmtYn = MapDataUtil.getString(hdAgrm, "PSNL_GVSR_EXMT_YN");
        
        if ("2".equals(tmpGvsrDscd) && "Y".equals(tmpPsnlGvsrExmtYn)) {
            // 입보면제일 경우 ==> 고객의 관련인 정보 조회
            MapDataUtil.setString(reqDoc, "CUST_INQR_DSCD", "IA01");
            MapDataUtil.setString(reqDoc, "CUST_INQR_COND_DSCD", "01");
            MapDataUtil.setString(reqDoc, "SRCH_KWRD", tmpAgrmPtno);
            
            resDoc = MapDataUtil.getMap(custMgmtSCService.selectCustInfo(reqDoc), "PRTY_BASC");
            // data 노드명을 <agreementinfomgmt/>로 통일 시키기 위해서
            List rsoaList = (List)resDoc.get("RSOA_LIST");
            
            ArrayList addtJnsrList = new ArrayList();
            Map tempDoc = null;
            Iterator<Map> dItr = null;
            
            if (null != rsoaList) {
                dItr = rsoaList.iterator();
                Map aDoc = null;
            
                while (dItr.hasNext()) {
                    tempDoc = dItr.next();
                    
                    if (SAAGConstants.RPPR_POS_CD_IN10.equals(MapDataUtil.getString(tempDoc, "OFCR_STCH_DSCD"))) {
                        aDoc = new HashMap();
                        MapDataUtil.setString(aDoc, "PTNO"			, MapDataUtil.getString(tempDoc, "PATR_PTNO"));
                        MapDataUtil.setString(aDoc, "PRTY_NM"		, MapDataUtil.getString(tempDoc, "PATR_PRTY_NM"));
                        MapDataUtil.setString(aDoc, "CUNO_KNCD"		, MapDataUtil.getString(tempDoc, "PATR_CUNO_KNCD"));
                        MapDataUtil.setString(aDoc, "CUNO"			, MapDataUtil.getString(tempDoc, "PATR_CUNO"));
                        MapDataUtil.setString(aDoc, "QTRT"			, MapDataUtil.getString(tempDoc, "QTRT"));
                        MapDataUtil.setString(aDoc, "QUOT_RNKN"		, MapDataUtil.getString(tempDoc, "QUOT_RNKN"));
                        MapDataUtil.setString(aDoc, "ZPCD1"			, MapDataUtil.getString(tempDoc, "LCTN_ZPCD"));
                        MapDataUtil.setString(aDoc, "AGRM_RPPR_ADRS", MapDataUtil.getString(tempDoc, "LCTN_ALL_ADRS"));
                        MapDataUtil.setString(aDoc, "JNGR_YN"		, MapDataUtil.getString(tempDoc, "EXSN_MMBR_YN"));
                        MapDataUtil.setString(aDoc, "RPPR_POS_CD"	, MapDataUtil.getString(tempDoc, "OFCR_STCH_DSCD"));
                        
                        addtJnsrList.add(aDoc);
                    }
                }
            }
            
            resAddtJnsr = addtJnsrList;
            
        } else {
            // 입보면제가 아닐 경우 ==> 현재 약정의 연대보증인 조회
            MapDataUtil.setString(reqDoc, "AGRM_MNNO", tmpAgrmMnno);
            MapDataUtil.setString(reqDoc, "AGRM_RLPR_DSCD", SAAGConstants.AGRM_RLPR_DSCD_IN20);
            
            // 20101126 약정관련인 추출시 고객쪽 주소 가져오는 쿼리로 교체 - 김진희
            // resAddtJnsr = xda.execute("com.cg.sa.ag.agreementinfomgmt.xda.ag_zag_agmt_so1512", reqDoc);
            resAddtJnsr = comCgSaAgAgreementinfomgmtAgzagagmtDAO.ag_zag_agmt_so1512(reqDoc);
        }
        
        // 현재 약정상태 정보
        MapDataUtil.setString(result, "AGRM_STCD", MapDataUtil.getString(hdAgrm, "AGRM_STCD"));
        MapDataUtil.setString(result, "VLDT_YN", MapDataUtil.getString(hdAgrm, "VLDT_YN"));
        
        result.put("ADDT_JNSR", resAddtJnsr);
        
        
        /**
         *  2011.06.16 박기석
         *  기등록된 신청내역이 있는경우에는 등록된 신청내역을 별도의 node로 생성해준다.
         *  => 화면에서 수정 및 조회용도일 경우에는 등록된 신청내역을 추가연대보증인에 보여줄 수 있도록 처리
         */
        // 기등록된 신청내역 node 만들어주기 ------------ START
        if (resAddtExtn != null) { // addtExtnCnt == 1
            // 추가입보연장동의 신청내역 있음
            reqDoc = new HashMap();
            MapDataUtil.setString(reqDoc, "AGRM_MNNO", MapDataUtil.getString(resAddtExtn, "AGRM_MNNO"));
            
            resAddtJnsr = comCgSaAgAdditonextensionmgmtAgzagagrmrlptDAO.ag_zag_agrm_rlpt_so3040(reqDoc);
            
            /**
             * 2011.06.15 박기석
             * 추가입보에 기등록된 연대보증인이 있는경우에는 당초연대보증인으로 같이 조회한다.
             */
            psnlList = resAddtJnsr;
            
            if (null != psnlList) {
                itr = psnlList.iterator();
            
                boolean listPtnoFlag = true;
                String[] listPtnoSplit = null;
            
                while (itr.hasNext()) {
                    listDoc = null;
                    listDoc = itr.next();
                    
                    listPtnoSplit = null;
                    listPtnoFlag = true;
                    listPtnoSplit = listPtno.split("/");
                    
                    for (int j = 0; j < listPtnoSplit.length; j++) {
                        if (MapDataUtil.getString(listDoc, "PTNO").equals(listPtnoSplit[j])) {
                            // 원래 당초연대보증인은 추가할 필요없다.
                            listPtnoFlag = false;
                        }
                    }
                    
                    if (listPtnoFlag) {
                        MapDataUtil.setString(listDoc, "GVSR_RSNM", "추가입보");
                        guasPartyList.add(listDoc);
                    }
                }
            }
            
            // 기등록된 입보서가 있는경우.. 당초연대보증인에 추가연대보증인이 추가될 수 있기때문에 아래에서 set해준다.
            result.put("GURT_JNSR", guasPartyList);
            AppLog.info("GURT_JNSR = \n" + guasPartyList);
            AppLog.info("GURT_JNSR (result) = \n" + result);
            
            // 등록된 연대보증인 노드를 생성해준다.
            result.put("EXIST_ADDT_JNSR", resAddtJnsr);
        }
        
        // 기등록된 신청내역 node 만들어주기 ------------ END
        AppLog.info("" + result);
        AppLog.info("기등록된 신청내역 node 만들어주기(result) = \n" + result);
        
        return result;
    }

    /**
     * <<TITLE>>
     * 보증당사자 관련 조회 처리를 한다.
     * <<LOGIC>>
     * 보증당사자 관련 조회 처리를 한다. SAGUgurtpartymgmt0004
     */
    public Map appendDocListSurety(Map pDocReq, Map pDocData) throws ElException, Exception {
        /**
         * 1.Document 변수의 정의
         *
         * XDA 결과 변수 result
         */
        // Return 할 데이터를 담을 Array
        List resAryList = null;
        if (MapDataUtil.getAttribute(pDocData, "result").equals(SAAGConstants.RESULT_0)) {
            resAryList = new ArrayList();
        } else {
            resAryList = (List)pDocData.get("vector");
        }
        
        try {
            Map docOrignSurety = gurtPartyMgmtSCService.selectGurtParty(pDocReq);
            AppLog.info("\n== docOrignSurety =======================");
            AppLog.info("\n" + docOrignSurety);
            
            // 새로운 조회한 데이터 목록
            List aryList = (List)docOrignSurety.get(GUUtil.ATTRIBUTE_RESULT);
            Iterator<Map> itr = aryList.iterator();
            while (itr.hasNext()) {
                Map listDoc = itr.next();
                AppLog.info("\n== listDoc =====================================");
                AppLog.info("\n" + listDoc);
                if(listDoc != null) resAryList.add(listDoc);
            }
        } catch (ElException e) {
        	AppLog.warn(e.getMessage(), e);
            /**
             * 3.Exception 처리
             *  Framework Level Exception을 catch하여 임의 가공 처리 할 경우 Warning 객체 정의
             *  Exception 객체 상속구조: Throwable<-Exceltion<-Warning<-FrameworkWarning
             */
            throw new CgAppUserException("CG_ERROR", 0, e.getMessage(), "SPLT0003", e);
        }
        AppLog.info("\n== AdditonExtensionBC.appendDocListSurety end =======================");
        /**
         * 2
         *  4.결과 반환
         */
        
        Map	result	= new HashMap();
        result.put("vector", resAryList);
        return result;
    }

    /**
     * <<TITLE>>
     * 연대보증인 추가입보서 등록 대상을 조회한다.
     * <<LOGIC>>
     * 1.연대보증인 추가입보서 등록 대상을 조회한다. (xda 실행 : ag_zag_agmt_so1305)
     * 2. 결과리턴
     * @param pDoc
     * @return
     * @throws Exception
     */
    public Map selectAdditionExtension(Map pDoc) throws ElException, Exception {
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
            //result = xda.execute("[XDAID를 입력합니다 ]", pDoc);
        } catch (ElException e) {
        	AppLog.warn(e.getMessage(), e);
            /**
             * 3.Exception 처리
             *  Framework Level Exception을 catch하여 임의 가공 처리 할 경우 Warning 객체 정의
             *  Exception 객체 상속구조: Throwable<-Exceltion<-Warning<-FrameworkWarning
             */
            throw new CgAppUserException("CG_ERROR", 0, e.getMessage(), CodeUtil.getCodeValue("[코드항목]", "[코드카테고리]", "[에러코드번호]"), e);
        }
        /**
         * 4.결과 반환
         */
        return result;
    }

    /**
     * <<TITLE>>
     * 추가입보 및 동의서 신청 이력을 조회힌다.
     * <<LOGIC>>
     * 1.연대보증인 추가입보 및 동의서 신청이력을 조회한다. (xda 실행 : ag_zag_agmt_so1302)
     * 2. 결과리턴
     * @param pDoc
     * @return
     * @throws Exception
     */
    public ArrayList<Map> selectAdditionExtensionApp(Map pDoc) throws ElException, Exception {
        AppLog.info("************************************");
        AppLog.info("[BC] selectAdditionExtensionApp pDoc");
        AppLog.info("************************************");
        AppLog.info("" + pDoc);
        AppLog.info("************************************");
        /**
         * 1.Document 변수의 정의
         *
         * XDA 결과 변수 result
         */
        ArrayList<Map> result = null;
        MapDataUtil.setAttribute(pDoc, "totalCount", "yes");
        try {
            /**
             * 2.XDA를 실행합니다.
             * 호출하려는 XDAID를 입력합니다.
             */
            //XDA xda = XDAFactory.getXDA(Constants.KEEP_CONNECTION);
            // if(lGuasNo.equals("")){	// 약정번호로 조회.
            AppLog.info("1.약정번호로 조회............");
            result = comCgSaAgAdditonextensionmgmtAgzagagmtDAO.ag_zag_agmt_so1302(pDoc);
            /*
			}else if(lAgrmMnno.equals("")){ // 보증서번호로 조회 .
				Logger.info("2.보증서번호로 조회............");
				result = xda.execute("com.cg.sa.ag.additonextensionmgmt.xda.ag_zag_agmt_so1303", pDoc);
			}else{ // 둘다 입력되면 약정번호로 조회한다.
				Logger.info("1.약정번호로 조회............");
				result = xda.execute("com.cg.sa.ag.additonextensionmgmt.xda.ag_zag_agmt_so1302", pDoc);
			}
			*/
            AppLog.info("******************************************");
            AppLog.info("result");
            AppLog.info("******************************************");
            AppLog.info("" + result);
            AppLog.info("******************************************");
        } catch (ElException e) {
        	AppLog.warn(e.getMessage(), e);
            /**
             * 3.Exception 처리
             *  Framework Level Exception을 catch하여 임의 가공 처리 할 경우 Warning 객체 정의
             *  Exception 객체 상속구조: Throwable<-Exceltion<-Warning<-FrameworkWarning
             */
            throw new CgAppUserException("CG_ERROR", 0, e.getMessage(), "SPLT0003", e);
        }
        /**
         * 4.결과 반환
         */
        return result;
    }

    /**
     * <<TITLE>>
     * 약정의 추가입보 및 동의서등록의 채무명세를 조회한다.
     * <<LOGIC>>
     * 1.약정관리번호의 채무명세를 조회한다.
     * > com.cg.sa.gu.guasinfminqr.Iguasinfminqr.selectGuaranteeSheet
     * 2. 결과리턴
     * @param pDoc
     * @return
     * @throws Exception
     */
    public ArrayList<Map> selectAgreementDebtDtls(Map pDoc) throws ElException, Exception {
        /**
         * 1.Document 변수의 정의
         *
         * XDA 결과 변수 result
         */
        ArrayList<Map> result = null;
        MapDataUtil.setAttribute(pDoc, "totalCount", "yes");
        
        try {
        	result = new ArrayList<Map>();
        
            /**
             * 2.XDA를 실행합니다.
             * 호출하려는 XDAID를 입력합니다.
             */
            //XDA xda = XDAFactory.getXDA(Constants.KEEP_CONNECTION);
            result = comCgSaAgAdditonextensionmgmtAgzagagmtDAO.ag_zag_agmt_so1301(pDoc);
        } catch (ElException e) {
        	AppLog.warn(e.getMessage(), e);
            /**
             * 3.Exception 처리
             *  Framework Level Exception을 catch하여 임의 가공 처리 할 경우 Warning 객체 정의
             *  Exception 객체 상속구조: Throwable<-Exceltion<-Warning<-FrameworkWarning
             */
            throw new CgAppUserException("CG_ERROR", 0, e.getMessage(), "SPLT0003", e);
        }
        
        /**
         * 4.결과 반환
         */
        return result;
    }

    /**
     * <<TITLE>>
     * 연대보증인 동의서 신청내용을 조회 한다
     * <<LOGIC>>
     * 1. 약정번호와 보증서번호로 연대보증인 동의서 신청내용을 조회한다.
     * >com.cg.sa.ag.additonextensionmgmt.bc.AdditonExtensionTblBC.selectZagAdGvsrExAgrnAplt
     * 2. 신청내용이 있는경우
     * 2.1. 추가입보연장동의방법이 개별인 경우 추가입보 연장동의 대상보증서 정보를 조회한다.
     * > IF (추가입보연장동의방법코드 == 개별) {
     * >com.cg.sa.ag.additonextensionmgmt.bc.AdditonExtensionTblBC.selectZagAdGvsrExAgrnApGaus
     * > }
     * 2.2. 추가입보 연장동의 연대보증인 정보를 조회한다.
     * >com.cg.sa.ag.additonextensionmgmt.bc.AdditonExtensionTblBC.selectZagAdGvsrExAgrnApJnsrAll
     * 3. 신청내용이 없는경우 약정관련인 정보를 조회한다.
     * 3.1 약정상세정보를 조회한다.
     * > com.cg.sa.ag.agreementinfomgmt.Iagreementinfomgmt.selectAgreementDtlbyPK
     * 3.2 추가입보연장동의방법이 개별인 경우 보증서정보를 조회한다.
     * > IF (추가입보연장동의방법코드 == 개별) {
     * > com.cg.sa.gu.guasinfminqr.Iguasinfminqr.selectGuaranteeSheetbyPK
     * > }
     * 4. 결과리턴
     * @param pDoc
     * @return
     * @throws Exception
     */
    public Map selectExtensionAgreemenbyPK(Map pDoc) throws ElException, Exception {
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
            //result = xda.execute("[XDAID를 입력합니다 ]", pDoc);
        } catch (ElException e) {
        	AppLog.warn(e.getMessage(), e);
            /**
             * 3.Exception 처리
             *  Framework Level Exception을 catch하여 임의 가공 처리 할 경우 Warning 객체 정의
             *  Exception 객체 상속구조: Throwable<-Exceltion<-Warning<-FrameworkWarning
             */
            throw new CgAppUserException("CG_ERROR", 0, e.getMessage(), CodeUtil.getCodeValue("[코드항목]", "[코드카테고리]", "[에러코드번호]"), e);
        }
        /**
         * 4.결과 반환
         */
        return result;
    }

    /**
     * <<TITLE>>
     * 연대보증인추가입보동의서현황조회을 조회한다.
     * <<LOGIC>>
     * 1. 연대보증인추가입보동의서현황조회을 조회한다.(xda 실행 :ag_zag_agmt_so1516)
     * 2. 결과리턴
     */
    public ArrayList<Map> selectWrittenConsent(Map pDoc) throws ElException, Exception {
        /**
         * 1.Document 변수의 정의
         *
         * XDA 결과 변수 result
         */
        ArrayList<Map> result = null;
        MapDataUtil.setAttribute(pDoc, "totalCount", "yes");
        try {
            /**
             * 2.XDA를 실행합니다.
             * 호출하려는 XDAID를 입력합니다.
             */
            //XDA xda = XDAFactory.getXDA(Constants.KEEP_CONNECTION);
            result = comCgSaAgAdditonextensionmgmtAgzagagmtDAO.ag_zag_agmt_so1516(pDoc);
        } catch (ElException e) {
        	AppLog.warn(e.getMessage(), e);
            /**
             * 3.Exception 처리
             *  Framework Level Exception을 catch하여 임의 가공 처리 할 경우 Warning 객체 정의
             *  Exception 객체 상속구조: Throwable<-Exceltion<-Warning<-FrameworkWarning
             */
            throw new CgAppUserException("CG_ERROR", 0, e.getMessage(), "SPLT0003", e);
        }
        /**
         * 4.결과 반환
         */
        return result;
    }

    /**
     * <<TITLE>>
     * 연대보증인 추가입보서 신청내용을 등록 한다.
     * <<LOGIC>>
     * 1. 연대보증인 추가입보서 신청내용을 검증한다.
     * 2. 연대보증인 추가입보서 신청내용을 등록한다.
     * 2.1 추가입보연장동의등록 테이블을 등록한다.
     * >com.cg.sa.ag.additonextensionmgmt.bc.AdditonExtensionTblBC.insertZagAdGvsrExAgrnAplt
     * 2.2 추가입보연장동의대상보증서 테이블을 등록한다.
     * > IF (추가입보연정동의방법코드 == 개별) {
     * >com.cg.sa.ag.additonextensionmgmt.bc.AdditonExtensionTblBC.insertZagAdGvsrExAgrnApGaus
     * > }
     * 2.3 추가입보연장동의연대보증인 테이블을 등록한다.
     * > LOOP(i <= size(추가입보한연대보증인수)) {
     * >com.cg.sa.ag.additonextensionmgmt.bc.AdditonExtensionTblBC.insertZagAdGvsrExAgrnApJnsr
     * > }
     * 3.결과리턴
     * @param pDoc
     * @return
     * @throws Exception
     */
    public Map insertAdditonGivingSurety_OLD(Map pDoc) throws ElException, Exception {
        /**
         * 1.Document 변수의 정의
         *
         * XDA 결과 변수 result
         */
        Map result = null;
        result = new HashMap();
        Map listDoc = null;
        // 약정관련인 저장용
        Map docReqPT = new HashMap();
        // 약정동의보증서 저장용
        Map docReqAG = new HashMap();
        // 당초약정정보
        Map docVO = MapDataUtil.getMap(pDoc, "VO");
        // 당초보증정보
        Map docGU = MapDataUtil.getMap(pDoc, "VO2");
        // 추가연대보증인
        List<Map> docVL = (List<Map>)pDoc.get("JOINTSURETY_LIST");
        AppLog.info("\n== AdditonExtensionBC.insertAdditonGivingSurety start =======================");
        AppLog.info("\n== docVO =======================");
        AppLog.info("\n" + docVO);
        AppLog.info("\n== docGU =======================");
        AppLog.info("\n" + docGU);
        try {
            /**
             * 2.XDA를 실행합니다.
             * 호출하려는 XDAID를 입력합니다.
             */
            //XDA xda = XDAFactory.getXDA(Constants.KEEP_CONNECTION);
            AppLog.info("\n== listDoc =======================");
            AppLog.info("\n" + listDoc);
            // AGRM_MNNO.TRNO 거래번호 (10)
            // String newAgrmMnno =  com.inswave.ext.cg.util.KeyUtil.getFormatIntKey("AGRM_MNNO@ZAG_AGMT", 10);
            Map newAgrmMnnoDo = agreementRegTblBCService.selectArgmMnno(pDoc);
            String newAgrmMnno = "";
            newAgrmMnno = MapDataUtil.getString(newAgrmMnnoDo, "NEW_AGRM_MNNO");
            /*
			// 약정관련자일련번호 채번
			docReqPT = XMLUtil.getDocument("<ROOT/>");
			XMLUtil.setString(docReqPT, "AGRM_MNNO",         newAgrmMnno);          // 약정관리번호
			
			//result = xda.execute("com.cg.sa.ag.additonextensionmgmt.xda.ag_zag_agmt_rlpr_so3105", docReqPT);
			Logger.info("\n== result 약정관련자일련번호 채번 [" + XMLUtil.getString(docVO,   "AGRM_MNNO") + "]=======================");
			Logger.info("\n" + XMLUtil.indent(result));
			*/
            AppLog.info("//////////////////////////");
            AppLog.info("// 연장동의보증서 등록");
            AppLog.info("//////////////////////////");
            docReqAG = new HashMap();
            // ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
            // 약정관리번호
            MapDataUtil.setString(docReqAG, "AGRM_MNNO", newAgrmMnno);
            // ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
            // XMLUtil.setString(docReqAG, "AGRM_RLPR_SRNO",           XMLUtil.getString(result,  "AGRM_RLPR_SRNO"));     // 약정관련자일련번호
            // 약정당사자번호
            MapDataUtil.setString(docReqAG, "AGRM_PTNO", MapDataUtil.getString(docVO, "AGRM_PTNO"));
            // 계약관리번호
            MapDataUtil.setString(docReqAG, "CNRC_MNNO", MapDataUtil.getString(pDoc, "CNRC_MNNO"));
            // 변경일련번호
            MapDataUtil.setString(docReqAG, "CHNG_SRNO", MapDataUtil.getString(pDoc, "CHNG_SRNO"));
            // 보증서번호
            MapDataUtil.setString(docReqAG, "GUAS_NO", MapDataUtil.getString(docGU, "GUAS_NO"));
            // 추가입보연장동의일자
            MapDataUtil.setString(docReqAG, "ADDT_GVSR_EXTN_AGRN_DATE", MapDataUtil.getString(docVO, "ADDT_GVSR_EXTN_AGRN_DATE"));
            // 연장보증기한일자
            MapDataUtil.setString(docReqAG, "EXTN_GURT_DLNN_DATE", MapDataUtil.getString(docVO, "EXTN_GURT_DLNN_DATE"));
            // 추가입보연장동의방법코드
            MapDataUtil.setString(docReqAG, "ADDT_GVSR_EXTN_AGRN_DSCD", MapDataUtil.getString(pDoc, "ADDT_GVSR_EXTN_AGRN_MTCD"));
            // 추가입보연장동의구분코드
            MapDataUtil.setString(docReqAG, "ADDT_GVSR_EXTN_AGRN_MTCD", MapDataUtil.getString(pDoc, "ADDT_GVSR_EXTN_AGRN_DSCD"));
            // 배수적용신용등급코드
            MapDataUtil.setString(docReqAG, "MLTP_APLC_CRRTN_CD", MapDataUtil.getString(pDoc, "MLTP_APLC_CRRTN_CD"));
            // 약정좌수
            MapDataUtil.setString(docReqAG, "AGRM_NOAC", MapDataUtil.getString(docVO, "AGRM_NOAC"));
            // 추가입보방법이 1.개별이면 보증금액 BNAMT
            // 2.일괄이면 약정금액 BASC_FNCN_LMAMT
            String lAddtGvsrExtnAgrnMtcd = MapDataUtil.getString(pDoc, "ADDT_GVSR_EXTN_AGRN_MTCD");
            // if(lAddtGvsrExtnAgrnMtcd.equals("1")){
            if (lAddtGvsrExtnAgrnMtcd.equals(SAAGConstants.ADDT_GVSR_EXTN_AGRN_MTCD_1)) {
                AppLog.info("보증금액:" + MapDataUtil.getString(docGU, "BNAMT"));
                // 보증금액
                MapDataUtil.setString(docReqAG, "AGRM_AMT", MapDataUtil.getString(docGU, "BNAMT"));
            } else // else if(lAddtGvsrExtnAgrnMtcd.equals("2")){
            if (lAddtGvsrExtnAgrnMtcd.equals(SAAGConstants.ADDT_GVSR_EXTN_AGRN_MTCD_2)) {
                AppLog.info("약정금액:" + MapDataUtil.getString(docVO, "BASC_FNCN_LMAMT"));
                // 약정금액
                MapDataUtil.setString(docReqAG, "AGRM_AMT", MapDataUtil.getString(docVO, "BASC_FNCN_LMAMT"));
            }
            String lEmpNo = UserHeaderUtil.getInstance().getEmpno();
            // 최종변경일시
            MapDataUtil.setString(docReqAG, "LAST_CHNG_DTTM", (String) UserHeaderUtil.getInstance().getTimestamp());
            // 최종변경자ID
            MapDataUtil.setString(docReqAG, "LAST_CHNR_ID", lEmpNo);
            // 추가입보사유내용
            MapDataUtil.setString(docReqAG, "ADDT_GVSR_RSN_CNTS", MapDataUtil.getString(docVO, "ADDT_GVSR_RSN_CNTS"));
            // 추가입보사유내용
            MapDataUtil.setString(docReqAG, "CHNG_TRGT_AGRM_MNNO", MapDataUtil.getString(docGU, "AGRM_MNNO"));
            AppLog.info("\n== listDoc.docReqAG =======================");
            AppLog.info("\n" + docReqAG);
            // if(XMLUtil.getString(pDoc, "ACTIONMODE").equals("U")){
            int	resultCnt	= 0;
            if (MapDataUtil.getString(pDoc, "ACTIONMODE").equals(SAAGConstants.UPDATE)) {
            	resultCnt	= additonExtensionTblBCService.updateZagAddtExtn(docReqAG);
            } else {
                // result = xda.execute("com.cg.sa.ag.additonextensionmgmt.xda.ag_zag_ad_gvsr_ex_agrn_guas_io3104", docReqAG);
            	resultCnt	= additonExtensionTblBCService.insertZagAdGvsrExAgrnGaus(docReqAG);
            }
            AppLog.info("**************************");
            AppLog.info(" 약정 관련인 result");
            AppLog.info("**************************");
            AppLog.info("" + resultCnt);
            AppLog.info("**************************");
            AppLog.info("######### ZAG_ADDT_EXTN END 	###########################");
            AppLog.info("######### ZAG_AGRM_RLPR START 	###########################");
            // 추가연대보증인 목록
            List aryList = docVL;
            Iterator<Map> itr = aryList.iterator();
            // 일련번호
            while (itr.hasNext()) {
                listDoc = itr.next();
                // lAgrmRlprSrno = String.format("%05d",intRlpr);
                AppLog.info("//////////////////////////");
                AppLog.info("// 약정관련인 등록");
                AppLog.info("//////////////////////////");
                docReqPT = new HashMap();
                // ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
                // 새로 채번된 약정관리번호
                MapDataUtil.setString(docReqPT, "NEW_AGRM_MNNO", newAgrmMnno);
                // 기존약정관리번호
                MapDataUtil.setString(docReqPT, "AGRM_MNNO", MapDataUtil.getString(listDoc, "AGRM_MNNO"));
                // 약정관련자구분코드 10.약정신청인,20.연대보증인,30.SPC연대보증인
                MapDataUtil.setString(docReqPT, "AGRM_RLPR_DSCD", "40");
                // 약정관련자일련번호
                MapDataUtil.setString(docReqPT, "AGRM_RLPR_SRNO", MapDataUtil.getString(listDoc, "AGRM_RLPR_SRNO"));
                // ///////////////////////////////////////////////////////////////////////////////////////////////////////////////////////
                // XMLUtil.setString(docReqPT, "PTNO", 				XMLUtil.getString(listDoc,   "PTNO")); 					//당사자번호
                // XMLUtil.setString(docReqPT, "AGRM_RLPR_DTL_DSCD", 	XMLUtil.getString(listDoc,   "AGRM_RLPR_DTL_DSCD")); 	//약정관련자상세구분코드
                // XMLUtil.setString(docReqPT, "RPPR_POS_CD", 			XMLUtil.getString(listDoc,   "RPPR_POS_CD")); 			//대표자직위코드
                // XMLUtil.setString(docReqPT, "RPPR_POS_CD", 			XMLUtil.getString(listDoc,   "QTRT")); 					//지분율
                // XMLUtil.setString(docReqPT, "QTRT", 				XMLUtil.getString(listDoc,   "QUOT_RNKN")); 			//지분순위
                // XMLUtil.setString(docReqPT, "ZPCD1", 				XMLUtil.getString(listDoc,   "ZPCD1")); 				//우편번호
                // XMLUtil.setString(docReqPT, "AGRM_PRRP_ADRS", 		XMLUtil.getString(listDoc,   "AGRM_PRRP_ADRS")); 		//약정대표자주소
                // XMLUtil.setString(docReqPT, "ASCN_JNNG_YN", 		XMLUtil.getString(listDoc,   "ASCN_JNNG_YN")); 			//조합가입여부
                // XMLUtil.setString(docReqPT, "MRTG_NOAC", 			XMLUtil.getString(listDoc,   "MRTG_NOAC")); 			//담보좌수
                // XMLUtil.setString(docReqPT, "CRRTN_CD", 			XMLUtil.getString(listDoc,   "CRRTN_CD")); 				//신용등급코드
                // XMLUtil.setString(docReqPT, "BSN_PTCP_QTRT", 		XMLUtil.getString(listDoc,   "BSN_PTCP_QTRT")); 		//사업참여지분율
                // XMLUtil.setString(docReqPT, "CNST_PTCP_QTRT", 		XMLUtil.getString(listDoc,   "CNST_PTCP_QTRT")); 		//시공참여지분율
                // XMLUtil.setString(docReqPT, "JNGR_YN", 				XMLUtil.getString(listDoc,   "JNGR_YN")); 				//연대보증여부
                // XMLUtil.setString(docReqPT, "GVSR_DATE", 			XMLUtil.getString(listDoc,   "GVSR_DATE")); 			//입보일자
                // XMLUtil.setString(docReqPT, "ADDT_GVSR_RSN_CNTS",   XMLUtil.getString(listDoc,   "ADDT_GVSR_RSN_CNTS")); 	//입보사유내용
                // XMLUtil.setString(docReqPT, "CNLT_RSN_DSCD", 		XMLUtil.getString(listDoc,   "CNLT_RSN_DSCD")); 		//해지사유구분코드
                // XMLUtil.setString(docReqPT, "APLC_SCR", 			XMLUtil.getString(listDoc,   "APLC_SCR")); 				//적용점수
                // UserSession userSession = (UserSession) ContextUtil.getUserData("userSession");
                // 사번
                MapDataUtil.setString(docReqPT, "LAST_CHNR_ID", UserHeaderUtil.getInstance().getEmpno());
                MapDataUtil.setString(docReqPT, "LAST_CHNG_DTTM", (String) UserHeaderUtil.getInstance().getTimestamp());
                AppLog.info("\n== listDoc.docReqPT =======================");
                AppLog.info("\n" + docReqPT);
                // xda.execute("com.cg.sa.ag.additonextensionmgmt.xda.ag_zag_agmt_rlpr_io3103", docReqPT);
                // xda.execute("com.cg.sa.ag.additonextensionmgmt.xda.ag_zag_agmt_rlpr_io3104", docReqPT);
                AppLog.info("등록이면 I , 수정이면 U :	[" + MapDataUtil.getString(pDoc, "ACTIONMODE") + "]");
                // if(XMLUtil.getString(pDoc, "ACTIONMODE").equals("U")){
                if (MapDataUtil.getString(pDoc, "ACTIONMODE").equals(SAAGConstants.UPDATE)) {
                	// dochy additonExtensionTblBCService.updateZagAgrmRlpr가 없음. / 20221031_해당 메서드 자체를 호출하는 곳이 없음. (사용하지 않는 메서드)
//                    resultCnt = additonExtensionTblBCService.updateZagAgrmRlpr(docReqPT);
                } else {
                	resultCnt = additonExtensionTblBCService.insertZagAgrmRlpr(docReqPT);
                }
            }
            // 채번된 계약관리번호를 넣는다.
            MapDataUtil.setString(result, "AGRM_MNNO", newAgrmMnno);
            AppLog.info("***********************************");
            AppLog.info("등록후 result");
            AppLog.info("***********************************");
            AppLog.info("" + resultCnt);
            AppLog.info("***********************************");
        } catch (ElException e) {
        	AppLog.warn(e.getMessage(), e);
            /**
             * 3.Exception 처리
             *  Framework Level Exception을 catch하여 임의 가공 처리 할 경우 Warning 객체 정의
             *  Exception 객체 상속구조: Throwable<-Exceltion<-Warning<-FrameworkWarning
             */
            throw new CgAppUserException("CG_ERROR", 0, e.getMessage(), "SPLT0003", e);
        }
        AppLog.info("\n== AdditonExtensionBC.insertAdditonGivingSurety end =======================");
        /**
         * 4.결과 반환
         */
        return result;
    }

    /**
     * <<TITLE>>
     * 연대보증인 추가입보서 신청내용을 등록 한다.
     * <<LOGIC>>
     */
    public Map insertAdditonGivingSurety(Map pDoc) throws ElException, Exception {
        Map result = new HashMap();
        int bizOutput = 0;
        
        AppLog.info("======================= insertAdditonGivingSurety(pDoc) =======================\n");
        AppLog.info(pDoc.toString());
        AppLog.info("======================= insertAdditonGivingSurety =======================\n");
        
        try {
            //XDA xda = XDAFactory.getXDA(Constants.KEEP_CONNECTION);

            Map newAgrmMnnoDoc = null;
            Map reqAddtExtn = null;
            Map gualListDoc = null;
            // 약정관리번호
            String newAgrmMnno = "";
            
            /**
             * 2012.01.17 박기석
             * 개별처리인경우는 신규보증서부터 해당되는 모든보증서에 대해 추가입보연장신청내용을 등록해준다.
             */
            if ("1".equals(MapDataUtil.getString(pDoc, "ADDT_GVSR_EXTN_AGRN_MTCD"))) {
                // 연대보증인정보를 미리 가져온다.
                Map listDoc = null;
                Map reqAgrmRlpr = null;
                int srno = 0;
                String agrmRlprDtlDscd = null;
                // 연대보증인정보
                List arryList = (List)pDoc.get("JOINTSURETY_LIST");
                Iterator<Map> itr = null;
                
                // 보증정보를 처리..
                List guasArryList = (List)pDoc.get("GUAS_LIST");
                Iterator<Map> guasItr = guasArryList.iterator();
                
                while (guasItr.hasNext()) {
                    gualListDoc = guasItr.next();

                    // 약정관리번호 채번
                    newAgrmMnnoDoc = agreementRegTblBCService.selectArgmMnno(pDoc);
                    newAgrmMnno = MapDataUtil.getString(newAgrmMnnoDoc, "NEW_AGRM_MNNO");
                    
                    // 추가입보연장 신청내용 등록
                    reqAddtExtn = new HashMap();
                    MapDataUtil.setString(reqAddtExtn, "AGRM_MNNO", newAgrmMnno);
                    MapDataUtil.setString(reqAddtExtn, "AGRM_PTNO", MapDataUtil.getString(pDoc, "AGRM_PTNO"));
                    MapDataUtil.setString(reqAddtExtn, "CNRC_MNNO", MapDataUtil.getString(gualListDoc, "CNRC_MNNO"));
                    MapDataUtil.setString(reqAddtExtn, "GUAS_NO", MapDataUtil.getString(gualListDoc, "GUAS_NO"));
                    MapDataUtil.setString(reqAddtExtn, "ADDT_GVSR_EXTN_AGRN_DATE", MapDataUtil.getString(pDoc, "ADDT_GVSR_EXTN_AGRN_DATE"));
                    MapDataUtil.setString(reqAddtExtn, "ADDT_GVSR_RSN_CNTS", MapDataUtil.getString(pDoc, "ADDT_GVSR_RSN_CNTS"));
                    MapDataUtil.setString(reqAddtExtn, "EXTN_GURT_DLNN_DATE", MapDataUtil.getString(pDoc, "EXTN_GURT_DLNN_DATE"));
                    MapDataUtil.setString(reqAddtExtn, "ADDT_GVSR_EXTN_AGRN_MTCD", MapDataUtil.getString(pDoc, "ADDT_GVSR_EXTN_AGRN_MTCD"));
                    MapDataUtil.setString(reqAddtExtn, "ADDT_GVSR_EXTN_AGRN_DSCD", MapDataUtil.getString(pDoc, "ADDT_GVSR_EXTN_AGRN_DSCD"));
                    MapDataUtil.setString(reqAddtExtn, "CHNG_TRGT_AGRM_MNNO", MapDataUtil.getString(pDoc, "CHNG_TRGT_AGRM_MNNO"));
                    // 최종변경자ID
                    MapDataUtil.setString(reqAddtExtn, "LAST_CHNR_ID", (String) UserHeaderUtil.getInstance().getEmpno());
                    MapDataUtil.setString(reqAddtExtn, "LAST_CHNG_DTTM", (String) UserHeaderUtil.getInstance().getTimestamp());

                    // BSEUtil.executeTask(reqAddtExtn,"com.cg.sa.ag.additonextensionmgmt.bc.AdditonExtensionTblBC", "insertZagAdGvsrExAgrnGaus");
                    AppLog.info("\n reqAddtExtn :: " + reqAddtExtn);
                    bizOutput = comCgSaAgAdditonextensionmgmtAgzagadgvsrexagrnguasDAO.ag_zag_ad_gvsr_ex_agrn_guas_io3104(reqAddtExtn);
                    MapDataUtil.setResult(result, bizOutput);

                    // 연대보증인 등록
                    listDoc = null;
                    reqAgrmRlpr = null;
                    srno = 0;
                    agrmRlprDtlDscd = "";
                    itr = arryList.iterator();
                    
                    while (itr.hasNext()) {
                        srno++;
                        listDoc = itr.next();
                        
                        agrmRlprDtlDscd = MapDataUtil.getString(listDoc, "AGRM_RLPR_DTL_DSCD");
                        agrmRlprDtlDscd = "41";
                        
                        reqAgrmRlpr = new HashMap();
                        // 새로 채번된 약정관리번호
                        MapDataUtil.setString(reqAgrmRlpr, "AGRM_MNNO"			, newAgrmMnno);
                        MapDataUtil.setString(reqAgrmRlpr, "AGRM_RLPR_DSCD"		, SAAGConstants.AGRM_RLPR_DSCD_IN40);
                        MapDataUtil.setString(reqAgrmRlpr, "AGRM_RLPR_SRNO"		, new Integer(srno).toString());
                        MapDataUtil.setString(reqAgrmRlpr, "PTNO"				, MapDataUtil.getString(listDoc, "PTNO"));
                        MapDataUtil.setString(reqAgrmRlpr, "AGRM_RLPR_DTL_DSCD"	, agrmRlprDtlDscd);
                        MapDataUtil.setString(reqAgrmRlpr, "RPPR_POS_CD"		, MapDataUtil.getString(listDoc, "RPPR_POS_CD"));
                        MapDataUtil.setString(reqAgrmRlpr, "QTRT"				, MapDataUtil.getString(listDoc, "QTRT"));
                        MapDataUtil.setString(reqAgrmRlpr, "QUOT_RNKN"			, MapDataUtil.getString(listDoc, "QUOT_RNKN"));
                        MapDataUtil.setString(reqAgrmRlpr, "ZPCD1"				, MapDataUtil.getString(listDoc, "ZPCD1"));
                        MapDataUtil.setString(reqAgrmRlpr, "AGRM_RPPR_ADRS"		, MapDataUtil.getString(listDoc, "AGRM_RPPR_ADRS"));
                        MapDataUtil.setString(reqAgrmRlpr, "JNGR_YN"			, MapDataUtil.getString(listDoc, "JNGR_YN"));
                        MapDataUtil.setString(reqAgrmRlpr, "GVSR_DATE"			, MapDataUtil.getString(pDoc, "ADDT_GVSR_EXTN_AGRN_DATE"));
                        // 최종변경자ID
                        MapDataUtil.setString(reqAgrmRlpr, "LAST_CHNR_ID"		, (String) UserHeaderUtil.getInstance().getEmpno());
                        MapDataUtil.setString(reqAgrmRlpr, "LAST_CHNG_DTTM"		, (String) UserHeaderUtil.getInstance().getTimestamp());
                        
                        // BSEUtil.executeTask(reqAgrmRlpr,"com.cg.sa.ag.additonextensionmgmt.bc.AdditonExtensionTblBC", "insertZagAgrmRlpr");
                        bizOutput = comCgSaAgAdditonextensionmgmtAgzagagmtrlprDAO.ag_zag_agmt_rlpr_io3104(reqAgrmRlpr);
                        MapDataUtil.setResult(result, bizOutput);
                    }
                }
                
                MapDataUtil.setString(result, "AGRM_MNNO", newAgrmMnno); // as-is엔 세팅하는 부분이 없었으나 화면에서 response 값으로 AGRM_MNNO을 받음
                
            } else {
                // 약정관리번호 채번
                newAgrmMnnoDoc = agreementRegTblBCService.selectArgmMnno(pDoc);
                newAgrmMnno = MapDataUtil.getString(newAgrmMnnoDoc, "NEW_AGRM_MNNO");
                
                // 추가입보연장 신청내용 등록
                reqAddtExtn = new HashMap();
                MapDataUtil.setString(reqAddtExtn, "AGRM_MNNO", newAgrmMnno);
                MapDataUtil.setString(reqAddtExtn, "AGRM_PTNO", MapDataUtil.getString(pDoc, "AGRM_PTNO"));
                MapDataUtil.setString(reqAddtExtn, "CNRC_MNNO", MapDataUtil.getString(pDoc, "CNRC_MNNO"));
                MapDataUtil.setString(reqAddtExtn, "GUAS_NO", MapDataUtil.getString(pDoc, "GUAS_NO"));
                MapDataUtil.setString(reqAddtExtn, "ADDT_GVSR_EXTN_AGRN_DATE", MapDataUtil.getString(pDoc, "ADDT_GVSR_EXTN_AGRN_DATE"));
                MapDataUtil.setString(reqAddtExtn, "ADDT_GVSR_RSN_CNTS", MapDataUtil.getString(pDoc, "ADDT_GVSR_RSN_CNTS"));
                MapDataUtil.setString(reqAddtExtn, "EXTN_GURT_DLNN_DATE", MapDataUtil.getString(pDoc, "EXTN_GURT_DLNN_DATE"));
                MapDataUtil.setString(reqAddtExtn, "ADDT_GVSR_EXTN_AGRN_MTCD", MapDataUtil.getString(pDoc, "ADDT_GVSR_EXTN_AGRN_MTCD"));
                MapDataUtil.setString(reqAddtExtn, "ADDT_GVSR_EXTN_AGRN_DSCD", MapDataUtil.getString(pDoc, "ADDT_GVSR_EXTN_AGRN_DSCD"));
                MapDataUtil.setString(reqAddtExtn, "CHNG_TRGT_AGRM_MNNO", MapDataUtil.getString(pDoc, "CHNG_TRGT_AGRM_MNNO"));
                // 최종변경자ID
                MapDataUtil.setString(reqAddtExtn, "LAST_CHNR_ID", (String) UserHeaderUtil.getInstance().getEmpno());
                MapDataUtil.setString(reqAddtExtn, "LAST_CHNG_DTTM", (String) UserHeaderUtil.getInstance().getTimestamp());

                // BSEUtil.executeTask(reqAddtExtn,"com.cg.sa.ag.additonextensionmgmt.bc.AdditonExtensionTblBC", "insertZagAdGvsrExAgrnGaus");
                AppLog.info("\n reqAddtExtn :: " + reqAddtExtn);
                bizOutput = comCgSaAgAdditonextensionmgmtAgzagadgvsrexagrnguasDAO.ag_zag_ad_gvsr_ex_agrn_guas_io3104(reqAddtExtn);
                MapDataUtil.setResult(result, bizOutput);

                // 연대보증인 등록
                Map listDoc = null;
                Map reqAgrmRlpr = null;
                int srno = 0;
                String agrmRlprDtlDscd = "";
                
                List arryList = (List)pDoc.get("JOINTSURETY_LIST");
                Iterator<Map> itr = arryList.iterator();
                
                while (itr.hasNext()) {
                    srno++;
                    listDoc = itr.next();
                    
                    agrmRlprDtlDscd = MapDataUtil.getString(listDoc, "AGRM_RLPR_DTL_DSCD");
                    agrmRlprDtlDscd = "41";
                    
                    reqAgrmRlpr = new HashMap();
                    // 새로 채번된 약정관리번호
                    MapDataUtil.setString(reqAgrmRlpr, "AGRM_MNNO", newAgrmMnno);
                    MapDataUtil.setString(reqAgrmRlpr, "AGRM_RLPR_DSCD", SAAGConstants.AGRM_RLPR_DSCD_IN40);
                    MapDataUtil.setString(reqAgrmRlpr, "AGRM_RLPR_SRNO", new Integer(srno).toString());
                    MapDataUtil.setString(reqAgrmRlpr, "PTNO", MapDataUtil.getString(listDoc, "PTNO"));
                    MapDataUtil.setString(reqAgrmRlpr, "AGRM_RLPR_DTL_DSCD", agrmRlprDtlDscd);
                    MapDataUtil.setString(reqAgrmRlpr, "RPPR_POS_CD", MapDataUtil.getString(listDoc, "RPPR_POS_CD"));
                    MapDataUtil.setString(reqAgrmRlpr, "QTRT", MapDataUtil.getString(listDoc, "QTRT"));
                    MapDataUtil.setString(reqAgrmRlpr, "QUOT_RNKN", MapDataUtil.getString(listDoc, "QUOT_RNKN"));
                    MapDataUtil.setString(reqAgrmRlpr, "ZPCD1", MapDataUtil.getString(listDoc, "ZPCD1"));
                    MapDataUtil.setString(reqAgrmRlpr, "AGRM_RPPR_ADRS", MapDataUtil.getString(listDoc, "AGRM_RPPR_ADRS"));
                    MapDataUtil.setString(reqAgrmRlpr, "JNGR_YN", MapDataUtil.getString(listDoc, "JNGR_YN"));
                    MapDataUtil.setString(reqAgrmRlpr, "GVSR_DATE", MapDataUtil.getString(pDoc, "ADDT_GVSR_EXTN_AGRN_DATE"));
                    // 최종변경자ID
                    MapDataUtil.setString(reqAgrmRlpr, "LAST_CHNR_ID", (String) UserHeaderUtil.getInstance().getEmpno());
                    MapDataUtil.setString(reqAgrmRlpr, "LAST_CHNG_DTTM", (String) UserHeaderUtil.getInstance().getTimestamp());
                    
                    // BSEUtil.executeTask(reqAgrmRlpr,"com.cg.sa.ag.additonextensionmgmt.bc.AdditonExtensionTblBC", "insertZagAgrmRlpr");
                    bizOutput = comCgSaAgAdditonextensionmgmtAgzagagmtrlprDAO.ag_zag_agmt_rlpr_io3104(reqAgrmRlpr);
                    MapDataUtil.setResult(result, bizOutput);
                }
                
                MapDataUtil.setString(result, "AGRM_MNNO", newAgrmMnno); // as-is엔 세팅하는 부분이 없었으나 화면에서 response 값으로 AGRM_MNNO을 받음
            }
        } catch (ElException e) {
            AppLog.warn(e.getMessage(), e);
            throw new CgAppUserException("CG_ERROR", 0, e.getMessage(), "SPLT0003", e);
        }
        
        return result;
    }

    /**
     * <<TITLE>>
     * 연대보증인 동의서 신청내용을 등록 한다
     * <<LOGIC>>
     * 1. 연대보증인 동의서 신청내용을 검증한다.
     * 2. 연대보증인 동의서 신청내용을 등록한다.
     * 2.1 추가입보연장동의등록 테이블을 등록한다.
     * >com.cg.sa.ag.additonextensionmgmt.bc.AdditonExtensionTblBC.insertZagAdGvsrExAgrnAplt
     * 2.2 추가입보연장동의대상보증서 테이블을 등록한다.
     * > IF (추가입보연정동의방법코드 == 개별) {
     * >com.cg.sa.ag.additonextensionmgmt.bc.AdditonExtensionTblBC.insertZagAdGvsrExAgrnApGaus
     * > }
     * 2.3 추가입보연장동의연대보증인 테이블을 등록한다.
     * > LOOP(i <= size(연장동의연대보증인수)) {
     * >com.cg.sa.ag.additonextensionmgmt.bc.AdditonExtensionTblBC.selectZagAdGvsrExAgrnApJnsr
     * > }
     * 3.결과리턴
     * @param pDoc
     * @return
     * @throws Exception
     */
    public Map insertExtensionAgreement(Map pDoc) throws ElException, Exception {
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
            //result = xda.execute("[ XDAID를 입력합니다]", pDoc);
        } catch (ElException e) {
        	AppLog.warn(e.getMessage(), e);
            /**
             * 3.Exception 처리
             *  Framework Level Exception을 catch하여 임의 가공 처리 할 경우 Warning 객체 정의
             *  Exception 객체 상속구조: Throwable<-Exceltion<-Warning<-FrameworkWarning
             */
            throw new CgAppUserException("CG_ERROR", 0, e.getMessage(), CodeUtil.getCodeValue("[코드항목]", "[코드카테고리]", "[에러코드번호]"), e);
        }
        /**
         * 4.결과 반환
         */
        return result;
    }

    /**
     * <<TITLE>>
     * 연대보증인 동의서 신청내용을 수정 한다
     * <<LOGIC>>
     * 1. 연대보증인 동의서 신청내용을 검증한다.
     * 2. 연대보증인 동의서 신청내용을 수정한다.
     * 2.1 추가입보연장동의등록 테이블을 수정한다.
     * >com.cg.sa.ag.additonextensionmgmt.bc.AdditonExtensionTblBC.updateZagAdGvsrExAgrnAplt
     * 2.2 추가입보연장동의대상보증서 테이블을 수정한다.
     * > IF (추가입보연정동의방법코드 == 개별) {
     * >com.cg.sa.ag.additonextensionmgmt.bc.AdditonExtensionTblBC.updateZagAdGvsrExAgrnApGaus
     * > }
     * 2.3 추가입보연장동의 연대보증인 테이블을 등록한다.
     * > 1) 기등록된 연대보증인을 삭제한다.
     * >com.cg.sa.ag.additonextensionmgmt.bc.AdditonExtensionTblBC.deleteZagAdGvsrExAgrnApJnsrAll
     * > 2) 연장동의한 연대보증인을 등록한다.
     * > LOOP(i <= size(연장동의연대보증인수)) {
     * >com.cg.sa.ag.additonextensionmgmt.bc.AdditonExtensionTblBC.insertZagAdGvsrExAgrnApJnsr
     * > }
     * 3.결과리턴
     * @param pDoc
     * @return
     * @throws Exception
     */
    public int updateExtensionAgreement(Map pDoc) throws ElException, Exception {
        /**
         * 1.Document 변수의 정의
         *
         * XDA 결과 변수 result
         */
        
//        int result = null;
        int result = 0;
        Map bizInput = null;
        Map bizOutput = null;
        
        AppLog.info("======================= updateExtensionAgreement(pDoc) =======================\n");
        AppLog.info(pDoc.toString());
        AppLog.info("======================= updateExtensionAgreement =======================\n");
        
        try {
            //XDA xda = XDAFactory.getXDA(Constants.KEEP_CONNECTION);
            
            /*
			 * 2012.01.27 박기석
			 * 개별처리건인 경우에는 해당되는 모든보증서에 대해 추가입보연장동의서에 insert했기에 아래와 같이 전부 찾아서 update 해준다. 
			 */
            if ("1".equals(MapDataUtil.getString(pDoc, "ADDT_GVSR_EXTN_AGRN_MTCD"))) {
                // 연대보증인조회 먼저처리
                String lAgrmMnno = null;
                List aryList = (List)pDoc.get("JOINTSURETY_LIST");
                
                Map listDoc = null;
                Map reqAgrmRlpr = null;
                int srno = 0;
                String agrmRlprDtlDscd = "";
                Iterator<Map> itr = null;
                // 보증정보조회..
                Map gualListDoc = null;
                
                List guasArryList = (List)pDoc.get("GUAS_LIST");
                Iterator<Map> guasItr = guasArryList.iterator();
                
                while (guasItr.hasNext()) {
                    gualListDoc = guasItr.next();

                    // 약정관리번호를 알아온다.
                    bizInput = new HashMap();
                    MapDataUtil.setString(bizInput, "CNRC_MNNO", MapDataUtil.getString(gualListDoc, "CNRC_MNNO"));
                    bizOutput = comCgSaAgAdditonextensionmgmtAgzagaddtextnDAO.ag_zag_addt_extn_so3036(bizInput);

                    // 조회된 약정관리번호를 셋팅
                    MapDataUtil.setString(pDoc, "AGRM_MNNO", MapDataUtil.getString(bizOutput, "AGRM_MNNO"));

                    // 추가 입보연장동의  수정
                    result = additonExtensionTblBCService.updateZagAddtExtn(pDoc);

                    // 연대보증인삭제
                    result = comCgSaAgAdditonextensionmgmtAgzagagmtrlprDAO.ag_zag_agmt_rlpr_do3102(pDoc);

                    // 연대보증인등록
                    lAgrmMnno = MapDataUtil.getString(pDoc, "AGRM_MNNO");
                    aryList = (List)pDoc.get("JOINTSURETY_LIST");
                    
                    listDoc = null;
                    reqAgrmRlpr = null;
                    srno = 0;
                    agrmRlprDtlDscd = "";
                    
                    itr = aryList.iterator();
                    
                    while (itr.hasNext()) {
                        srno++;
                        listDoc = itr.next();
                        
                        agrmRlprDtlDscd = MapDataUtil.getString(listDoc, "AGRM_RLPR_DTL_DSCD");
                        agrmRlprDtlDscd = "41";
                        
                        reqAgrmRlpr = new HashMap();
                        // 신규약정관리번호(추가입보연장동의)
                        MapDataUtil.setString(reqAgrmRlpr, "AGRM_MNNO", lAgrmMnno);
                        // 약정관련자구분코드 10.약정신청인,20.연대보증인,30.SPC연대보증인
                        MapDataUtil.setString(reqAgrmRlpr, "AGRM_RLPR_DSCD", SAAGConstants.AGRM_RLPR_DSCD_IN40);
                        // 약정관련자일련번호
                        MapDataUtil.setString(reqAgrmRlpr, "AGRM_RLPR_SRNO", new Integer(srno).toString());
                        // 당사자번호
                        MapDataUtil.setString(reqAgrmRlpr, "PTNO", MapDataUtil.getString(listDoc, "PTNO"));
                        // 약정관련자상세구분코드
                        MapDataUtil.setString(reqAgrmRlpr, "AGRM_RLPR_DTL_DSCD", agrmRlprDtlDscd);
                        // 대표자직위코드
                        MapDataUtil.setString(reqAgrmRlpr, "RPPR_POS_CD", MapDataUtil.getString(listDoc, "RPPR_POS_CD"));
                        // 지분율
                        MapDataUtil.setString(reqAgrmRlpr, "QTRT", MapDataUtil.getString(listDoc, "QTRT"));
                        // 지분순위
                        MapDataUtil.setString(reqAgrmRlpr, "QUOT_RNKN", MapDataUtil.getString(listDoc, "QUOT_RNKN"));
                        // 우편번호
                        MapDataUtil.setString(reqAgrmRlpr, "ZPCD1", MapDataUtil.getString(listDoc, "ZPCD1"));
                        // 약정대표자주소
                        MapDataUtil.setString(reqAgrmRlpr, "AGRM_RPPR_ADRS", MapDataUtil.getString(listDoc, "AGRM_RPPR_ADRS"));
                        // 조합가입여부
                        MapDataUtil.setString(reqAgrmRlpr, "ASCN_JNNG_YN", MapDataUtil.getString(listDoc, "ASCN_JNNG_YN"));
                        // 담보좌수
                        MapDataUtil.setString(reqAgrmRlpr, "MRTG_NOAC", MapDataUtil.getString(listDoc, "MRTG_NOAC"));
                        // 신용등급코드
                        MapDataUtil.setString(reqAgrmRlpr, "CRRTN_CD", MapDataUtil.getString(listDoc, "CRRTN_CD"));
                        // 사업참여지분율
                        MapDataUtil.setString(reqAgrmRlpr, "BSN_PTCP_QTRT", MapDataUtil.getString(listDoc, "BSN_PTCP_QTRT"));
                        // 시공참여지분율
                        MapDataUtil.setString(reqAgrmRlpr, "CNST_PTCP_QTRT", MapDataUtil.getString(listDoc, "CNST_PTCP_QTRT"));
                        // 연대보증여부
                        MapDataUtil.setString(reqAgrmRlpr, "JNGR_YN", MapDataUtil.getString(listDoc, "JNGR_YN"));
                        // 입보일자
                        MapDataUtil.setString(reqAgrmRlpr, "GVSR_DATE", MapDataUtil.getString(pDoc, "ADDT_GVSR_EXTN_AGRN_DATE"));
                        // 입보사유내용
                        MapDataUtil.setString(reqAgrmRlpr, "ADDT_GVSR_RSN_CNTS", MapDataUtil.getString(listDoc, "ADDT_GVSR_RSN_CNTS"));
                        // 해지사유구분코드
                        MapDataUtil.setString(reqAgrmRlpr, "CNLT_RSN_DSCD", MapDataUtil.getString(listDoc, "CNLT_RSN_DSCD"));
                        // 적용점수
                        MapDataUtil.setString(reqAgrmRlpr, "APLC_SCR", MapDataUtil.getString(listDoc, "APLC_SCR"));
                        // 최종변경자ID
                        MapDataUtil.setString(reqAgrmRlpr, "LAST_CHNR_ID", (String) UserHeaderUtil.getInstance().getEmpno());
                        MapDataUtil.setString(reqAgrmRlpr, "LAST_CHNG_DTTM", (String) UserHeaderUtil.getInstance().getTimestamp());

                        // result = BSEUtil.executeTask(reqAgrmRlpr,"com.cg.sa.ag.additonextensionmgmt.bc.AdditonExtensionTblBC", "insertZagAgrmRlpr");
                        result = comCgSaAgAdditonextensionmgmtAgzagagmtrlprDAO.ag_zag_agmt_rlpr_io3104(reqAgrmRlpr);
                    }
                }
            } else {
                // 추가 입보연장동의  수정
                result = additonExtensionTblBCService.updateZagAddtExtn(pDoc);

                // 연대보증인삭제
                result = comCgSaAgAdditonextensionmgmtAgzagagmtrlprDAO.ag_zag_agmt_rlpr_do3102(pDoc);

                // 연대보증인등록
                String lAgrmMnno = MapDataUtil.getString(pDoc, "AGRM_MNNO");
                List aryList = (List)pDoc.get("JOINTSURETY_LIST");
                
                Map listDoc = null;
                Map reqAgrmRlpr = null;
                int srno = 0;
                String agrmRlprDtlDscd = "";
                
                Iterator<Map> itr = aryList.iterator();
                
                while (itr.hasNext()) {
                    srno++;
                    listDoc = itr.next();
                
                    agrmRlprDtlDscd = MapDataUtil.getString(listDoc, "AGRM_RLPR_DTL_DSCD");
                    agrmRlprDtlDscd = "41";
                    
                    reqAgrmRlpr = new HashMap();
                    // 신규약정관리번호(추가입보연장동의)
                    MapDataUtil.setString(reqAgrmRlpr, "AGRM_MNNO", lAgrmMnno);
                    // 약정관련자구분코드 10.약정신청인,20.연대보증인,30.SPC연대보증인
                    MapDataUtil.setString(reqAgrmRlpr, "AGRM_RLPR_DSCD", SAAGConstants.AGRM_RLPR_DSCD_IN40);
                    // 약정관련자일련번호
                    MapDataUtil.setString(reqAgrmRlpr, "AGRM_RLPR_SRNO", new Integer(srno).toString());
                    // 당사자번호
                    MapDataUtil.setString(reqAgrmRlpr, "PTNO", MapDataUtil.getString(listDoc, "PTNO"));
                    // 약정관련자상세구분코드
                    MapDataUtil.setString(reqAgrmRlpr, "AGRM_RLPR_DTL_DSCD", agrmRlprDtlDscd);
                    // 대표자직위코드
                    MapDataUtil.setString(reqAgrmRlpr, "RPPR_POS_CD", MapDataUtil.getString(listDoc, "RPPR_POS_CD"));
                    // 지분율
                    MapDataUtil.setString(reqAgrmRlpr, "QTRT", MapDataUtil.getString(listDoc, "QTRT"));
                    // 지분순위
                    MapDataUtil.setString(reqAgrmRlpr, "QUOT_RNKN", MapDataUtil.getString(listDoc, "QUOT_RNKN"));
                    // 우편번호
                    MapDataUtil.setString(reqAgrmRlpr, "ZPCD1", MapDataUtil.getString(listDoc, "ZPCD1"));
                    // 약정대표자주소
                    MapDataUtil.setString(reqAgrmRlpr, "AGRM_RPPR_ADRS", MapDataUtil.getString(listDoc, "AGRM_RPPR_ADRS"));
                    // 조합가입여부
                    MapDataUtil.setString(reqAgrmRlpr, "ASCN_JNNG_YN", MapDataUtil.getString(listDoc, "ASCN_JNNG_YN"));
                    // 담보좌수
                    MapDataUtil.setString(reqAgrmRlpr, "MRTG_NOAC", MapDataUtil.getString(listDoc, "MRTG_NOAC"));
                    // 신용등급코드
                    MapDataUtil.setString(reqAgrmRlpr, "CRRTN_CD", MapDataUtil.getString(listDoc, "CRRTN_CD"));
                    // 사업참여지분율
                    MapDataUtil.setString(reqAgrmRlpr, "BSN_PTCP_QTRT", MapDataUtil.getString(listDoc, "BSN_PTCP_QTRT"));
                    // 시공참여지분율
                    MapDataUtil.setString(reqAgrmRlpr, "CNST_PTCP_QTRT", MapDataUtil.getString(listDoc, "CNST_PTCP_QTRT"));
                    // 연대보증여부
                    MapDataUtil.setString(reqAgrmRlpr, "JNGR_YN", MapDataUtil.getString(listDoc, "JNGR_YN"));
                    // 입보일자
                    MapDataUtil.setString(reqAgrmRlpr, "GVSR_DATE", MapDataUtil.getString(pDoc, "ADDT_GVSR_EXTN_AGRN_DATE"));
                    // 입보사유내용
                    MapDataUtil.setString(reqAgrmRlpr, "ADDT_GVSR_RSN_CNTS", MapDataUtil.getString(listDoc, "ADDT_GVSR_RSN_CNTS"));
                    // 해지사유구분코드
                    MapDataUtil.setString(reqAgrmRlpr, "CNLT_RSN_DSCD", MapDataUtil.getString(listDoc, "CNLT_RSN_DSCD"));
                    // 적용점수
                    MapDataUtil.setString(reqAgrmRlpr, "APLC_SCR", MapDataUtil.getString(listDoc, "APLC_SCR"));
                    // 최종변경자ID
                    MapDataUtil.setString(reqAgrmRlpr, "LAST_CHNR_ID", (String) UserHeaderUtil.getInstance().getEmpno());
                    MapDataUtil.setString(reqAgrmRlpr, "LAST_CHNG_DTTM", (String) UserHeaderUtil.getInstance().getTimestamp());

                    // result = BSEUtil.executeTask(reqAgrmRlpr,"com.cg.sa.ag.additonextensionmgmt.bc.AdditonExtensionTblBC", "insertZagAgrmRlpr");
                    result = comCgSaAgAdditonextensionmgmtAgzagagmtrlprDAO.ag_zag_agmt_rlpr_io3104(reqAgrmRlpr);
                }
            }
        } catch (ElException e) {
        	AppLog.warn(e.getMessage(), e);
            /**
             * 3.Exception 처리
             *  Framework Level Exception을 catch하여 임의 가공 처리 할 경우 Warning 객체 정의
             *  Exception 객체 상속구조: Throwable<-Exceltion<-Warning<-FrameworkWarning
             */
            throw new CgAppUserException("CG_ERROR", 0, e.getMessage(), CodeUtil.getCodeValue("[코드항목]", "[코드카테고리]", "[에러코드번호]"), e);
        }
        
        /**
         * 4.결과 반환
         */
        return result;
    }

    /**
     * <<TITLE>>
     * 연대보증인 추가입보서 신청내용을 수정 한다.
     * <<LOGIC>>
     * 1. 연대보증인 추가입보서 신청내용을 검증한다.
     * 2. 연대보증인 추가입보서 신청내용을 수정한다.
     * 2.1 추가입보연장동의등록 테이블을 수정한다.
     * >com.cg.sa.ag.additonextensionmgmt.bc.AdditonExtensionTblBC.updateZagAdGvsrExAgrnAplt
     * 2.2 추가입보연장동의대상보증서 테이블을 수정한다.
     * > IF (추가입보연정동의방법코드 == 개별) {
     * >com.cg.sa.ag.additonextensionmgmt.bc.AdditonExtensionTblBC.updateZagAdGvsrExAgrnApGaus
     * > }
     * 2.3 추가입보연장동의연대보증인 테이블을 등록한다.
     * > 1) 기등록된 연대보증인을 삭제한다.
     * >com.cg.sa.ag.additonextensionmgmt.bc.AdditonExtensionTblBC.deleteZagAdGvsrExAgrnApJnsrAll
     * > 2) 추가입보한 연대보증인을 등록한다.
     * > LOOP(i <= size(추가입보한연대보증인수)) {
     * >com.cg.sa.ag.additonextensionmgmt.bc.AdditonExtensionTblBC.insertZagAdGvsrExAgrnApJnsr
     * > }
     * 3.결과리턴
     * @param pDoc
     * @return
     * @throws Exception
     */
    public Map updateAdditonGivingSurety(Map pDoc) throws ElException, Exception {
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
            //result = xda.execute("[ XDAID를 입력합니다]", pDoc);
        } catch (ElException e) {
        	AppLog.warn(e.getMessage(), e);
            /**
             * 3.Exception 처리
             *  Framework Level Exception을 catch하여 임의 가공 처리 할 경우 Warning 객체 정의
             *  Exception 객체 상속구조: Throwable<-Exceltion<-Warning<-FrameworkWarning
             */
            throw new CgAppUserException("CG_ERROR", 0, e.getMessage(), CodeUtil.getCodeValue("[코드항목]", "[코드카테고리]", "[에러코드번호]"), e);
        }
        /**
         * 4.결과 반환
         */
        return result;
    }

    /**
     * <<TITLE>>
     * 연대보증인 추가입보 및 동의서 신청내용을 삭제 한다
     * <<LOGIC>>
     * 1. 추가입보연장동의등록 테이블 삭제처리를 한다.
     * > com.cg.sa.ag.additonextensionmgmt.bc.AdditonExtensionTblBC.deleteZagAdGvsrExAgrnAplt
     * 2. 추가입보연장동의연대보증인 테이블 삭제  처리를 한다.
     * > com.cg.sa.ag.additonextensionmgmt.bc.AdditonExtensionTblBC.deleteZagAdGvsrExAgrnApJnsr
     * 3. 추가입보연장동의보증서 테이블 삭제 처리를 한다.
     * > com.cg.sa.ag.additonextensionmgmt.bc.AdditonExtensionTblBC.deleteZagAdGvsrExAgrnApGaus
     * 4. 결과리턴
     * @param pDoc
     * @return
     * @throws Exception
     */
    public int deleteAdditionExtension(Map pDoc) throws ElException, Exception {
        /**
         * 1.Document 변수의 정의
         *
         * XDA 결과 변수 result
         */
        int result = 0;
        Map bizInput = null;
        Map bizOutput = null;
        
        AppLog.info("\n== AdditonExtensionBC.deleteAdditionExtension start =======================");
        AppLog.info("\n== pDoc =======================");
        AppLog.info("\n" + pDoc);
        
        try {
            /**
             * 2.XDA를 실행합니다.
             * 호출하려는 XDAID를 입력합니다.
             */
            //XDA xda = XDAFactory.getXDA(Constants.KEEP_CONNECTION);
            /*
			 * 2012.01.27 박기석
			 * 개별처리건인 경우에는 해당되는 모든보증서에 대해 추가입보연장동의서에 insert했기에 아래와 같이 전부 찾아서 update 해준다. 
			 */
            if ("1".equals(MapDataUtil.getString(pDoc, "ADDT_GVSR_EXTN_AGRN_MTCD"))) {
                // 보증정보조회
                Map gualListDoc = null;
                List guasArryList = (List)pDoc.get("GUAS_LIST");
                Iterator<Map> guasItr = guasArryList.iterator();
                
                while (guasItr.hasNext()) {
                    gualListDoc = guasItr.next();
                
                    // 약정관리번호를 알아온다.
                    bizInput = new HashMap();
                    MapDataUtil.setString(bizInput, "CNRC_MNNO", MapDataUtil.getString(gualListDoc, "CNRC_MNNO"));
                    bizOutput = comCgSaAgAdditonextensionmgmtAgzagaddtextnDAO.ag_zag_addt_extn_so3036(bizInput);

                    // 조회된 약정관리번호를 셋팅
                    MapDataUtil.setString(pDoc, "AGRM_MNNO", MapDataUtil.getString(bizOutput, "AGRM_MNNO"));

                    // 연대보증인동의서등록_약정관련인 삭제
                    result = comCgSaAgAdditonextensionmgmtAgzagagmtrlprDAO.ag_zag_agmt_rlpr_do3102(pDoc);

                    // 연대보증인동의서등록_연장동의보증서 삭제
                    result = comCgSaAgAdditonextensionmgmtAgzagadgvsrexagrnguasDAO.ag_zag_ad_gvsr_ex_agrn_guas_do3101(pDoc);
                }
            } else {
                // 연대보증인동의서등록_약정관련인 삭제
                result = comCgSaAgAdditonextensionmgmtAgzagagmtrlprDAO.ag_zag_agmt_rlpr_do3102(pDoc);

                // 연대보증인동의서등록_연장동의보증서 삭제
                result = comCgSaAgAdditonextensionmgmtAgzagadgvsrexagrnguasDAO.ag_zag_ad_gvsr_ex_agrn_guas_do3101(pDoc);
            }
        } catch (ElException e) {
        	AppLog.warn(e.getMessage(), e);
            /**
             * 3.Exception 처리
             *  Framework Level Exception을 catch하여 임의 가공 처리 할 경우 Warning 객체 정의
             *  Exception 객체 상속구조: Throwable<-Exceltion<-Warning<-FrameworkWarning
             */
            throw new CgAppUserException("CG_ERROR", 0, e.getMessage(), "SPLT0003", e);
        }
        
        AppLog.info("\n== AdditonExtensionBC.deleteAdditionExtension end =======================");
        
        /**
         * 4.결과 반환
         */
        return result;
    }

    @Resource(name = "custMgmtSCServiceImpl")
    private com.cg.cu.cb.customermgmt.service.CustMgmtSCService custMgmtSCService;

    @Resource(name = "guasInfmInqrSCServiceImpl")
    private com.cg.sa.gu.guasinfminqr.service.GuasInfmInqrSCService guasInfmInqrSCService;

    @Resource(name = "additonExtensionTblBCServiceImpl")
    private com.cg.sa.ag.additonextensionmgmt.service.AdditonExtensionTblBCService additonExtensionTblBCService;

    @Resource(name = "gurtPartyMgmtSCServiceImpl")
    private com.cg.sa.gu.gurtpartymgmt.service.GurtPartyMgmtSCService gurtPartyMgmtSCService;

    @Resource(name = "agreementInfoMgmtSCServiceImpl")
    private com.cg.sa.ag.agreementinfomgmt.service.AgreementInfoMgmtSCService agreementInfoMgmtSCService;
    
    @Resource(name = "comCgSaAgAdditonextensionmgmtAgzagagmtDAO")
    private com.cg.sa.ag.additonextensionmgmt.dao.ComCgSaAgAdditonextensionmgmtAgzagagmtDAO comCgSaAgAdditonextensionmgmtAgzagagmtDAO;

    @Resource(name = "comCgSaAgAdditonextensionmgmtAgzagagrmrlprDAO")
    private com.cg.sa.ag.additonextensionmgmt.dao.ComCgSaAgAdditonextensionmgmtAgzagagrmrlprDAO comCgSaAgAdditonextensionmgmtAgzagagrmrlprDAO;

    @Resource(name = "comCgSaAgAdditonextensionmgmtAgzagaddtextnDAO")
    private com.cg.sa.ag.additonextensionmgmt.dao.ComCgSaAgAdditonextensionmgmtAgzagaddtextnDAO comCgSaAgAdditonextensionmgmtAgzagaddtextnDAO;

    @Resource(name = "comCgSaAgAgreementinfomgmtAgzagagmtDAO")
    private com.cg.sa.ag.agreementinfomgmt.dao.ComCgSaAgAgreementinfomgmtAgzagagmtDAO comCgSaAgAgreementinfomgmtAgzagagmtDAO;

    @Resource(name = "comCgSaAgAdditonextensionmgmtAgzagagrmrlptDAO")
    private com.cg.sa.ag.additonextensionmgmt.dao.ComCgSaAgAdditonextensionmgmtAgzagagrmrlptDAO comCgSaAgAdditonextensionmgmtAgzagagrmrlptDAO;

    @Resource(name = "agreementRegTblBCServiceImpl")
    private com.cg.sa.ag.agreementregmgmt.service.AgreementRegTblBCService agreementRegTblBCService;

    @Resource(name = "comCgSaAgAdditonextensionmgmtAgzagadgvsrexagrnguasDAO")
    private com.cg.sa.ag.additonextensionmgmt.dao.ComCgSaAgAdditonextensionmgmtAgzagadgvsrexagrnguasDAO comCgSaAgAdditonextensionmgmtAgzagadgvsrexagrnguasDAO;

    @Resource(name = "comCgSaAgAdditonextensionmgmtAgzagagmtrlprDAO")
    private com.cg.sa.ag.additonextensionmgmt.dao.ComCgSaAgAdditonextensionmgmtAgzagagmtrlprDAO comCgSaAgAdditonextensionmgmtAgzagagmtrlprDAO;
}