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

}