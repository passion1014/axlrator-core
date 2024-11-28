package com.modon.control.pig.service;

import com.modon.control.alarm.service.AlarmService;
import com.modon.control.common.aws.AwsBuckets;
import com.modon.control.common.aws.S3;
import com.modon.control.common.exception.CustomRuntimeException;
import com.modon.control.common.menu.service.MenuService;
import com.modon.control.common.menu.service.MenuUpdateService;
import com.modon.control.common.security.CustomUserDetails;
import com.modon.control.common.util.SessionUtil;
import com.modon.control.domain.entity.*;
import com.modon.control.domain.repository.*;
import com.modon.control.domain.type.GenderType;
import com.modon.control.domain.type.LitterStatus;
import com.modon.control.domain.type.PigHistoryStatus;
import com.modon.control.domain.type.PigStatus;
import com.modon.control.dto.alarm.AlarmDto;
import com.modon.control.dto.common.AttachDto;
import com.modon.control.dto.common.MenuBadgeDto;
import com.modon.control.dto.common.RemoveDto;
import com.modon.control.dto.pig.*;
import com.modon.control.dto.sensor.SensorDataDto;
import com.modon.control.dto.statistic.StatisticPigletDto;
import lombok.RequiredArgsConstructor;
import org.modelmapper.ModelMapper;
import org.springframework.data.domain.Page;
import org.springframework.security.core.Authentication;
import org.springframework.security.core.context.SecurityContextHolder;
import org.springframework.security.crypto.password.PasswordEncoder;
import org.springframework.stereotype.Service;
import org.springframework.transaction.annotation.Transactional;
import org.springframework.web.multipart.MultipartFile;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.*;
import java.util.concurrent.atomic.AtomicReference;
import java.util.stream.Collectors;

@Service
@RequiredArgsConstructor
public class PigServiceImpl implements PigService {
    private final PasswordEncoder passwordEncoder;
    private final MoPigRepository moPigRepository;
    private final MoPigLitterRepository moPigLitterRepository;
    private final MoPigMemoRepository moPigMemoRepository;
    private final MoPigHistoryRepository moPigHistoryRepository;
    private final MoFarmRepository moFarmRepository;
    private final MoPigQueryDsl moPigQueryDsl;
    private final MoAttachRepository moAttachRepository;
    private final MoPigPlacementHistoryRepository moPigPlacementHistoryRepository;
    private final MoTypeRepository moTypeRepository;
    private final MoCagePartitionRepository moCagePartitionRepository;
    private final MoCageRepository moCageRepository;
    private final MenuUpdateService menuUpdateService;
    private final S3 s3;
    ModelMapper mapper = new ModelMapper();
    private final MoMemberRepository moMemberRepository;
    private final MoPigRelationRepository moPigRelationRepository;
    private final MoPigFarrowingScheduleRepository moPigFarrowingScheduleRepository;

    private final AlarmService alarmService;

    @Override
    public Optional<Integer> getStatisticLitterCnt(PigSearchDto pigSearchDto) {
        // 스케줄링 통계정산에 사용 (각 농장별 암컷이면서 상태가 (정상,임신중,분만중,재교배)이고, 삭제처리 되지 않은 양돈)
        return moPigQueryDsl.getStatisticLitterCnt(pigSearchDto);
    }

    @Override
    public Optional<Map<Integer, Long>> getStatisticLitterGroupCnt(PigSearchDto pigSearchDto) {
        // 스케줄링 통계정산에 사용 (각 농장별 암컷이면서 산차의 회차가 가장 큰 기준, 삭제처리 되지 않은 양돈)
        return moPigQueryDsl.getStatisticLitterGroupCnt(pigSearchDto);
    }

    @Override
    public Optional<StatisticPigletDto> getStatisticPigletCnt(StatisticPigletDto statisticPigletDto) {
//        getStatisticPigletCnt
        return moPigQueryDsl.getStatisticPigletCnt(statisticPigletDto);
    }

    @Override
    public Optional<StatisticPigletDto> getStatisticPigletDaysCnt(StatisticPigletDto statisticPigletDto) {
//        getStatisticPigletCnt
        return moPigQueryDsl.getStatisticPigletDaysCnt(statisticPigletDto);
    }


    @Override
    public Optional<Integer> getManagementCnt(PigSearchDto pigSearchDto) {
        // 대시보드에서 사용 (관심돈 수)
        return moPigQueryDsl.countPigList(pigSearchDto);
    }


    @Override
    public Optional<Integer> getPigCount(PigSearchDto pigSearchDto) {
        // 검색조건에 따른 양돈수
        return moPigQueryDsl.getPigCount(pigSearchDto);
    }

