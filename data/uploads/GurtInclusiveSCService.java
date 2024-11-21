/**
 * Copyright (c) 2010 CG. All rights reserved.
 *
 * This software is the confidential and proprietary information of CG. You
 * shall not disclose such Confidential Information and shall use it only in
 * accordance with the terms of the license agreement you entered into with CG.
 */
package com.cg.sa.gu.gurtinclusive.service;

import java.util.ArrayList;
import java.util.Map;
import com.inswave.elfw.exception.ElException;

/**
 * 업무 그룹명 : com.cg.sa.gu.gurtinclusive.sc
 * 서브 업무명 : GurtInclusiveSC.java
 * 작성자 : Park. Ki-Seok
 * 작성일 : 2012.04.26
 * 설 명 : 포괄보증에서 처리하는 내용을 관리하는 클래스이다.
 */
/**
 * 포괄보증에서 처리하는 내용을 관리하는 클래스이다.
 */
public interface GurtInclusiveSCService {

    /**
     * <<TITLE>>
     * 포괄보증 해제시에 포괄보증의 보증잔액과 수수료잔액을 수정한다.
     * <<LOGIC>>
     * 1. [Initiate] VO개체 변수 정의
     * > Document 개체 정의 : [INPUT] Document pDoc, [OUTPUT] Document result
     * 2. 포괄보증의 보증잔액과 수수료잔액을 수정한다.
     * > com.cg.sa.gu.gurtinclusive.bc.GurtInclusiveBC.updateInlvReleasePrmmGurtBaln
     * 3. [Finalize] 정상처리후 사용자 정의 메시지 설정후 리턴
     * (사용자 정의 메세지 display를 위해 setResultStatus를 1으로 설정
     */
    public Map updateInlvReleasePrmmGurtBaln(Map pDoc) throws ElException, Exception;

    /**
     * <<TITLE>>
     * 포괄보증 계약관리번호로 해제대상의 개별보증정보를 조회한다.
     * <<LOGIC>>
     * 1. [Initiate] VO개체 변수 정의
     * > Document 개체 정의 : [INPUT] Document pDoc, [OUTPUT] Document result
     * 2. 해제대상의 포괄보증서정보를 조회한다.
     * > com.cg.sa.gu.gurtinclusive.bc.IndvGurtReleses.insertIndvApltDtl
     * 3. [Finalize] 정상처리후 사용자 정의 메시지 설정후 리턴
     * (사용자 정의 메세지 display를 위해 setResultStatus를 1으로 설정
     */
    public Map selectIndvGuasList(Map pDoc) throws ElException, Exception;

    /**
     * <<TITLE>>
     * 해제대상의 포괄보증서정보를 조회한다.
     * <<LOGIC>>
     * 1. [Initiate] VO개체 변수 정의
     * > Document 개체 정의 : [INPUT] Document pDoc, [OUTPUT] Document result
     * 2. 해제대상의 포괄보증서정보를 조회한다.
     * > com.cg.sa.gu.gurtinclusive.bc.IndvGurtReleses.insertIndvApltDtl
     * 3. [Finalize] 정상처리후 사용자 정의 메시지 설정후 리턴
     * (사용자 정의 메세지 display를 위해 setResultStatus를 1으로 설정
     */
    public Map selectInlvGuasList(Map pDoc) throws ElException, Exception;

    /**
     * <<TITLE>>
     * 건설공사대장 수신 후 개별보증신청내역에 자료를 입력한다.
     * <<LOGIC>>
     * 1. [Initiate] VO개체 변수 정의
     * > Document 개체 정의 : [INPUT] Document pDoc, [OUTPUT] Document result
     * 2. 개별보증신청대상에대해 개별보증신청내역을 등록한다.
     * > com.cg.sa.gu.gurtinclusive.bc.GurtInclusiveBC.insertIndvApltDtl
     * 3. [Finalize] 정상처리후 사용자 정의 메시지 설정후 리턴
     * (사용자 정의 메세지 display를 위해 setResultStatus를 1으로 설정
     */
    public Map insertIndvApltDtl(Map pDoc) throws ElException, Exception;

