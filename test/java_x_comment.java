
package com.cg.sa.ag.additonextensionmgmt.service.impl;

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

@SuppressWarnings({ "rawtypes", "unchecked" })
@Service("additonExtensionBCServiceImpl")
public class AdditonExtensionBCServiceImpl implements AdditonExtensionBCService {
    
    public Map admitAdditionExtension(Map pDoc) throws ElException, Exception {
        
        Map result = null;
        try {
            
        } catch (ElException e) {
        	AppLog.warn(e.getMessage(), e);
            
            throw new CgAppUserException("CG_ERROR", 0, e.getMessage(), CodeUtil.getCodeValue("[코드항목]", "[코드카테고리]", "[에러코드번호]"), e);
        }
        
        return result;
    }
    
    public Map approveAdditionExtension(Map pDoc) throws ElException, Exception {
        
        Map result = null;
        try {
            
        } catch (ElException e) {
        	AppLog.warn(e.getMessage(), e);
            
            throw new CgAppUserException("CG_ERROR", 0, e.getMessage(), CodeUtil.getCodeValue("[코드항목]", "[코드카테고리]", "[에러코드번호]"), e);
        }
        
        return result;
    }
    
    public Map selectAdditonGivingSuretybyPK_OLD(Map pDoc) throws ElException, Exception {
        
        Map result = new HashMap();
        Map docRequest = new HashMap();
        Map docGuas = new HashMap();
        Map docAgmt = new HashMap();
        Map docOrignSurety = new HashMap();
        Map docOrignSuretyTwo = new HashMap();
        Map docAddSurety = new HashMap();
        Map listDoc = null;
        try {
            docRequest = new HashMap();
            MapDataUtil.setString(docRequest, "CUST_INQR_DSCD", "IA01");
            MapDataUtil.setString(docRequest, "CUST_INQR_COND_DSCD", MapDataUtil.getString(pDoc, "CUST_INQR_COND_DSCD"));
            MapDataUtil.setString(docRequest, "SRCH_KWRD", MapDataUtil.getString(pDoc, "AMNO"));
            
            result = MapDataUtil.getMap(custMgmtSCService.selectCustInfo(docRequest), "PRTY_BASC");
            if (MapDataUtil.getString(pDoc, "AMNO") == "") {
                String[] saveStatus = new String[] { "조합원번호" };
                throw new CgAppUserException("CG_ERROR", 0, CodeUtil.getCodeValue("CGMsgCode", "I", "I03000", saveStatus), "I03000");
            }
            Map custResult = null;
            custResult = new HashMap();
            custResult.put("RPL", result.get("RSOA_LIST"));
            result = new HashMap();
            String lZagAddtExtnAgrmMnno = "";
            if (MapDataUtil.getString(pDoc, "ADDT_GVSR_EXTN_AGRN_MTCD").equals(SAAGConstants.ADDT_GVSR_EXTN_AGRN_MTCD_1)) {
                docRequest = new HashMap();
                MapDataUtil.setString(docRequest, "CNRC_MNNO", MapDataUtil.getString(pDoc, "CNRC_MNNO"));
                docGuas = guasInfmInqrSCService.selectGuaranteeSheetbyPK(docRequest);
                MapDataUtil.setString(pDoc, "AGRM_MNNO", MapDataUtil.getString(docGuas, "AGRM_MNNO"));
                Map getZagAddtExtn = additonExtensionTblBCService.selectZagAdGvsrExAgrnApGaus(docGuas);
                int resultOneInt = Integer.parseInt(MapDataUtil.getAttribute(getZagAddtExtn, "result"));
                if (resultOneInt > 0) {
                    MapDataUtil.setString(docGuas, "ADDT_GVSR_EXTN_AGRN_DATE", MapDataUtil.getString(getZagAddtExtn, "ADDT_GVSR_EXTN_AGRN_DATE"));
                    MapDataUtil.setString(docGuas, "ADDT_GVSR_RSN_CNTS", MapDataUtil.getString(getZagAddtExtn, "ADDT_GVSR_RSN_CNTS"));
                    MapDataUtil.setString(docGuas, "EXTN_GURT_DLNN_DATE", MapDataUtil.getString(getZagAddtExtn, "EXTN_GURT_DLNN_DATE"));
                    lZagAddtExtnAgrmMnno = MapDataUtil.getString(getZagAddtExtn, "AGRM_MNNO");
                    MapDataUtil.setString(docGuas, "NEW_AGRM_MNNO", lZagAddtExtnAgrmMnno);
                } else {
                }
                
                docRequest = new HashMap();
                MapDataUtil.setString(docRequest, "CNRC_MNNO", MapDataUtil.getString(pDoc, "CNRC_MNNO"));
                MapDataUtil.setString(docRequest, "PATY_TPCD", "500");
                docOrignSurety = gurtPartyMgmtSCService.selectGurtParty(docRequest);
                MapDataUtil.setString(docRequest, "PATY_TPCD", "600");
                docOrignSuretyTwo = gurtPartyMgmtSCService.selectGurtParty(docRequest);
                List aryList 	= (List)docOrignSurety.get(GUUtil.ATTRIBUTE_RESULT);
                List aryListTwo	= (List)docOrignSuretyTwo.get(GUUtil.ATTRIBUTE_RESULT);
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
                result.putAll(docGuas);
                result.put("LIST", docOrignSurety);
                docRequest = new HashMap();
                MapDataUtil.setString(docRequest, "AGRM_MNNO", MapDataUtil.getString(pDoc, "AGRM_MNNO"));
                MapDataUtil.setString(docRequest, "CHYN_AGRM_MNNO", MapDataUtil.getString(pDoc, "AGRM_MNNO"));
                MapDataUtil.setString(docRequest, "CHYN_AGRM_RLPR_DSCD", "20");
                docAgmt = agreementInfoMgmtSCService.selectAgreementDtlbyPK(docRequest);
            }
            if (MapDataUtil.getString(pDoc, "ADDT_GVSR_EXTN_AGRN_MTCD").equals(SAAGConstants.ADDT_GVSR_EXTN_AGRN_MTCD_2)) {
                docAgmt = additonExtensionTblBCService.selectZagAdGvsrExAgrnApJnsrAll(pDoc);
                List<Map> rplOutput = additonExtensionTblBCService.selectZagAgrmRlpr(pDoc);
                result.put("LIST", rplOutput);
                docAgmt.put("RPL", rplOutput);
                if (MapDataUtil.getAttribute(docAgmt, "result").equals(SAAGConstants.RESULT_1)) {
                } else {
                    docRequest = new HashMap();
                    MapDataUtil.setString(docRequest, "AGRM_MNNO", MapDataUtil.getString(pDoc, "AGRM_MNNO"));
                    MapDataUtil.setString(docRequest, "CHYN_AGRM_MNNO", MapDataUtil.getString(pDoc, "AGRM_MNNO"));
                    MapDataUtil.setString(docRequest, "CHYN_AGRM_RLPR_DSCD", "20");
                    docAgmt = comCgSaAgAdditonextensionmgmtAgzagagmtDAO.ag_zag_agmt_so1504(docRequest);
                    ArrayList<Map> rplOutListSAGU = comCgSaAgAdditonextensionmgmtAgzagagrmrlprDAO.ag_zag_agrm_rlpr_so1508(docRequest);
                    result.put("LIST", rplOutListSAGU);
                    ArrayList<Map> rplOut = comCgSaAgAdditonextensionmgmtAgzagagrmrlprDAO.ag_zag_agrm_rlpr_so1507(docRequest);
                    docAgmt.put("RPL", rplOut);
                }
                result.put("LIST1", docAgmt.get("RPL"));
            }
            result.putAll(docAgmt);
            
            if (MapDataUtil.getString(pDoc, "ADDT_GVSR_EXTN_AGRN_DSCD").equals(SAAGConstants.ADDT_GVSR_EXTN_AGRN_DSCD_2) || MapDataUtil.getString(pDoc, "ADDT_GVSR_EXTN_AGRN_DSCD").equals(SAAGConstants.ADDT_GVSR_EXTN_AGRN_DSCD_3)) {
                result.put("LIST1", docAgmt.get("RPL"));
            }
            if (MapDataUtil.getString(pDoc, "ADDT_GVSR_EXTN_AGRN_DSCD").equals(SAAGConstants.ADDT_GVSR_EXTN_AGRN_DSCD_1)) {
                if ((lZagAddtExtnAgrmMnno != "") && (lZagAddtExtnAgrmMnno != null)) {
                    Map inputZagAgrmRlpr = null;
                    inputZagAgrmRlpr = new HashMap();
                    MapDataUtil.setString(inputZagAgrmRlpr, "AGRM_MNNO", MapDataUtil.getString(docGuas, "NEW_AGRM_MNNO"));
                    List<Map> rplOutput = additonExtensionTblBCService.selectZagAgrmRlprMsg(inputZagAgrmRlpr);
                    inputZagAgrmRlpr = new HashMap();
                    inputZagAgrmRlpr.put("RPL", rplOutput);
                    docAgmt = inputZagAgrmRlpr;
                }
                if ((lZagAddtExtnAgrmMnno == "") || (lZagAddtExtnAgrmMnno == null)) {
                    docRequest = new HashMap();
                    MapDataUtil.setString(docRequest, "AGRM_PTNO", MapDataUtil.getString(pDoc, "PTNO"));
                    MapDataUtil.setString(docRequest, "AGRM_DATE", DateUtil.getCurrentDate("yyyymmdd"));
                    MapDataUtil.setString(docRequest, "SALS_AGRM_DSCD", "20");
                    MapDataUtil.setString(docRequest, "AGRM_FORM_DSCD", "2");
                    docAddSurety = agreementInfoMgmtSCService.selectAgreementHd(docRequest);
                    String lGvsrDscd = MapDataUtil.getString(docAddSurety, "GVSR_DSCD");
                    if (lGvsrDscd.equals(SAAGConstants.YES)) {
                        docAgmt.put("RPL", custResult.get("RPL"));
                    } else 
                    if (lGvsrDscd.equals(SAAGConstants.NO)) {
                        docAgmt.put("RPL", docAddSurety.get("AGRM_RLPR"));
                    }
                }
            }
            result.put("LIST1", docAgmt.get("RPL"));
        } catch (ElException e) {
        	AppLog.warn(e.getMessage(), e);
            
            throw new CgAppUserException("CG_ERROR", 0, e.getMessage(), "SPLT0003", e);
        }
        
        return result;
    }
    