    @Override
    @Transactional
    public Optional<Page<PigDto>> getListSearchType(PigSearchDto pigSearchDto) {
//            유형, 성별, 상태
//            생년월일 시작일 ~ 종료일, 관심양돈
//            구입일 시작일 ~ 종료일, 구입체중
//            초발정일 시작일 ~ 종료일
//            등록일 시작일 ~ 종료일
//            개체번호
        return moPigQueryDsl.findPigList(pigSearchDto);
    }

    @Override
    @Transactional
    public Optional<List<PigDto>> getAllListSearchType(PigSearchDto pigSearchDto) {
//            유형, 성별, 상태
//            생년월일 시작일 ~ 종료일, 관심양돈
//            구입일 시작일 ~ 종료일, 구입체중
//            초발정일 시작일 ~ 종료일
//            등록일 시작일 ~ 종료일
//            개체번호
        return moPigQueryDsl.findPigAllList(pigSearchDto);
    }


    @Override
    public Optional<PigDetailDto> getPigDetail(Long id) {
        PigDto pigDto = PigDto.builder().id(id).build();
        PigDetailDto pigDetailDto = PigDetailDto.builder().pigDto(pigDto).build();


        // 양돈 정보 조회
        moPigRepository.findById(id)
                .map(item -> {

                    // 양돈의 성별을 확인하고, 암컷일 경우에만 산차 이력 조회를 진행합니다.
                    if ("FEMALE".equals(item.getPigGender().name())) {  // 암컷인 경우
                        // 양돈 산차 이력 조회
                        List<PigLitterDto> pigLitterDtoList = moPigLitterRepository.findByPigCode(item)
                                .stream()
                                .map(pigLitter -> mapper.map(pigLitter, PigLitterDto.class))
                                .sorted(Comparator.comparing(PigLitterDto::getLitterNumber)) // 여기에서 정렬
                                .collect(Collectors.toCollection(ArrayList::new));  // 변경 가능한 ArrayList로 변환

                        // 산차 이력이 8개 미만일 경우, 나머지를 빈 객체로 채움
                        while (pigLitterDtoList.size() < 8) {
                            pigLitterDtoList.add(new PigLitterDto());
                        }

                        pigDetailDto.setPigLitterDtoList(pigLitterDtoList);
                    }

                    MoType moType = moTypeRepository.findByTypeTypeAndCode("2", item.getTypeCode()).orElse(null);
                    return PigDto.builder()
                            .id(item.getId())
                            .pigNo(item.getPigNo())
                            .pigIdentification(item.getPigIdentification())
                            .pigFarmCode(item.getPigFarmCode().getId())
                            .pigStatus(item.getPigStatus().getStatus())
                            .pigManagementYn(item.getPigManagementYn())
                            .pigName(item.getPigName())
                            .pigBreed(item.getPigBreed())
                            .pigWeight(item.getPigWeight())
                            .pigBirthdate(item.getPigBirthdate())
                            .pigGender(item.getPigGender().getType())
                            .pigDate(item.getPigDate())
                            .pigWriter(item.getPigWriter())
                            .pigPurchaseWeight(item.getPigPurchaseWeight())
                            .pigFirstEstrous(item.getPigFirstEstrous())
                            .pigPurchaseDate(item.getPigPurchaseDate())
                            .cageName(item.getCageName())
                            .partitionName(item.getPartitionName())
                            .pigOrigin(item.getPigOrigin())
                            .pigExpiryDate(LocalDate.from(item.getPigExpiryDate()))
                            .typeCode(moType)
                            .pigAttach1((item.getPigImgId1() != null ? AttachDto.builder()
                                    .id(item.getPigImgId1().getId())
                                    .attachFileExtension(item.getPigImgId1().getAttachFileExtension())
                                    .attachFileSize(item.getPigImgId1().getAttachFileSize())
                                    .attachFilePath(item.getPigImgId1().getAttachFilePath())
                                    .attachOriginalFileName(item.getPigImgId1().getAttachOriginalFileName())
                                    .attachSavedFileName(item.getPigImgId1().getAttachSavedFileName())
                                    .build() : new AttachDto()))
                            .pigAttach2((item.getPigImgId2() != null ? AttachDto.builder()
                                    .id(item.getPigImgId2().getId())
                                    .attachFileExtension(item.getPigImgId2().getAttachFileExtension())
                                    .attachFileSize(item.getPigImgId2().getAttachFileSize())
                                    .attachFilePath(item.getPigImgId2().getAttachFilePath())
                                    .attachOriginalFileName(item.getPigImgId2().getAttachOriginalFileName())
                                    .attachSavedFileName(item.getPigImgId2().getAttachSavedFileName())
                                    .build() : new AttachDto()))
                            .pigAttach3((item.getPigImgId3() != null ? AttachDto.builder()
                                    .id(item.getPigImgId3().getId())
                                    .attachFileExtension(item.getPigImgId3().getAttachFileExtension())
                                    .attachFileSize(item.getPigImgId3().getAttachFileSize())
                                    .attachFilePath(item.getPigImgId3().getAttachFilePath())
                                    .attachOriginalFileName(item.getPigImgId3().getAttachOriginalFileName())
                                    .attachSavedFileName(item.getPigImgId3().getAttachSavedFileName())
                                    .build() : new AttachDto()))
                            .build();
                })
                .ifPresent(pigDetailDto::setPigDto);

        // 양돈 변경 이력 조회
        List<PigHistoryDto> pigHistoryDtoList = moPigHistoryRepository.findByHistoryPigCode(MoPig.builder().id(id).build())
                .stream()
                .map(item -> mapper.map(item, PigHistoryDto.class))
                .toList();
        pigDetailDto.setPigHistoryDtoList(pigHistoryDtoList);


        return Optional.of(pigDetailDto);
    }