    /**
     * <<TITLE>>
     * 포괄(개별)대금지급보증에 대한 키스콘 전송상태를 조회한다.
     * <<LOGIC>>
     * 1. [Initiate] VO개체 변수 정의
     * > Document 개체 정의 : [INPUT] Document pDoc, [OUTPUT] Document result
     * 2. 포괄(개별) 대급지금보증에 대한 키스콘 전송상태 조회
     * > com.cg.sa.gu.gurtinclusive.bc.GurtInclusiveBC.selectInclusiveGurtKisconTnsmStat
     * 3. [Finalize] 정상처리후 사용자 정의 메시지 설정후 리턴
     * (사용자 정의 메세지 display를 위해 setResultStatus를 1으로 설정
     */
    public Map selectInclusiveGuasKisconTnsmStat(Map pDoc) throws ElException, Exception;

    /**
     * <<TITLE>>
     * 포괄(개별)대금지급보증 실시간 키스콘 전송
     * <<LOGIC>>
     * 1. [Initiate] VO개체 변수 정의
     * > Document 개체 정의 : [INPUT] Document pDoc, [OUTPUT] Document result
     * 2. 포괄(개별)대금지급보증 실시간 키스콘 전송
     * > com.cg.sa.gu.gurtinclusive.bc.GurtInclusiveBC.sendSbpbGurtOnline
     * 3. [Finalize] 정상처리후 사용자 정의 메시지 설정후 리턴
     * (사용자 정의 메세지 display를 위해 setResultStatus를 1으로 설정
     */
    public Map sendSbpbGurtOnline(Map pDoc) throws ElException, Exception;

    /**
     * <<TITLE>>
     * 개별대금지급보증 목록조회
     * <<LOGIC>>
     * 1. [Initiate] VO개체 변수 정의
     * > Document 개체 정의 : [INPUT] Document pDoc, [OUTPUT] Document result
     * 2. 개별대금지급보증 목록조회
     * > com.cg.sa.gu.gurtinclusive.bc.GurtInclusiveBC.selectIndvApltDtl
     * 3. [Finalize] 정상처리후 사용자 정의 메시지 설정후 리턴
     * (사용자 정의 메세지 display를 위해 setResultStatus를 1으로 설정
     */
    public Map selectIndvApltDtl(Map pDoc) throws ElException, Exception;

    /**
     * <<TITLE>>
     * 확약서번호 생성
     * <<LOGIC>>
     * 1. [Initiate] VO개체 변수 정의
     * > Document 개체 정의 : [INPUT] Document pDoc, [OUTPUT] Document result
     * 2. 개별대금지급보증 목록조회
     * > com.cg.sa.gu.gurtinclusive.bc.GurtInclusiveBC.createindvAgrmMnno
     * 3. [Finalize] 정상처리후 사용자 정의 메시지 설정후 리턴
     * (사용자 정의 메세지 display를 위해 setResultStatus를 1으로 설정
     */
    public Map createindvAgrmMnno(Map pDoc) throws ElException, Exception;

    /**
     * <<TITLE>>
     * SMS발송 한다
     * <<LOGIC>>
     * 1. [Initiate] VO개체 변수 정의
     * > Document 개체 정의 : [INPUT] Document pDoc, [OUTPUT] Document result
     * 2. SMS발송 한다
     * > com.cg.sa.gu.gurtinclusive.bc.GurtInclusiveBC.callSMS
     * 3. [Finalize] 정상처리후 사용자 정의 메시지 설정후 리턴
     * (사용자 정의 메세지 display를 위해 setResultStatus를 1으로 설정
     */
    public Map callSMS(Map pDoc) throws ElException, Exception;

    /**
     * <<TITLE>>
     * 개별보증신청내역에 제출여부 및 기타 저장한다.
     * <<LOGIC>>
     * 1. [Initiate] VO개체 변수 정의
     * > Document 개체 정의 : [INPUT] Document pDoc, [OUTPUT] Document result
     * 2. 개별보증신청내역에 제출여부 및 기타 저장한다.
     * > com.cg.sa.gu.gurtinclusive.bc.GurtInclusiveBC.saveIndvApltDtl
     * 3. [Finalize] 정상처리후 사용자 정의 메시지 설정후 리턴
     * (사용자 정의 메세지 display를 위해 setResultStatus를 1으로 설정
     */
    public Map saveIndvApltDtl(Map pDoc) throws ElException, Exception;