    public Map selectAdditonGivingSuretybyPK(Map pDoc) throws ElException, Exception {
        Map result = new HashMap();
        MapDataUtil.setAttribute(pDoc, "totalCount", "yes");
        String addtGvsrExtnAgrnMtcd = MapDataUtil.getString(pDoc, "ADDT_GVSR_EXTN_AGRN_MTCD");
        String addtAgrmMnno = MapDataUtil.getString(pDoc, "AGRM_MNNO");
        
        Map resAddtExtn = null;
        if (SAAGConstants.ADDT_GVSR_EXTN_AGRN_MTCD_1.equals(addtGvsrExtnAgrnMtcd)) {
            resAddtExtn = comCgSaAgAdditonextensionmgmtAgzagaddtextnDAO.ag_zag_addt_extn_so3036(pDoc);
        } else {
            resAddtExtn = comCgSaAgAdditonextensionmgmtAgzagaddtextnDAO.ag_zag_addt_extn_so3041(pDoc);
        }
        if(!ObjectUtils.isEmpty(resAddtExtn)) {
        	result.putAll(resAddtExtn);
        }
        
        Map resAgmt = comCgSaAgAgreementinfomgmtAgzagagmtDAO.ag_zag_agmt_so1001(pDoc);
        if(!ObjectUtils.isEmpty(resAgmt)) {
        	result.putAll(resAgmt);
        }
        
        Map 		resGuas 	= null;
        List<Map>	resGuasList	= null;
    	resGuasList = (List<Map>) guasInfmInqrSCService.selectGuaranteeSheetList(pDoc).get(GUUtil.ATTRIBUTE_RESULT); 
        if(!ObjectUtils.isEmpty(resGuasList)) {
        	MapDataUtil.setList(result, "GUAS_LIST", resGuasList);
        } else {
        	MapDataUtil.setList(result, "GUAS_LIST", resGuasList);
        }
        
        Map reqGurtJnsr = new HashMap();
        resGuas = guasInfmInqrSCService.selectGuaranteeSheetbyPK(pDoc);
        MapDataUtil.setString(reqGurtJnsr, "CNRC_MNNO", MapDataUtil.getString(pDoc, "CNRC_MNNO"));
        MapDataUtil.setString(reqGurtJnsr, "CHNG_SRNO", MapDataUtil.getString(resGuas, "LAST_CHNG_SRNO"));
        MapDataUtil.setString(reqGurtJnsr, "PATY_TPCD", SAGUConstants.PATY_PSNL_JNSR);
        List psnlList = (List) gurtPartyMgmtSCService.selectGurtParty(reqGurtJnsr).get(GUUtil.ATTRIBUTE_RESULT); 
        MapDataUtil.setString(reqGurtJnsr, "PATY_TPCD", SAGUConstants.PATY_CRPT_JNSR);
        List crptList = (List) gurtPartyMgmtSCService.selectGurtParty(reqGurtJnsr).get(GUUtil.ATTRIBUTE_RESULT); 
        
        if (SAAGConstants.ADDT_GVSR_EXTN_AGRN_MTCD_2.equals(addtGvsrExtnAgrnMtcd)) {
            reqGurtJnsr = new HashMap();
            MapDataUtil.setString(reqGurtJnsr, "AGRM_MNNO", addtAgrmMnno);
            MapDataUtil.setString(reqGurtJnsr, "AGRM_RLPR_DSCD", SAAGConstants.AGRM_RLPR_DSCD_IN20);
            psnlList = comCgSaAgAgreementinfomgmtAgzagagmtDAO.ag_zag_agmt_so1512(reqGurtJnsr);
        }
        ArrayList guasPartyList = new ArrayList();
        Map listDoc = null;
        Iterator<Map> itr = null;
        String listPtno = "";
        if (null != psnlList) {
            itr = psnlList.iterator();
            while (itr.hasNext()) {
                listDoc = itr.next();
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
                if (!"".equals(listPtno)) {
                    listPtno = listPtno + "/";
                }
                listPtno = listPtno + MapDataUtil.getString(listDoc, "PTNO");
                guasPartyList.add(listDoc);
            }
        }
        
        if (resAddtExtn == null) { 
            result.put("GURT_JNSR", guasPartyList);
        }
        
        List<Map> resAddtJnsr = null;
        Map reqDoc = null;
        Map resDoc = null;
        reqDoc = new HashMap();
        MapDataUtil.setString(reqDoc, "AGRM_PTNO", MapDataUtil.getString(pDoc, "PTNO"));
        MapDataUtil.setString(reqDoc, "SALS_AGRM_DSCD", SAAGConstants.SALS_AGRM_DSCD_20);
        MapDataUtil.setString(reqDoc, "AGRM_FORM_DSCD", SAAGConstants.AGRM_FORM_DSCD_2);
        Map hdAgrm = MapDataUtil.getMap(agreementInfoMgmtSCService.selectAgreementHd(reqDoc), "result"); 
        String tmpAgrmMnno = MapDataUtil.getString(hdAgrm, "AGRM_MNNO");
        String tmpAgrmPtno = MapDataUtil.getString(hdAgrm, "AGRM_PTNO");
        String tmpGvsrDscd = MapDataUtil.getString(hdAgrm, "GVSR_DSCD");
        String tmpPsnlGvsrExmtYn = MapDataUtil.getString(hdAgrm, "PSNL_GVSR_EXMT_YN");
        if ("2".equals(tmpGvsrDscd) && "Y".equals(tmpPsnlGvsrExmtYn)) {
            MapDataUtil.setString(reqDoc, "CUST_INQR_DSCD", "IA01");
            MapDataUtil.setString(reqDoc, "CUST_INQR_COND_DSCD", "01");
            MapDataUtil.setString(reqDoc, "SRCH_KWRD", tmpAgrmPtno);
            resDoc = MapDataUtil.getMap(custMgmtSCService.selectCustInfo(reqDoc), "PRTY_BASC");
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
            MapDataUtil.setString(reqDoc, "AGRM_MNNO", tmpAgrmMnno);
            MapDataUtil.setString(reqDoc, "AGRM_RLPR_DSCD", SAAGConstants.AGRM_RLPR_DSCD_IN20);
            resAddtJnsr = comCgSaAgAgreementinfomgmtAgzagagmtDAO.ag_zag_agmt_so1512(reqDoc);
        }
        MapDataUtil.setString(result, "AGRM_STCD", MapDataUtil.getString(hdAgrm, "AGRM_STCD"));
        MapDataUtil.setString(result, "VLDT_YN", MapDataUtil.getString(hdAgrm, "VLDT_YN"));
        result.put("ADDT_JNSR", resAddtJnsr);
        
        if (resAddtExtn != null) { 
            reqDoc = new HashMap();
            MapDataUtil.setString(reqDoc, "AGRM_MNNO", MapDataUtil.getString(resAddtExtn, "AGRM_MNNO"));
            resAddtJnsr = comCgSaAgAdditonextensionmgmtAgzagagrmrlptDAO.ag_zag_agrm_rlpt_so3040(reqDoc);
            
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
                            listPtnoFlag = false;
                        }
                    }
                    if (listPtnoFlag) {
                        MapDataUtil.setString(listDoc, "GVSR_RSNM", "추가입보");
                        guasPartyList.add(listDoc);
                    }
                }
            }
            result.put("GURT_JNSR", guasPartyList);
            result.put("EXIST_ADDT_JNSR", resAddtJnsr);
        }
        return result;
    }
    
    public Map appendDocListSurety(Map pDocReq, Map pDocData) throws ElException, Exception {
        
        List resAryList = null;
        if (MapDataUtil.getAttribute(pDocData, "result").equals(SAAGConstants.RESULT_0)) {
            resAryList = new ArrayList();
        } else {
            resAryList = (List)pDocData.get("vector");
        }
        try {
            Map docOrignSurety = gurtPartyMgmtSCService.selectGurtParty(pDocReq);
            List aryList = (List)docOrignSurety.get(GUUtil.ATTRIBUTE_RESULT);
            Iterator<Map> itr = aryList.iterator();
            while (itr.hasNext()) {
                Map listDoc = itr.next();
                if(listDoc != null) resAryList.add(listDoc);
            }
        } catch (ElException e) {
        	AppLog.warn(e.getMessage(), e);
            
            throw new CgAppUserException("CG_ERROR", 0, e.getMessage(), "SPLT0003", e);
        }
        
        Map	result	= new HashMap();
        result.put("vector", resAryList);
        return result;
    }
    
    public Map selectAdditionExtension(Map pDoc) throws ElException, Exception {
        
        Map result = null;
        try {
            
        } catch (ElException e) {
        	AppLog.warn(e.getMessage(), e);
            
            throw new CgAppUserException("CG_ERROR", 0, e.getMessage(), CodeUtil.getCodeValue("[코드항목]", "[코드카테고리]", "[에러코드번호]"), e);
        }
        
        return result;
    }
    
    public ArrayList<Map> selectAdditionExtensionApp(Map pDoc) throws ElException, Exception {
        
        ArrayList<Map> result = null;
        MapDataUtil.setAttribute(pDoc, "totalCount", "yes");
        try {
            
            result = comCgSaAgAdditonextensionmgmtAgzagagmtDAO.ag_zag_agmt_so1302(pDoc);
            
        } catch (ElException e) {
        	AppLog.warn(e.getMessage(), e);
            
            throw new CgAppUserException("CG_ERROR", 0, e.getMessage(), "SPLT0003", e);
        }
        
        return result;
    }
    
    public ArrayList<Map> selectAgreementDebtDtls(Map pDoc) throws ElException, Exception {
        
        ArrayList<Map> result = null;
        MapDataUtil.setAttribute(pDoc, "totalCount", "yes");
        try {
        	result = new ArrayList<Map>();
            
            result = comCgSaAgAdditonextensionmgmtAgzagagmtDAO.ag_zag_agmt_so1301(pDoc);
        } catch (ElException e) {
        	AppLog.warn(e.getMessage(), e);
            
            throw new CgAppUserException("CG_ERROR", 0, e.getMessage(), "SPLT0003", e);
        }
        
        return result;
    }
    
    public Map selectExtensionAgreemenbyPK(Map pDoc) throws ElException, Exception {
        
        Map result = null;
        try {
            
        } catch (ElException e) {
        	AppLog.warn(e.getMessage(), e);
            
            throw new CgAppUserException("CG_ERROR", 0, e.getMessage(), CodeUtil.getCodeValue("[코드항목]", "[코드카테고리]", "[에러코드번호]"), e);
        }
        
        return result;
    }
    
    public ArrayList<Map> selectWrittenConsent(Map pDoc) throws ElException, Exception {
        
        ArrayList<Map> result = null;
        MapDataUtil.setAttribute(pDoc, "totalCount", "yes");
        try {
            
            result = comCgSaAgAdditonextensionmgmtAgzagagmtDAO.ag_zag_agmt_so1516(pDoc);
        } catch (ElException e) {
        	AppLog.warn(e.getMessage(), e);
            
            throw new CgAppUserException("CG_ERROR", 0, e.getMessage(), "SPLT0003", e);
        }
        
        return result;
    }
    
    public Map insertAdditonGivingSurety_OLD(Map pDoc) throws ElException, Exception {
        
        Map result = null;
        result = new HashMap();
        Map listDoc = null;
        Map docReqPT = new HashMap();
        Map docReqAG = new HashMap();
        Map docVO = MapDataUtil.getMap(pDoc, "VO");
        Map docGU = MapDataUtil.getMap(pDoc, "VO2");
        List<Map> docVL = (List<Map>)pDoc.get("JOINTSURETY_LIST");
        try {
            
            Map newAgrmMnnoDo = agreementRegTblBCService.selectArgmMnno(pDoc);
            String newAgrmMnno = "";
            newAgrmMnno = MapDataUtil.getString(newAgrmMnnoDo, "NEW_AGRM_MNNO");
            
            docReqAG = new HashMap();
            MapDataUtil.setString(docReqAG, "AGRM_MNNO", newAgrmMnno);
            MapDataUtil.setString(docReqAG, "AGRM_PTNO", MapDataUtil.getString(docVO, "AGRM_PTNO"));
            MapDataUtil.setString(docReqAG, "CNRC_MNNO", MapDataUtil.getString(pDoc, "CNRC_MNNO"));
            MapDataUtil.setString(docReqAG, "CHNG_SRNO", MapDataUtil.getString(pDoc, "CHNG_SRNO"));
            MapDataUtil.setString(docReqAG, "GUAS_NO", MapDataUtil.getString(docGU, "GUAS_NO"));
            MapDataUtil.setString(docReqAG, "ADDT_GVSR_EXTN_AGRN_DATE", MapDataUtil.getString(docVO, "ADDT_GVSR_EXTN_AGRN_DATE"));
            MapDataUtil.setString(docReqAG, "EXTN_GURT_DLNN_DATE", MapDataUtil.getString(docVO, "EXTN_GURT_DLNN_DATE"));
            MapDataUtil.setString(docReqAG, "ADDT_GVSR_EXTN_AGRN_DSCD", MapDataUtil.getString(pDoc, "ADDT_GVSR_EXTN_AGRN_MTCD"));
            MapDataUtil.setString(docReqAG, "ADDT_GVSR_EXTN_AGRN_MTCD", MapDataUtil.getString(pDoc, "ADDT_GVSR_EXTN_AGRN_DSCD"));
            MapDataUtil.setString(docReqAG, "MLTP_APLC_CRRTN_CD", MapDataUtil.getString(pDoc, "MLTP_APLC_CRRTN_CD"));
            MapDataUtil.setString(docReqAG, "AGRM_NOAC", MapDataUtil.getString(docVO, "AGRM_NOAC"));
            String lAddtGvsrExtnAgrnMtcd = MapDataUtil.getString(pDoc, "ADDT_GVSR_EXTN_AGRN_MTCD");
            if (lAddtGvsrExtnAgrnMtcd.equals(SAAGConstants.ADDT_GVSR_EXTN_AGRN_MTCD_1)) {
                MapDataUtil.setString(docReqAG, "AGRM_AMT", MapDataUtil.getString(docGU, "BNAMT"));
            } else 
            if (lAddtGvsrExtnAgrnMtcd.equals(SAAGConstants.ADDT_GVSR_EXTN_AGRN_MTCD_2)) {
                MapDataUtil.setString(docReqAG, "AGRM_AMT", MapDataUtil.getString(docVO, "BASC_FNCN_LMAMT"));
            }
            String lEmpNo = UserHeaderUtil.getInstance().getEmpno();
            MapDataUtil.setString(docReqAG, "LAST_CHNG_DTTM", (String) UserHeaderUtil.getInstance().getTimestamp());
            MapDataUtil.setString(docReqAG, "LAST_CHNR_ID", lEmpNo);
            MapDataUtil.setString(docReqAG, "ADDT_GVSR_RSN_CNTS", MapDataUtil.getString(docVO, "ADDT_GVSR_RSN_CNTS"));
            MapDataUtil.setString(docReqAG, "CHNG_TRGT_AGRM_MNNO", MapDataUtil.getString(docGU, "AGRM_MNNO"));
            int	resultCnt	= 0;
            if (MapDataUtil.getString(pDoc, "ACTIONMODE").equals(SAAGConstants.UPDATE)) {
            	resultCnt	= additonExtensionTblBCService.updateZagAddtExtn(docReqAG);
            } else {
            	resultCnt	= additonExtensionTblBCService.insertZagAdGvsrExAgrnGaus(docReqAG);
            }
            List aryList = docVL;
            Iterator<Map> itr = aryList.iterator();
            while (itr.hasNext()) {
                listDoc = itr.next();
                docReqPT = new HashMap();
                MapDataUtil.setString(docReqPT, "NEW_AGRM_MNNO", newAgrmMnno);
                MapDataUtil.setString(docReqPT, "AGRM_MNNO", MapDataUtil.getString(listDoc, "AGRM_MNNO"));
                MapDataUtil.setString(docReqPT, "AGRM_RLPR_DSCD", "40");
                MapDataUtil.setString(docReqPT, "AGRM_RLPR_SRNO", MapDataUtil.getString(listDoc, "AGRM_RLPR_SRNO"));
                MapDataUtil.setString(docReqPT, "LAST_CHNR_ID", UserHeaderUtil.getInstance().getEmpno());
                MapDataUtil.setString(docReqPT, "LAST_CHNG_DTTM", (String) UserHeaderUtil.getInstance().getTimestamp());
                if (MapDataUtil.getString(pDoc, "ACTIONMODE").equals(SAAGConstants.UPDATE)) {
                } else {
                	resultCnt = additonExtensionTblBCService.insertZagAgrmRlpr(docReqPT);
                }
            }
            MapDataUtil.setString(result, "AGRM_MNNO", newAgrmMnno);
        } catch (ElException e) {
        	AppLog.warn(e.getMessage(), e);
            
            throw new CgAppUserException("CG_ERROR", 0, e.getMessage(), "SPLT0003", e);
        }
        
        return result;
    }
    
    public Map insertAdditonGivingSurety(Map pDoc) throws ElException, Exception {
        Map result = new HashMap();
        int bizOutput = 0;
        try {
            Map newAgrmMnnoDoc = null;
            Map reqAddtExtn = null;
            Map gualListDoc = null;
            String newAgrmMnno = "";
            
            if ("1".equals(MapDataUtil.getString(pDoc, "ADDT_GVSR_EXTN_AGRN_MTCD"))) {
                Map listDoc = null;
                Map reqAgrmRlpr = null;
                int srno = 0;
                String agrmRlprDtlDscd = null;
                List arryList = (List)pDoc.get("JOINTSURETY_LIST");
                Iterator<Map> itr = null;
                List guasArryList = (List)pDoc.get("GUAS_LIST");
                Iterator<Map> guasItr = guasArryList.iterator();
                while (guasItr.hasNext()) {
                    gualListDoc = guasItr.next();
                    newAgrmMnnoDoc = agreementRegTblBCService.selectArgmMnno(pDoc);
                    newAgrmMnno = MapDataUtil.getString(newAgrmMnnoDoc, "NEW_AGRM_MNNO");
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
                    MapDataUtil.setString(reqAddtExtn, "LAST_CHNR_ID", (String) UserHeaderUtil.getInstance().getEmpno());
                    MapDataUtil.setString(reqAddtExtn, "LAST_CHNG_DTTM", (String) UserHeaderUtil.getInstance().getTimestamp());
                    bizOutput = comCgSaAgAdditonextensionmgmtAgzagadgvsrexagrnguasDAO.ag_zag_ad_gvsr_ex_agrn_guas_io3104(reqAddtExtn);
                    MapDataUtil.setResult(result, bizOutput);
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
                        MapDataUtil.setString(reqAgrmRlpr, "LAST_CHNR_ID"		, (String) UserHeaderUtil.getInstance().getEmpno());
                        MapDataUtil.setString(reqAgrmRlpr, "LAST_CHNG_DTTM"		, (String) UserHeaderUtil.getInstance().getTimestamp());
                        bizOutput = comCgSaAgAdditonextensionmgmtAgzagagmtrlprDAO.ag_zag_agmt_rlpr_io3104(reqAgrmRlpr);
                        MapDataUtil.setResult(result, bizOutput);
                    }
                }
                MapDataUtil.setString(result, "AGRM_MNNO", newAgrmMnno); 
            } else {
                newAgrmMnnoDoc = agreementRegTblBCService.selectArgmMnno(pDoc);
                newAgrmMnno = MapDataUtil.getString(newAgrmMnnoDoc, "NEW_AGRM_MNNO");
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
                MapDataUtil.setString(reqAddtExtn, "LAST_CHNR_ID", (String) UserHeaderUtil.getInstance().getEmpno());
                MapDataUtil.setString(reqAddtExtn, "LAST_CHNG_DTTM", (String) UserHeaderUtil.getInstance().getTimestamp());
                bizOutput = comCgSaAgAdditonextensionmgmtAgzagadgvsrexagrnguasDAO.ag_zag_ad_gvsr_ex_agrn_guas_io3104(reqAddtExtn);
                MapDataUtil.setResult(result, bizOutput);
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
                    MapDataUtil.setString(reqAgrmRlpr, "LAST_CHNR_ID", (String) UserHeaderUtil.getInstance().getEmpno());
                    MapDataUtil.setString(reqAgrmRlpr, "LAST_CHNG_DTTM", (String) UserHeaderUtil.getInstance().getTimestamp());
                    bizOutput = comCgSaAgAdditonextensionmgmtAgzagagmtrlprDAO.ag_zag_agmt_rlpr_io3104(reqAgrmRlpr);
                    MapDataUtil.setResult(result, bizOutput);
                }
                MapDataUtil.setString(result, "AGRM_MNNO", newAgrmMnno); 
            }
        } catch (ElException e) {
            AppLog.warn(e.getMessage(), e);
            throw new CgAppUserException("CG_ERROR", 0, e.getMessage(), "SPLT0003", e);
        }
        return result;
    }
    
    public Map insertExtensionAgreement(Map pDoc) throws ElException, Exception {
        
        Map result = null;
        try {
            
        } catch (ElException e) {
        	AppLog.warn(e.getMessage(), e);
            
            throw new CgAppUserException("CG_ERROR", 0, e.getMessage(), CodeUtil.getCodeValue("[코드항목]", "[코드카테고리]", "[에러코드번호]"), e);
        }
        
        return result;
    }
    
    public int updateExtensionAgreement(Map pDoc) throws ElException, Exception {
        
        int result = 0;
        Map bizInput = null;
        Map bizOutput = null;
        try {
            
            if ("1".equals(MapDataUtil.getString(pDoc, "ADDT_GVSR_EXTN_AGRN_MTCD"))) {
                String lAgrmMnno = null;
                List aryList = (List)pDoc.get("JOINTSURETY_LIST");
                Map listDoc = null;
                Map reqAgrmRlpr = null;
                int srno = 0;
                String agrmRlprDtlDscd = "";
                Iterator<Map> itr = null;
                Map gualListDoc = null;
                List guasArryList = (List)pDoc.get("GUAS_LIST");
                Iterator<Map> guasItr = guasArryList.iterator();
                while (guasItr.hasNext()) {
                    gualListDoc = guasItr.next();
                    bizInput = new HashMap();
                    MapDataUtil.setString(bizInput, "CNRC_MNNO", MapDataUtil.getString(gualListDoc, "CNRC_MNNO"));
                    bizOutput = comCgSaAgAdditonextensionmgmtAgzagaddtextnDAO.ag_zag_addt_extn_so3036(bizInput);
                    MapDataUtil.setString(pDoc, "AGRM_MNNO", MapDataUtil.getString(bizOutput, "AGRM_MNNO"));
                    result = additonExtensionTblBCService.updateZagAddtExtn(pDoc);
                    result = comCgSaAgAdditonextensionmgmtAgzagagmtrlprDAO.ag_zag_agmt_rlpr_do3102(pDoc);
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
                        MapDataUtil.setString(reqAgrmRlpr, "AGRM_MNNO", lAgrmMnno);
                        MapDataUtil.setString(reqAgrmRlpr, "AGRM_RLPR_DSCD", SAAGConstants.AGRM_RLPR_DSCD_IN40);
                        MapDataUtil.setString(reqAgrmRlpr, "AGRM_RLPR_SRNO", new Integer(srno).toString());
                        MapDataUtil.setString(reqAgrmRlpr, "PTNO", MapDataUtil.getString(listDoc, "PTNO"));
                        MapDataUtil.setString(reqAgrmRlpr, "AGRM_RLPR_DTL_DSCD", agrmRlprDtlDscd);
                        MapDataUtil.setString(reqAgrmRlpr, "RPPR_POS_CD", MapDataUtil.getString(listDoc, "RPPR_POS_CD"));
                        MapDataUtil.setString(reqAgrmRlpr, "QTRT", MapDataUtil.getString(listDoc, "QTRT"));
                        MapDataUtil.setString(reqAgrmRlpr, "QUOT_RNKN", MapDataUtil.getString(listDoc, "QUOT_RNKN"));
                        MapDataUtil.setString(reqAgrmRlpr, "ZPCD1", MapDataUtil.getString(listDoc, "ZPCD1"));
                        MapDataUtil.setString(reqAgrmRlpr, "AGRM_RPPR_ADRS", MapDataUtil.getString(listDoc, "AGRM_RPPR_ADRS"));
                        MapDataUtil.setString(reqAgrmRlpr, "ASCN_JNNG_YN", MapDataUtil.getString(listDoc, "ASCN_JNNG_YN"));
                        MapDataUtil.setString(reqAgrmRlpr, "MRTG_NOAC", MapDataUtil.getString(listDoc, "MRTG_NOAC"));
                        MapDataUtil.setString(reqAgrmRlpr, "CRRTN_CD", MapDataUtil.getString(listDoc, "CRRTN_CD"));
                        MapDataUtil.setString(reqAgrmRlpr, "BSN_PTCP_QTRT", MapDataUtil.getString(listDoc, "BSN_PTCP_QTRT"));
                        MapDataUtil.setString(reqAgrmRlpr, "CNST_PTCP_QTRT", MapDataUtil.getString(listDoc, "CNST_PTCP_QTRT"));
                        MapDataUtil.setString(reqAgrmRlpr, "JNGR_YN", MapDataUtil.getString(listDoc, "JNGR_YN"));
                        MapDataUtil.setString(reqAgrmRlpr, "GVSR_DATE", MapDataUtil.getString(pDoc, "ADDT_GVSR_EXTN_AGRN_DATE"));
                        MapDataUtil.setString(reqAgrmRlpr, "ADDT_GVSR_RSN_CNTS", MapDataUtil.getString(listDoc, "ADDT_GVSR_RSN_CNTS"));
                        MapDataUtil.setString(reqAgrmRlpr, "CNLT_RSN_DSCD", MapDataUtil.getString(listDoc, "CNLT_RSN_DSCD"));
                        MapDataUtil.setString(reqAgrmRlpr, "APLC_SCR", MapDataUtil.getString(listDoc, "APLC_SCR"));
                        MapDataUtil.setString(reqAgrmRlpr, "LAST_CHNR_ID", (String) UserHeaderUtil.getInstance().getEmpno());
                        MapDataUtil.setString(reqAgrmRlpr, "LAST_CHNG_DTTM", (String) UserHeaderUtil.getInstance().getTimestamp());
                        result = comCgSaAgAdditonextensionmgmtAgzagagmtrlprDAO.ag_zag_agmt_rlpr_io3104(reqAgrmRlpr);
                    }
                }
            } else {
                result = additonExtensionTblBCService.updateZagAddtExtn(pDoc);
                result = comCgSaAgAdditonextensionmgmtAgzagagmtrlprDAO.ag_zag_agmt_rlpr_do3102(pDoc);
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
                    MapDataUtil.setString(reqAgrmRlpr, "AGRM_MNNO", lAgrmMnno);
                    MapDataUtil.setString(reqAgrmRlpr, "AGRM_RLPR_DSCD", SAAGConstants.AGRM_RLPR_DSCD_IN40);
                    MapDataUtil.setString(reqAgrmRlpr, "AGRM_RLPR_SRNO", new Integer(srno).toString());
                    MapDataUtil.setString(reqAgrmRlpr, "PTNO", MapDataUtil.getString(listDoc, "PTNO"));
                    MapDataUtil.setString(reqAgrmRlpr, "AGRM_RLPR_DTL_DSCD", agrmRlprDtlDscd);
                    MapDataUtil.setString(reqAgrmRlpr, "RPPR_POS_CD", MapDataUtil.getString(listDoc, "RPPR_POS_CD"));
                    MapDataUtil.setString(reqAgrmRlpr, "QTRT", MapDataUtil.getString(listDoc, "QTRT"));
                    MapDataUtil.setString(reqAgrmRlpr, "QUOT_RNKN", MapDataUtil.getString(listDoc, "QUOT_RNKN"));
                    MapDataUtil.setString(reqAgrmRlpr, "ZPCD1", MapDataUtil.getString(listDoc, "ZPCD1"));
                    MapDataUtil.setString(reqAgrmRlpr, "AGRM_RPPR_ADRS", MapDataUtil.getString(listDoc, "AGRM_RPPR_ADRS"));
                    MapDataUtil.setString(reqAgrmRlpr, "ASCN_JNNG_YN", MapDataUtil.getString(listDoc, "ASCN_JNNG_YN"));
                    MapDataUtil.setString(reqAgrmRlpr, "MRTG_NOAC", MapDataUtil.getString(listDoc, "MRTG_NOAC"));
                    MapDataUtil.setString(reqAgrmRlpr, "CRRTN_CD", MapDataUtil.getString(listDoc, "CRRTN_CD"));
                    MapDataUtil.setString(reqAgrmRlpr, "BSN_PTCP_QTRT", MapDataUtil.getString(listDoc, "BSN_PTCP_QTRT"));
                    MapDataUtil.setString(reqAgrmRlpr, "CNST_PTCP_QTRT", MapDataUtil.getString(listDoc, "CNST_PTCP_QTRT"));
                    MapDataUtil.setString(reqAgrmRlpr, "JNGR_YN", MapDataUtil.getString(listDoc, "JNGR_YN"));
                    MapDataUtil.setString(reqAgrmRlpr, "GVSR_DATE", MapDataUtil.getString(pDoc, "ADDT_GVSR_EXTN_AGRN_DATE"));
                    MapDataUtil.setString(reqAgrmRlpr, "ADDT_GVSR_RSN_CNTS", MapDataUtil.getString(listDoc, "ADDT_GVSR_RSN_CNTS"));
                    MapDataUtil.setString(reqAgrmRlpr, "CNLT_RSN_DSCD", MapDataUtil.getString(listDoc, "CNLT_RSN_DSCD"));
                    MapDataUtil.setString(reqAgrmRlpr, "APLC_SCR", MapDataUtil.getString(listDoc, "APLC_SCR"));
                    MapDataUtil.setString(reqAgrmRlpr, "LAST_CHNR_ID", (String) UserHeaderUtil.getInstance().getEmpno());
                    MapDataUtil.setString(reqAgrmRlpr, "LAST_CHNG_DTTM", (String) UserHeaderUtil.getInstance().getTimestamp());
                    result = comCgSaAgAdditonextensionmgmtAgzagagmtrlprDAO.ag_zag_agmt_rlpr_io3104(reqAgrmRlpr);
                }
            }
        } catch (ElException e) {
        	AppLog.warn(e.getMessage(), e);
            
            throw new CgAppUserException("CG_ERROR", 0, e.getMessage(), CodeUtil.getCodeValue("[코드항목]", "[코드카테고리]", "[에러코드번호]"), e);
        }
        
        return result;
    }
    
    public Map updateAdditonGivingSurety(Map pDoc) throws ElException, Exception {
        
        Map result = null;
        try {
            
        } catch (ElException e) {
        	AppLog.warn(e.getMessage(), e);
            
            throw new CgAppUserException("CG_ERROR", 0, e.getMessage(), CodeUtil.getCodeValue("[코드항목]", "[코드카테고리]", "[에러코드번호]"), e);
        }
        
        return result;
    }
    
    public int deleteAdditionExtension(Map pDoc) throws ElException, Exception {
        
        int result = 0;
        Map bizInput = null;
        Map bizOutput = null;
        try {
            
            
            if ("1".equals(MapDataUtil.getString(pDoc, "ADDT_GVSR_EXTN_AGRN_MTCD"))) {
                Map gualListDoc = null;
                List guasArryList = (List)pDoc.get("GUAS_LIST");
                Iterator<Map> guasItr = guasArryList.iterator();
                while (guasItr.hasNext()) {
                    gualListDoc = guasItr.next();
                    bizInput = new HashMap();
                    MapDataUtil.setString(bizInput, "CNRC_MNNO", MapDataUtil.getString(gualListDoc, "CNRC_MNNO"));
                    bizOutput = comCgSaAgAdditonextensionmgmtAgzagaddtextnDAO.ag_zag_addt_extn_so3036(bizInput);
                    MapDataUtil.setString(pDoc, "AGRM_MNNO", MapDataUtil.getString(bizOutput, "AGRM_MNNO"));
                    result = comCgSaAgAdditonextensionmgmtAgzagagmtrlprDAO.ag_zag_agmt_rlpr_do3102(pDoc);
                    result = comCgSaAgAdditonextensionmgmtAgzagadgvsrexagrnguasDAO.ag_zag_ad_gvsr_ex_agrn_guas_do3101(pDoc);
                }
            } else {
                result = comCgSaAgAdditonextensionmgmtAgzagagmtrlprDAO.ag_zag_agmt_rlpr_do3102(pDoc);
                result = comCgSaAgAdditonextensionmgmtAgzagadgvsrexagrnguasDAO.ag_zag_ad_gvsr_ex_agrn_guas_do3101(pDoc);
            }
        } catch (ElException e) {
        	AppLog.warn(e.getMessage(), e);
            
            throw new CgAppUserException("CG_ERROR", 0, e.getMessage(), "SPLT0003", e);
        }
        
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