    @Override
    public Optional<PigDto> registPigImage(PigDto pigDto) {


        MoPig moPig = moPigRepository.findById(pigDto.getId())
                .orElseThrow(() -> new CustomRuntimeException("등록되지 않은 돼지입니다."));

        // 파일 업로드
        String s3Key = AwsBuckets.generateUserProfileKey(moPig.getPigIdentification());
        if (pigDto.getPigImgId1() != null) {
            String url = s3.upload(pigDto.getPigImgId1(), s3Key);

            if (url != null && !url.isEmpty()) {
                String savedFileName = url.substring(url.lastIndexOf("/"));
                moPig.setPigImgId1(MoAttach.builder()
                        .attachFileExtension(pigDto.getPigImgId1().getContentType())
                        .attachFileSize(pigDto.getPigImgId1().getSize())
                        .attachFilePath(url)
                        .attachOriginalFileName(pigDto.getPigImgId1().getOriginalFilename())
                        .attachSavedFileName(savedFileName)
                        .build());

                pigDto.setPigAttach1(AttachDto.builder()
                        .id(moPig.getPigImgId1().getId())
                        .attachFileExtension(moPig.getPigImgId1().getAttachFileExtension())
                        .attachFileSize(moPig.getPigImgId1().getAttachFileSize())
                        .attachFilePath(moPig.getPigImgId1().getAttachFilePath())
                        .attachOriginalFileName(moPig.getPigImgId1().getAttachOriginalFileName())
                        .attachSavedFileName(moPig.getPigImgId1().getAttachSavedFileName())
                        .build());
            }
        }
        if (pigDto.getPigImgId2() != null) {
            String url = s3.upload(pigDto.getPigImgId2(), s3Key);

            if (url != null && !url.isEmpty()) {
                String savedFileName = url.substring(url.lastIndexOf("/"));
                moPig.setPigImgId2(MoAttach.builder()
                        .attachFileExtension(pigDto.getPigImgId2().getContentType())
                        .attachFileSize(pigDto.getPigImgId2().getSize())
                        .attachFilePath(url)
                        .attachOriginalFileName(pigDto.getPigImgId2().getOriginalFilename())
                        .attachSavedFileName(savedFileName)
                        .build());

                pigDto.setPigAttach2(AttachDto.builder()
                        .id(moPig.getPigImgId2().getId())
                        .attachFileExtension(moPig.getPigImgId2().getAttachFileExtension())
                        .attachFileSize(moPig.getPigImgId2().getAttachFileSize())
                        .attachFilePath(moPig.getPigImgId2().getAttachFilePath())
                        .attachOriginalFileName(moPig.getPigImgId2().getAttachOriginalFileName())
                        .attachSavedFileName(moPig.getPigImgId2().getAttachSavedFileName())
                        .build());
            }
        }
        if (pigDto.getPigImgId3() != null) {
            String url = s3.upload(pigDto.getPigImgId3(), s3Key);

            if (url != null && !url.isEmpty()) {
                String savedFileName = url.substring(url.lastIndexOf("/"));
                moPig.setPigImgId3(MoAttach.builder()
                        .attachFileExtension(pigDto.getPigImgId3().getContentType())
                        .attachFileSize(pigDto.getPigImgId3().getSize())
                        .attachFilePath(url)
                        .attachOriginalFileName(pigDto.getPigImgId3().getOriginalFilename())
                        .attachSavedFileName(savedFileName)
                        .build());

                pigDto.setPigAttach3(AttachDto.builder()
                        .id(moPig.getPigImgId3().getId())
                        .attachFileExtension(moPig.getPigImgId3().getAttachFileExtension())
                        .attachFileSize(moPig.getPigImgId3().getAttachFileSize())
                        .attachFilePath(moPig.getPigImgId3().getAttachFilePath())
                        .attachOriginalFileName(moPig.getPigImgId3().getAttachOriginalFileName())
                        .attachSavedFileName(moPig.getPigImgId3().getAttachSavedFileName())
                        .build());

            }
        }

        // 양돈 정보 수정
        moPigRepository.save(moPig);

        return Optional.of(pigDto);


    }