    /**
     * <<TITLE>>
     * 포괄보증 연대채무 확약서 신청인 정보 조회
     * <<LOGIC>>
     * 1. [Initiate] VO개체 변수 정의
     * > Document 개체 정의 : [INPUT] Document pDoc, [OUTPUT] Document result
     * 2. 개별보증신청내역에 제출여부 및 기타 저장한다.
     * > com.cg.sa.gu.gurtinclusive.bc.GurtInclusiveBC.saveIndvApltDtl
     * 3. [Finalize] 정상처리후 사용자 정의 메시지 설정후 리턴
     * (사용자 정의 메세지 display를 위해 setResultStatus를 1으로 설정
     */
    public Map selectIndvAgrmMnnoInfo(Map pDoc) throws ElException, Exception;

    /**
     * <<TITLE>>
     * 포괄업무약정서 부가정보 저장
     * <<LOGIC>>
     * 1. [Initiate] VO개체 변수 정의
     * > Document 개체 정의 : [INPUT] Document pDoc, [OUTPUT] Document result
     * 2. 개별보증신청내역에 제출여부 및 기타 저장한다.
     * > com.cg.sa.gu.gurtinclusive.bc.GurtInclusiveBC.saveIndvApltDtl
     * 3. [Finalize] 정상처리후 사용자 정의 메시지 설정후 리턴
     * (사용자 정의 메세지 display를 위해 setResultStatus를 1으로 설정
     */
    public Map updateAgrmIndvAfshInfo(Map pDoc) throws ElException, Exception;

    /**
     * <<TITLE>>
     * 포괄대금지급보증 발급사실 공시를 조회한다.
     * <<LOGIC>>
     * 1. [Initiate] VO개체 변수 정의
     * > Document 개체 정의 : [INPUT] Document pDoc, [OUTPUT] Document result
     * 2. 개별보증신청내역에 제출여부 및 기타 저장한다.
     * > com.cg.sa.gu.gurtinclusive.bc.GurtInclusiveBC.selectGuasNo
     * 3. [Finalize] 정상처리후 사용자 정의 메시지 설정후 리턴
     * (사용자 정의 메세지 display를 위해 setResultStatus를 1으로 설정
     */
    public Map selectGuasNo(Map pDoc) throws ElException, Exception;

    /**
     * <<TITLE>>
     * 개별대금지급보증 발급사실 공시를 조회한다.
     * <<LOGIC>>
     * 1. [Initiate] VO개체 변수 정의
     * > Document 개체 정의 : [INPUT] Document pDoc, [OUTPUT] Document result
     * 2. 개별보증신청내역에 제출여부 및 기타 저장한다.
     * > com.cg.sa.gu.gurtinclusive.bc.GurtInclusiveBC.selectGuasNo
     * 3. [Finalize] 정상처리후 사용자 정의 메시지 설정후 리턴
     * (사용자 정의 메세지 display를 위해 setResultStatus를 1으로 설정
     */
    public Map selectPtno(Map pDoc) throws ElException, Exception;

    /**
     * <<TITLE>>
     * 기존보증서 발급정보 조회
     * <<LOGIC>>
     * 1. [Initiate] VO개체 변수 정의
     * > Document 개체 정의 : [INPUT] Document pDoc, [OUTPUT] Document result
     * 2. 개별보증신청내역에 제출여부 및 기타 저장한다.
     * > com.cg.sa.gu.gurtinclusive.bc.GurtInclusiveBC.selectExistingGuasIssuInfm
     * 3. [Finalize] 정상처리후 사용자 정의 메시지 설정후 리턴
     * (사용자 정의 메세지 display를 위해 setResultStatus를 1으로 설정
     */
    public Map selectExistingGuasIssuInfm(Map pDoc) throws ElException, Exception;

