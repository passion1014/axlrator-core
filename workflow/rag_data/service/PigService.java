package com.modon.control.pig.service;

import com.modon.control.dto.common.RemoveDto;
import com.modon.control.dto.pig.*;
import com.modon.control.dto.sensor.SensorDataDto;
import com.modon.control.dto.statistic.StatisticPigletDto;
import org.springframework.data.domain.Page;

import java.util.List;
import java.util.Map;
import java.util.Optional;

public interface PigService {
    Optional<Integer> getStatisticLitterCnt(PigSearchDto pigSearchDto);

    Optional<Map<Integer, Long>> getStatisticLitterGroupCnt(PigSearchDto pigSearchDto);

    Optional<StatisticPigletDto> getStatisticPigletCnt(StatisticPigletDto statisticPigletDto);

    Optional<StatisticPigletDto> getStatisticPigletDaysCnt(StatisticPigletDto statisticPigletDto);

    Optional<Integer> getManagementCnt(PigSearchDto pigSearchDto);

    Optional<Integer> getPigCount(PigSearchDto pigSearchDto); // 검색조건에 맞는 카운트

    Optional<Page<PigDto>> getListSearchType(PigSearchDto pigSearchDto);

    Optional<List<PigDto>> getAllListSearchType(PigSearchDto pigSearchDto);

    Optional<PigDetailDto> getPigDetail(Long id);

    Optional<PigDto> registPigImage(PigDto pigDto);

    Optional<Boolean> updatePig(PigDto pigDto);

    Optional<PigLitterDto> registPigBirth(PigLitterDto pigDto);

    Optional<List<PigLitterDto>> getPigLitterList(Long pigId);

    Optional<PigLitterDto> getPigLitterDetail(Long pigId, int litterNum);

    Optional<Page<PigMemoDto>> getPigMemoList(PigSearchDto pigSearchDto);

    Optional<Boolean> registPigMemo(PigMemoDto pigMemoDto);

    Optional<Page<PigHistoryDto>> getPigChangeHistory(PigSearchDto pigSearchDto);

    Optional<Page<SensorDataDto>> getPigVitalData(PigSearchDto pigSearchDto);

    Optional<SensorDataDto> getPigVital(Long vitalCode, Long pigCode);

    Optional<RemoveDto> deletePig(RemoveDto removeDto);

    Optional<PigDto> registPig(PigDto pigDto);

    Optional<Boolean> deletePigImage(PigImgDeleteDto pigImgDeleteDto);

    Optional<Page<PigPlacementHistoryDto>> getPigPlacementHistory(PigSearchDto pigSearchDto);

    Optional<Boolean> setPigPlacementHistory(PigPlacementHistoryDto pigPlacementHistoryDto);


}