    @Override
    public Optional<Boolean> updatePig(PigDto pigDto) {

        MoPig moPig = moPigRepository.findById(pigDto.getId())
                .orElseThrow(() -> new IllegalArgumentException("해당 양돈정보가 없습니다. id=" + pigDto.getId()));

        // 이전 양돈정보는 이력에 남김
        MoPigHistory moPigHistory = MoPigHistory.builder()
                .historyPigCode(moPig)
                .pigNo(moPig.getPigNo())
                .pigIdentification(moPig.getPigIdentification())
                .pigName(moPig.getPigName())
                .pigFarmCode(moPig.getPigFarmCode())
                .pigStatus(moPig.getPigStatus())
                .pigManagementYn(moPig.getPigManagementYn())
                .pigBreed(moPig.getPigBreed())
                .pigWeight(moPig.getPigWeight())
                .pigBirthdate(moPig.getPigBirthdate())
                .pigGender(moPig.getPigGender())
                .pigDate(moPig.getPigDate())
                .pigWriter(moPig.getPigWriter())
                .pigPurchaseWeight(moPig.getPigPurchaseWeight())
                .pigFirstEstrous(moPig.getPigFirstEstrous())
                .pigPurchaseDate(moPig.getPigPurchaseDate())
                .pigOrigin(moPig.getPigOrigin())
                .pigExpiryDate(moPig.getPigExpiryDate())
                .pigExpiredYn(moPig.getPigExpiredYn())
                .typeCode(moPig.getTypeCode())
                .historyMemberId(moPig.getPigWriter().toString())
                .historyDate(LocalDateTime.now())
                .cageName(moPig.getCageName())
                .partitionName(moPig.getPartitionName())
                .build();
        moPigHistoryRepository.save(moPigHistory);


        if (pigDto.getPigNo() != null) moPig.setPigNo(pigDto.getPigNo());
        if (pigDto.getPigIdentification() != null) moPig.setPigIdentification(pigDto.getPigIdentification());
        if (pigDto.getPigExpiryDate() != null) moPig.setPigExpiryDate(LocalDateTime.now());
        if (pigDto.getPigWriter() != null) moPig.setPigWriter(pigDto.getPigWriter());
        if (pigDto.getPigDate() != null) moPig.setPigDate(pigDto.getPigDate());
        if (pigDto.getPigStatus() != null) moPig.setPigStatus(PigStatus.valueOf(pigDto.getPigStatus()));
        if (pigDto.getPigBreed() != null) moPig.setPigBreed(pigDto.getPigBreed());
        if (pigDto.getPigIdentification() != null) moPig.setPigIdentification(pigDto.getPigIdentification());
        if (pigDto.getTypeCode() != null) {
            moPig.setTypeCode(pigDto.getTypeCode().getCode());
        }
        if (pigDto.getPigName() != null) {
            moPig.setPigName(pigDto.getPigName());
        }
        if (pigDto.getPigGender() != null) moPig.setPigGender(GenderType.valueOf(pigDto.getPigGender()));
        if (pigDto.getPigWeight() != null) moPig.setPigWeight(pigDto.getPigWeight());
        if (pigDto.getPigBirthdate() != null) moPig.setPigBirthdate(pigDto.getPigBirthdate());
        if (pigDto.getPigManagementYn() != null) moPig.setPigManagementYn(pigDto.getPigManagementYn());

        if (pigDto.getPigPurchaseWeight() != null) moPig.setPigPurchaseWeight(pigDto.getPigPurchaseWeight());
        if (pigDto.getPigPurchaseDate() != null) moPig.setPigPurchaseDate(pigDto.getPigPurchaseDate());
        if (pigDto.getPigOrigin() != null) moPig.setPigOrigin(pigDto.getPigOrigin());
        if (pigDto.getPigFirstEstrous() != null) moPig.setPigFirstEstrous(pigDto.getPigFirstEstrous());

        if (pigDto.getCageName() != null)
            moPig.setCageName(pigDto.getCageName().isBlank() ? null : pigDto.getCageName());
        if (pigDto.getPartitionName() != null)
            moPig.setPartitionName(pigDto.getPartitionName().isBlank() ? null : pigDto.getPartitionName());


        // 양돈 정보 수정
        moPigRepository.save(moPig);


        return Optional.of(true);
    }