    /**
     * <<TITLE>>
     * 포괄보증 보증서번호로 포괄 및 개별대금 발급정보를 조회한다.
     * <<LOGIC>>
     * 1. [Initiate] VO개체 변수 정의
     * > Document 개체 정의 : [INPUT] Document pDoc, [OUTPUT] Document result
     * 2. 포괄보증 보증서번호로 포괄 및 개별대금 발급정보를 조회한다.
     * > com.cg.sa.gu.gurtinclusive.bc.GurtInclusiveBC.selectInlvIndvAmt
     * 3. [Finalize] 정상처리후 사용자 정의 메시지 설정후 리턴
     * (사용자 정의 메세지 display를 위해 setResultStatus를 1으로 설정
     */
    public Map selectInlvIndvAmt(Map pDoc) throws ElException, Exception;

    /**
     * <<TITLE>>
     * 개별보증신청내역 조회
     * <<LOGIC>>
     * 1. [Initiate] VO개체 변수 정의
     * > Document 개체 정의 : [INPUT] Document pDoc, [OUTPUT] Document result
     * 2. 개별보증신청내역 조회
     * > com.cg.sa.gu.gurtinclusive.bc.GurtInclusiveBC.selectZguIndvApltDtl
     * 3. [Finalize] 정상처리후 사용자 정의 메시지 설정후 리턴
     * (사용자 정의 메세지 display를 위해 setResultStatus를 1으로 설정
     */
    public Map selectZguIndvApltDtl(Map pDoc) throws ElException, Exception;

    /**
     * <<TITLE>>
     * 포괄대금지급보증 잔액 및 수수료를 관리조회
     * <<LOGIC>>
     * 1. [Initiate] VO개체 변수 정의
     * > Document 개체 정의 : [INPUT] Document pDoc, [OUTPUT] Document result
     * 2. 포괄대금지급보증 잔액 및 수수료를 관리조회
     * > com.cg.sa.gu.gurtinclusive.bc.GurtInclusiveBC.selectBalnPrmmMngm
     * 3. [Finalize] 정상처리후 사용자 정의 메시지 설정후 리턴
     * (사용자 정의 메세지 display를 위해 setResultStatus를 1으로 설정
     */
    public Map selectBalnPrmmMngm(Map pDoc) throws ElException, Exception;

    /**
     * <<TITLE>>
     * 포괄보증 연대채무 확약서 조회
     * <<LOGIC>>
     * 1. [Initiate] VO개체 변수 정의
     * > Document 개체 정의 : [INPUT] Document pDoc, [OUTPUT] Document result
     * 2. 포괄보증 연대채무 확약서 조회
     * > com.cg.sa.gu.gurtinclusive.bc.GurtInclusiveBC.selectIndvApltDtlBzrno
     * 3. [Finalize] 정상처리후 사용자 정의 메시지 설정후 리턴
     * (사용자 정의 메세지 display를 위해 setResultStatus를 1으로 설정
     */
    public Map selectIndvApltDtlBzrno(Map pDoc) throws ElException, Exception;

    /**
     * <<TITLE>>
     * 포괄보증의 보증잔액과 수수료잔액을 조회
     * <<LOGIC>>
     * 1. [Initiate] VO개체 변수 정의
     * > Document 개체 정의 : [INPUT] Document pDoc, [OUTPUT] Document result
     * 2. 포괄보증 연대채무 확약서 조회
     * > com.cg.sa.gu.gurtinclusive.bc.GurtInclusiveBC.selectInlvPrmmGurtBaln
     * 3. [Finalize] 정상처리후 사용자 정의 메시지 설정후 리턴
     * (사용자 정의 메세지 display를 위해 setResultStatus를 1으로 설정
     */
    public Map selectInlvPrmmGurtBaln(Map pDoc) throws ElException, Exception;

