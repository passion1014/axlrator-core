package com.modon.control.pig.service;

import com.modon.control.domain.entity.MoPig;
import com.modon.control.domain.entity.MoPigBreath;
import com.modon.control.domain.repository.MoPigBreathRepository;
import com.modon.control.domain.repository.MoPigRepository;
import com.modon.control.domain.repository.MoSensorSocketRepository;
import com.modon.control.dto.pig.PigBreathDto;
import com.modon.control.statistic.service.task.StatisticCommonTask;
import jakarta.transaction.Transactional;
import lombok.RequiredArgsConstructor;
import org.springframework.stereotype.Service;

import java.time.LocalDateTime;
import java.util.List;
import java.util.Map;
import java.util.Optional;

@Service
@RequiredArgsConstructor
public class PigBreathServiceImpl implements PigBreathService{

    private final MoPigBreathRepository moPigBreathRepository;
    private final StatisticCommonTask statisticCommonTask;
    private final MoSensorSocketRepository moSensorSocketRepository;
    private final MoPigRepository moPigRepository;

    @Override
    @Transactional
    public void deleteAllPigBreaths() {
        moPigBreathRepository.deleteAll();
    }

    @Override
    @Transactional
    public void setPigBreath() {
        Map<String, Map<String, LocalDateTime>> dataRanges = statisticCommonTask.calculateExactTimeRanges(LocalDateTime.now());

        // 각 시간 범위를 개별 변수에 할당
        LocalDateTime currentStart = dataRanges.get("current").get("start");

        LocalDateTime twoHoursStart = dataRanges.get("twoHours").get("start");
        LocalDateTime twoHoursEnd = dataRanges.get("twoHours").get("end");

        LocalDateTime twelveHoursStart = dataRanges.get("twelveHours").get("start");
        LocalDateTime twelveHoursEnd = dataRanges.get("twelveHours").get("end");

        LocalDateTime todayStart = dataRanges.get("today").get("start");
        LocalDateTime todayEnd = dataRanges.get("today").get("end");

        LocalDateTime yesterdayStart = dataRanges.get("yesterday").get("start");
        LocalDateTime yesterdayEnd = dataRanges.get("yesterday").get("end");

        LocalDateTime threeDaysStart = dataRanges.get("threeDays").get("start");
        LocalDateTime threeDaysEnd = dataRanges.get("threeDays").get("end");

        LocalDateTime oneWeekStart = dataRanges.get("oneWeek").get("start");
        LocalDateTime oneWeekEnd = dataRanges.get("oneWeek").get("end");

        LocalDateTime twoWeeksStart = dataRanges.get("twoWeeks").get("start");
        LocalDateTime twoWeeksEnd = dataRanges.get("twoWeeks").get("end");




        moSensorSocketRepository.findDistinctPigIdByDateTimeAfter(twoWeeksStart).forEach(pigCode -> {
            Optional<MoPig> moPigOptional = moPigRepository.findById(pigCode);
            if (moPigOptional.isPresent()) {
                MoPig moPig = moPigOptional.get();

                // 시간 범위 별 평균 호흡수 계산
                Double avgBreathTwoHours = calculateAverageBreathForTimeRange(moPig.getId(), twoHoursStart, twoHoursEnd);
                Double avgBreathToday = calculateAverageBreathForTimeRange(moPig.getId(), todayStart, todayEnd);
                Double avgBreathYesterday = calculateAverageBreathForTimeRange(moPig.getId(), yesterdayStart, yesterdayEnd);
                Double avgBreathThreeday = calculateAverageBreathForTimeRange(moPig.getId(), threeDaysStart, threeDaysEnd);
                Double avgBreathOneWeek = calculateAverageBreathForTimeRange(moPig.getId(), oneWeekStart, oneWeekEnd);
                Double avgBreathTwoWeek = calculateAverageBreathForTimeRange(moPig.getId(), twoWeeksStart, twoWeeksEnd);
                Double avgBreathTwelveHours = calculateAverageBreathForTimeRange(moPig.getId(), twelveHoursStart, twelveHoursEnd);
                ;
                // 생성된 MoPigBreath 객체를 데이터베이스에 저장
                moPigBreathRepository.save(MoPigBreath.builder()
                        .pigCode(moPig)
                        .avgBreathTwoHours(avgBreathTwoHours)
                        .avgBreathTwelveHours(avgBreathTwelveHours)
                        .avgBreathToday(avgBreathToday)
                        .avgBreathYesterday(avgBreathYesterday)
                        .avgBreathThreeDays(avgBreathThreeday)
                        .avgBreathLastWeek(avgBreathOneWeek)
                        .avgBreathTwoWeeks(avgBreathTwoWeek)
                        .lastUpdateDate(currentStart)
                        .build());
            }
        });
    }


    private Double calculateAverageBreathForTimeRange(Long pigId, LocalDateTime start, LocalDateTime end) {
        List<PigBreathDto> results = moSensorSocketRepository.findAverageBreathByPigIdsAndTimeRange(pigId, start, end);
        return results.isEmpty() ? 0.0 : results.get(0).getAverageBreath();
    }

}