    @Override
    @Transactional
    public Optional<PigLitterDto> registPigBirth(PigLitterDto pigLitterDto) {
        MoPig moPig = moPigRepository.findById(pigLitterDto.getPigId())
                .orElseThrow(() -> new CustomRuntimeException("양돈 정보를 찾을수 없습니다."));

        MoPigLitter moPigLitter;
        if (pigLitterDto.getId() != null) {
            moPigLitter = moPigLitterRepository.findById(pigLitterDto.getId())
                    .orElseThrow(() -> new CustomRuntimeException("해당 산차 기록이 없습니다."));
        } else {
            moPigLitter = new MoPigLitter(); // ID가 없는 경우, 새로운 MoPigLitter 객체 생성
        }


        if (pigLitterDto.getLitterStatus() != null)
            moPigLitter.setLitterStatus(LitterStatus.valueOf(pigLitterDto.getLitterStatus().name()));
        if (pigLitterDto.getLitterNumber() != null) moPigLitter.setLitterNumber(pigLitterDto.getLitterNumber());
        if (pigLitterDto.getPigId() != null) moPigLitter.setPigCode(moPig);
        if (pigLitterDto.getPigIdentification() != null)
            moPigLitter.setPigIdentification(pigLitterDto.getPigIdentification());
        if (pigLitterDto.getMatingDate() != null) moPigLitter.setMatingDate(pigLitterDto.getMatingDate());
//        if (pigLitterDto.getMatingPigIdentification() != null)
//            moPigLitter.setMatingPigIdentification(pigLitterDto.getMatingPigIdentification());
        if (pigLitterDto.getReturnCheckDate() != null)
            moPigLitter.setReturnCheckDate(pigLitterDto.getReturnCheckDate());
        if (pigLitterDto.getExpectedFarrowingDate() != null)
            moPigLitter.setExpectedFarrowingDate(pigLitterDto.getExpectedFarrowingDate());
        if (pigLitterDto.getFarrowingDate() != null) moPigLitter.setFarrowingDate(pigLitterDto.getFarrowingDate());
        if (pigLitterDto.getTotalBorn() != null) moPigLitter.setTotalBorn(pigLitterDto.getTotalBorn());
        if (pigLitterDto.getNursingStartDate() != null)
            moPigLitter.setNursingStartDate(pigLitterDto.getNursingStartDate());
        if (pigLitterDto.getWeaningDate() != null) moPigLitter.setWeaningDate(pigLitterDto.getWeaningDate());
        if (pigLitterDto.getWeanedNumber() != null) moPigLitter.setWeanedNumber(pigLitterDto.getWeanedNumber());
        if (pigLitterDto.getRemarks() != null) moPigLitter.setRemarks(pigLitterDto.getRemarks());

        moPigLitter = moPigLitterRepository.save(moPigLitter);


        pigLitterDto.setId(moPigLitter.getId());

        // 분만일이 업데이트 되었을때 (분만예정테이블의 분만일을 업데이트해준다)
        if (pigLitterDto.getFarrowingDate() != null) {
            moPigFarrowingScheduleRepository.updateRealFarrowingDate(moPigLitter, pigLitterDto.getFarrowingDate());
        }

        return Optional.of(pigLitterDto);
    }


    @Override
    public Optional<List<PigLitterDto>> getPigLitterList(Long pigId) {
        moPigRepository.findById(pigId)
                .orElseThrow(() -> new IllegalArgumentException("해당 양돈이 없습니다. id=" + pigId));
        List<PigLitterDto> list = moPigLitterRepository.findByPigCode(MoPig.builder().id(pigId).build())
                .stream()
                .map(item -> PigLitterDto.builder()
                        .id(item.getId())
                        .litterStatus(item.getLitterStatus())
                        .litterNumber(item.getLitterNumber())
//                        .pigCode(item.getPigCode().getId())
                        .pigIdentification(item.getPigIdentification())
                        .matingDate(item.getMatingDate())
//                        .matingPigCode(item.getMatingPigCode().getId())
//                        .matingPigIdentification(item.getMatingPigIdentification())
                        .returnCheckDate(item.getReturnCheckDate())
                        .expectedFarrowingDate(item.getExpectedFarrowingDate())
                        .farrowingDate(item.getFarrowingDate())
                        .totalBorn(item.getTotalBorn())
                        .nursingStartDate(item.getNursingStartDate())
                        .weaningDate(item.getWeaningDate())
                        .weanedNumber(item.getWeanedNumber())
                        .remarks(item.getRemarks())
                        .build())
                .toList();

        return Optional.of(list);
    }