    /**
     * <<TITLE>>
     * 포괄보증의 보증잔액과 수수료잔액을 수정한다.
     * <<LOGIC>>
     * 1. [Initiate] VO개체 변수 정의
     * > Document 개체 정의 : [INPUT] Document pDoc, [OUTPUT] Document result
     * 2. 포괄보증의 보증잔액과 수수료잔액을 수정한다.
     * > com.cg.sa.gu.gurtinclusive.bc.GurtInclusiveBC.updateInlvPrmmGurtBaln
     * 3. [Finalize] 정상처리후 사용자 정의 메시지 설정후 리턴
     * (사용자 정의 메세지 display를 위해 setResultStatus를 1으로 설정
     */
    public Map updateInlvPrmmGurtBaln(Map pDoc) throws ElException, Exception;

    /**
     * <<TITLE>>
     * 장기공사차수 포괄보증 조회
     * <<LOGIC>>
     * 1. [Initiate] VO개체 변수 정의
     * > Document 개체 정의 : [INPUT] Document pDoc, [OUTPUT] Document result
     * 2. 포괄보증 연대채무 확약서 조회
     * > com.cg.sa.gu.gurtinclusive.bc.GurtInclusiveBC.selectLntrCntcWrksOrseq
     * 3. [Finalize] 정상처리후 사용자 정의 메시지 설정후 리턴
     * (사용자 정의 메세지 display를 위해 setResultStatus를 1으로 설정
     */
    public Map selectLntrCntcWrksOrseq(Map pDoc) throws ElException, Exception;

    /**
     * <<TITLE>>
     * 공사이행보증 발급 유무 조회
     * <<LOGIC>>
     * 1. [Initiate] VO개체 변수 정의
     * > Document 개체 정의 : [INPUT] Document pDoc, [OUTPUT] Document result
     * 2. 포괄보증 연대채무 확약서 조회
     * > com.cg.sa.gu.gurtinclusive.bc.GurtInclusiveBC.selectPfbnIssuXn
     * 3. [Finalize] 정상처리후 사용자 정의 메시지 설정후 리턴
     * (사용자 정의 메세지 display를 위해 setResultStatus를 1으로 설정
     */
    public Map selectPfbnIssuXn(Map pDoc) throws ElException, Exception;

    /**
     * <<TITLE>>
     * 기발급보증서정보 조회
     * <<LOGIC>>
     * 1. [Initiate] VO개체 변수 정의
     * > Document 개체 정의 : [INPUT] Document pDoc, [OUTPUT] Document result
     * 2. 포괄보증 연대채무 확약서 조회
     * > com.cg.sa.gu.gurtinclusive.bc.GurtInclusiveBC.selectPrisGuasInfm
     * 3. [Finalize] 정상처리후 사용자 정의 메시지 설정후 리턴
     * (사용자 정의 메세지 display를 위해 setResultStatus를 1으로 설정
     */
    public Map selectPrisGuasInfm(Map pDoc) throws ElException, Exception;

    /**
     * <<TITLE>>
     * 전문전송
     * <<LOGIC>>
     * 1. [Initiate] VO개체 변수 정의
     * > Document 개체 정의 : [INPUT] Document pDoc, [OUTPUT] Document result
     * 2. 전문전송
     * > com.cg.sa.gu.gurtinclusive.bc.GurtInclusiveBC.processPrisGuasInfm
     * 3. [Finalize] 정상처리후 사용자 정의 메시지 설정후 리턴
     * (사용자 정의 메세지 display를 위해 setResultStatus를 1으로 설정
     */
    public Map processPrisGuasInfm(Map pDoc) throws ElException, Exception;

    /**
     * <<TITLE>>
     * 개별확정대여금액합계 조회
     * <<LOGIC>>
     * 1. [Initiate] VO개체 변수 정의
     * > Document 개체 정의 : [INPUT] Document pDoc, [OUTPUT] Document result
     * 2. 포괄보증 연대채무 확약서 조회
     * > com.cg.sa.gu.gurtinclusive.bc.GurtInclusiveBC.selectInlvCnttAmt
     * 3. [Finalize] 정상처리후 사용자 정의 메시지 설정후 리턴
     * (사용자 정의 메세지 display를 위해 setResultStatus를 1으로 설정
     */
    public Map selectInlvCnttAmt(Map pDoc) throws ElException, Exception;
}