    @Override
    public Optional<PigLitterDto> getPigLitterDetail(Long pigId, int litterNum) {
        MoPig moPig = moPigRepository.findById(pigId)
                .orElseThrow(() -> new CustomRuntimeException("해당 양돈이 없습니다. id=" + pigId));

        // findByPigIdentificationAndLitterNumber의 반환값을 Optional로 처리
        MoPigLitter litter = moPigLitterRepository.findByPigIdentificationAndLitterNumber(moPig.getPigIdentification(), litterNum);

        // litter가 null이 아닐 경우에만 PigLitterDto로 변환
        return Optional.ofNullable(litter).map(item -> PigLitterDto.builder()
                .id(item.getId())
                .litterStatus(item.getLitterStatus())
                .litterNumber(item.getLitterNumber())
                .pigId(pigId)
                .pigIdentification(item.getPigIdentification())
                .matingDate(item.getMatingDate())
                .returnCheckDate(item.getReturnCheckDate())
                .expectedFarrowingDate(item.getExpectedFarrowingDate())
                .farrowingDate(item.getFarrowingDate())
                .totalBorn(item.getTotalBorn())
                .nursingStartDate(item.getNursingStartDate())
                .weaningDate(item.getWeaningDate())
                .weanedNumber(item.getWeanedNumber())
                .remarks(item.getRemarks())
                .build());
    }


    @Override
    public Optional<Page<PigMemoDto>> getPigMemoList(PigSearchDto pigSearchDto) {
        // 양돈 메모 이력 조회
        return moPigQueryDsl.findPigMemoList(pigSearchDto.getId()
                , pigSearchDto.getSearchType()
                , pigSearchDto.getSearchValue()
                , pigSearchDto.getSearchStartDate()
                , pigSearchDto.getSearchEndDate()
                , pigSearchDto.getPage()
                , pigSearchDto.getSize());
    }

    @Override
    public Optional<Boolean> registPigMemo(PigMemoDto pigMemoDto) {
        moPigMemoRepository.save(MoPigMemo.builder()
                .id(pigMemoDto.getId())
                .memoPigCode(MoPig.builder().id(pigMemoDto.getMemoPigCode()).build())
                .memoPigIdentification(pigMemoDto.getMemoPigIdentification())
                .memoContent(pigMemoDto.getMemoContent())
                .memoMemberCode(MoMember.builder().id(SessionUtil.getMemberPK()).build())
                .memoDate(LocalDateTime.now())
                .build());
        return Optional.of(true);
    }

    @Override
    public Optional<Page<PigHistoryDto>> getPigChangeHistory(PigSearchDto pigSearchDto) {
        return moPigQueryDsl.findPigChangeHistoryList(pigSearchDto.getId()
                , pigSearchDto.getSearchType()
                , pigSearchDto.getSearchValue()
                , pigSearchDto.getSearchStartDate()
                , pigSearchDto.getSearchEndDate()
                , pigSearchDto.getPage()
                , pigSearchDto.getSize());
    }

    @Transactional
    @Override
    public Optional<Boolean> deletePigImage(PigImgDeleteDto pigImgDeleteDto) {
        // 양돈 정보 찾기
        MoPig pig = moPigRepository.findById(pigImgDeleteDto.getPigId())
                .orElseThrow(() -> new IllegalArgumentException("양돈정보가 존재하지 않습니다. id=" + pigImgDeleteDto.getPigId()));

        // 양돈 테이블에서 이미지 참조 제거
        switch (pigImgDeleteDto.getFieldId()) {
            case 1:
                pig.setPigImgId1(null);
                break;
            case 2:
                pig.setPigImgId2(null);
                break;
            case 3:
                pig.setPigImgId3(null);
                break;
            default:
                throw new IllegalArgumentException("잘못된 fieldId 값: ");
        }

        // 변경 사항 저장 및 반영
        moPigRepository.saveAndFlush(pig);

        // DB 파일 정보 삭제
        String attachFilePath = pigImgDeleteDto.getAttachFilePath();
        moAttachRepository.deleteByAttachFilePath(attachFilePath);

        // S3 파일 삭제
        s3.delete(attachFilePath);

        return Optional.of(true);
    }


    public Optional<Page<PigPlacementHistoryDto>> getPigPlacementHistory(PigSearchDto pigSearchDto) {
        return moPigQueryDsl.findPlacementHistoryList(pigSearchDto.getId()
                , pigSearchDto.getSearchStartDate()
                , pigSearchDto.getSearchEndDate()
                , pigSearchDto.getPage()
                , pigSearchDto.getSize());
    }

    // 배치 이력 상태에 따른 설명을 생성하는 메서드
    private String createReason(String pigIdentification, String memberName, String location, String action, LocalDateTime dateTime) {
        String baseFormat = "[%s] %s가 %s님에 의해 %s에 %s되었습니다."; // 기본 문구 형식
        if ("이동".equals(action)) {
            baseFormat = "[%s] %s가 %s님에 의해 %s에서 %s되었습니다."; // MOVE일 때 문구 형식
        }

        return String.format(baseFormat,
                dateTime.format(DateTimeFormatter.ofPattern("yyyy-MM-dd HH:mm")),
                pigIdentification,
                memberName,
                location,
                action);
    }

    @Override
    public Optional<Boolean> setPigPlacementHistory(PigPlacementHistoryDto pigPlacementHistoryDto) {
        // 양돈 정보 조회
        MoPig moPig = moPigRepository.findById(pigPlacementHistoryDto.getHistoryPigCode().getId())
                .orElseThrow(() -> new CustomRuntimeException("양돈 정보를 조회할 수 없습니다."));

        // 현재 인증된 사용자 정보 조회
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        CustomUserDetails userDetails = (CustomUserDetails) authentication.getPrincipal();

        // 현재 시간
        LocalDateTime now = LocalDateTime.now();

        String facilityOrPartitionName;

        MoCage moCage = null;
        MoCagePartition moCagePartition = null;
        // 시설 또는 파티션 이름 조회
        if (pigPlacementHistoryDto.getHistoryCageCode() != null) {
            // cageCode가 null이 아니면 MoCage 객체를 조회
            moCage = moCageRepository.findById(pigPlacementHistoryDto.getHistoryCageCode())
                    .orElseThrow(() -> new CustomRuntimeException("케이지 정보를 조회할 수 없습니다."));

            facilityOrPartitionName = moCage.getCageName();
        } else if (pigPlacementHistoryDto.getHistoryPartitionCode() != null) {
            // partitionCode가 null이 아니면 MoCagePartition 객체를 조회
            moCagePartition = moCagePartitionRepository.findById(pigPlacementHistoryDto.getHistoryPartitionCode())
                    .orElseThrow(() -> new CustomRuntimeException("파티션 정보를 조회할 수 없습니다."));

            facilityOrPartitionName = moCagePartition.getPartitionCage().getCageName() + " > " + moCagePartition.getPartitionName();
        } else {
            facilityOrPartitionName = "알 수 없는 위치";
        }

        // 이력 상태에 따른 설명 생성
        String action = PigHistoryStatus.fromString(pigPlacementHistoryDto.getHistoryStatus()).getDescription();
        String reason = createReason(moPig.getPigIdentification(), userDetails.getMemberName(), facilityOrPartitionName, action, now);

        // 배치 이력 객체 생성 및 저장
        MoPigPlacementHistory history = MoPigPlacementHistory.builder()
                .historyPigCode(moPig)
                .historyPigIdentification(moPig.getPigIdentification())
                .historyPartitionCode(moCagePartition)
                .historyCageCode(moCage)
                .facilityName(facilityOrPartitionName)
                .historyReason(reason)
                .historyStatus(PigHistoryStatus.fromString(pigPlacementHistoryDto.getHistoryStatus()))
                .historyMemberCode(userDetails.getId())
                .historyDate(now)
                .build();

        moPigPlacementHistoryRepository.save(history);

        return Optional.of(true);
    }


    @Override
    public Optional<Page<SensorDataDto>> getPigVitalData(PigSearchDto pigSearchDto) {
        return moPigQueryDsl.findPigVitalDataList(pigSearchDto.getId()
                , pigSearchDto.getSearchStartDate()
                , pigSearchDto.getSearchEndDate()
                , pigSearchDto.getPage()
                , pigSearchDto.getSize());
    }


    @Override
    public Optional<SensorDataDto> getPigVital(Long vitalCode, Long pigCode) {
        return moPigQueryDsl.findPigVitalData(vitalCode, pigCode);
    }

    @Override
    @Transactional
    public Optional<RemoveDto> deletePig(RemoveDto removeDto) {
        Authentication authentication = SecurityContextHolder.getContext().getAuthentication();
        CustomUserDetails userDetails = (CustomUserDetails) authentication.getPrincipal();

        try {
            // 현재 센서정보를 조회
            MoPig moPig = moPigRepository.findById(removeDto.getCode())
                    .orElseThrow(() -> new RuntimeException("양돈 정보를 조회할수 없습니다."));

            // 현재 로그인된 사용자의 최신 정보 조회
            MoMember currentMember = moMemberRepository.findByMemberFarmCodeAndMemberId(userDetails.getMemberFarmCode(), userDetails.getMemberId())
                    .orElseThrow(() -> new RuntimeException("현재 로그인된 사용자 정보 조회 실패"));

            // 조건 1: 비밀번호 일치 확인
            if (!passwordEncoder.matches(removeDto.getMemberPass(), currentMember.getMemberPass())) {
                throw new RuntimeException("비밀번호가 일치하지 않습니다.");
            }

            if (moPig.getPigManagementYn() == 'Y') {
                throw new RuntimeException("관심돈은 삭제할수 없습니다.");
            }

            // 모든 조건을 만족하는 경우, 소프트 삭제 수행
            moPig.setPigExpiredYn('Y');
            moPig.setPigExpiryDate(LocalDateTime.now());
            moPig.setDeleteYn("Y");
            moPigRepository.save(moPig);

            // 매칭되어있는 파티션에서 해당 양돈 제거
            moPigRelationRepository.deleteByPigCode(moPig);

            // 양돈 삭제코드는 7임
            MoConfigSms moConfigSms = MoConfigSms.builder().id(7L).build();
            alarmService.setAlarm(
                    AlarmDto
                            .builder()
                            .moConfigSms(moConfigSms)
                            .pigDto(
                                    PigDto
                                            .builder()
                                            .pigIdentification(moPig.getPigIdentification())
                                            .pigFarmCode(moPig.getPigFarmCode().getId())
                                            .build()
                            ).build()
            );

            removeDto.setSuccess(true);
            removeDto.setMessage("양돈 삭제가 성공적으로 완료되었습니다.");
        } catch (RuntimeException e) {
            removeDto.setSuccess(false);
            removeDto.setMessage(e.getMessage());
        }

        return Optional.of(removeDto); // 삭제 처리 결과 반환
    }


    @Override
    @Transactional
    public Optional<PigDto> registPig(PigDto pigDto) {

        try {
            MoFarm moFarm = moFarmRepository.findById(pigDto.getPigFarmCode())
                    .orElseThrow(() -> new CustomRuntimeException("해당 농장이 없습니다. id=" + pigDto.getPigFarmCode()));

            moPigRepository.findByPigFarmCode_IdAndPigIdentification(pigDto.getPigFarmCode(), pigDto.getPigIdentification())
                    .ifPresent(moPig -> {
                        throw new CustomRuntimeException("이미 사용되고 있는 개체번호입니다.");
                    });

            MoPig moPig = moPigRepository.save(MoPig.builder()
//                    .pigExpiryDate("9999-12-31 23:59:59")
                    .pigExpiredYn('N')
                    .pigManagementYn('N')
                    .pigFarmCode(moFarm)
                    .pigDate(LocalDate.now())
                    .pigWriter(pigDto.getPigWriter())
                    .pigStatus(PigStatus.valueOf(pigDto.getPigStatus())) // 상태
                    .pigBreed(pigDto.getPigBreed()) // 품번
                    .pigIdentification(pigDto.getPigIdentification()) // 개체번호
                    .pigName(pigDto.getPigName()) // 개체명
                    .typeCode(pigDto.getTypeCode().getCode()) // 유형
                    .pigGender(GenderType.valueOf(pigDto.getPigGender())) // 성별
                    .pigWeight(pigDto.getPigWeight()) // 체중
                    .pigBirthdate(pigDto.getPigBirthdate()) // 생년월일
                    .pigPurchaseWeight(pigDto.getPigPurchaseWeight()) // 구입체중
                    .pigPurchaseDate(pigDto.getPigPurchaseDate()) // 구입일
                    .pigOrigin(pigDto.getPigOrigin()) // 생산지
                    .pigFirstEstrous(pigDto.getPigFirstEstrous()) // 초발정일
                    .build());

            // 채번된 ID를 DTO에 설정
            pigDto.setId(moPig.getId());

            // 파일이 있다면 파일등록을 수행
            List<MultipartFile> files = Arrays.asList(pigDto.getPigImgId1(), pigDto.getPigImgId2(), pigDto.getPigImgId3());
            if (files.stream().anyMatch(file -> file != null && !file.isEmpty())) {
                registPigImage(pigDto);
            }


            // 양돈 등록시 신규뱃지 업데이트
            menuUpdateService.addMenuBadge(MenuBadgeDto.builder().type("pig").farm(moFarm).build());

            // 양돈 생성코드는 3임
            MoConfigSms moConfigSms = MoConfigSms.builder().id(3L).build();
            alarmService.setAlarm(AlarmDto.builder().moConfigSms(moConfigSms).pigDto(pigDto).build());

            return Optional.of(pigDto);

        } catch (Exception e) {
            throw new CustomRuntimeException(e.getMessage());
        }
    }
}
