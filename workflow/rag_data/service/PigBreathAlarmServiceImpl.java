package com.modon.control.pig.service;

import com.modon.control.alarm.service.AlarmService;
import com.modon.control.domain.entity.*;
import com.modon.control.domain.repository.*;
import com.modon.control.dto.alarm.AlarmDto;
import com.modon.control.dto.pig.PigAlarmDto;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.PageRequest;
import org.springframework.stereotype.Repository;
import org.springframework.stereotype.Service;

import java.time.LocalDate;
import java.time.LocalDateTime;
import java.time.format.DateTimeFormatter;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

@RequiredArgsConstructor
@Service
public class PigBreathAlarmServiceImpl implements PigBreathAlarmService {
    private final MoFarmRepository moFarmRepository;
    private final MoPigBreathRepository moPigBreathRepository;
    private final MoPigRepository moPigRepository;
    private final MoPigLitterRepository moPigLitterRepository;
    private final MoPigAlarmHistoryRepository moPigAlarmHistoryRepository;
    private final MoPigFarrowingScheduleRepository moPigFarrowingScheduleRepository;
    private final MoPigEmergencyRepository moPigEmergencyRepository;
    private final MoConfigSmsRepository moConfigSmsRepository;
    private final AlarmService alarmService;


    private static final DateTimeFormatter formatter = DateTimeFormatter.ofPattern("yyyy년 MM월 dd일");


    // 특정 조건에 따라 알람 이력과 예정건을 등록하는 메서드
    private void processAlarm(MoPigLitter moPigLitter, MoPig moPig, MoConfigSms moConfigSms, LocalDate expectedDate, List<String> pigIdentifications) {
        // 알람 이력 검사 및 등록/업데이트
        MoPigAlarmHistory existingAlarmHistory = moPigAlarmHistoryRepository.findByMoPigLitterAndMoConfigSms(moPigLitter, moConfigSms);
        if (existingAlarmHistory == null) {
            moPigAlarmHistoryRepository.save(
                    MoPigAlarmHistory.builder()
                            .moPigLitter(moPigLitter)
                            .moConfigSms(moConfigSms)
                            .messageSent(false)
                            .build()
            );
        }

        // 분만 예정건 검사 및 등록/업데이트
        MoPigFarrowingSchedule existingFarrowingSchedule = moPigFarrowingScheduleRepository.findByMoPigAndMoPigLitter(moPig, moPigLitter);
        if (existingFarrowingSchedule == null) {
            moPigFarrowingScheduleRepository.save(
                    MoPigFarrowingSchedule.builder()
                            .moPig(moPig)
                            .moPigLitter(moPigLitter)
                            .expectedFarrowingDate(expectedDate)
                            .build()
            );
        }

        // 문자 발송 대상 목록에 양돈 ID 추가 (중복 제거 로직 포함)
        String pigIdentification = moPigLitter.getPigIdentification();
        if (!pigIdentifications.contains(pigIdentification)) {
            pigIdentifications.add(pigIdentification);
        }
    }


    private void twoWeekAct(
            MoFarm moFarm,
            MoPigBreath moPigBreath,
            MoPigLitter moPigLitter,
            MoPig moPig,
            AlarmDto alarmTwoWeek,
            MoConfigSms moConfigSmsTwoWeek,
            LocalDate date,
            List<String> twoWeekPigs) {

        // 2주전 체크 로직 (1주전 호흡수보다 당일의 호흡수가 10%이상 증가 && 호흡수 100초과 && 120이하)
        if (moPigBreath.getAvgBreathLastWeek() != null &&
                moPigBreath.getAvgBreathToday() > moPigBreath.getAvgBreathLastWeek() * 1.1 &&
                moPigBreath.getAvgBreathToday() > 100 &&
                moPigBreath.getAvgBreathToday() <= 120
        ) {

            // 2주 전 조건이 만족되면 이전 알람 이력 확인
            List<MoPigAlarmHistory> alarmHistories = moPigAlarmHistoryRepository.findByMoPigLitter(moPigLitter);

            for (MoPigAlarmHistory alarmHistory : alarmHistories) {
                // 각 조건에 해당하는 CONFIG_SMS_CODE를 확인하여 이력 존재 여부 확인
                // 해당 산차의 2주전 알람이 등록되어있다면 문자발송이 되지 않은경우 || 1주전 알람이 등록된 경우 || 3일전 알람이 등록된경우 || 1일전 알람이 등록된경우 를 건너뛴다.
                if ((alarmHistory.getMoConfigSms().getId().equals(10L) && alarmHistory.isMessageSent()) ||
                        alarmHistory.getMoConfigSms().getId().equals(11L) ||
                        alarmHistory.getMoConfigSms().getId().equals(12L) ||
                        alarmHistory.getMoConfigSms().getId().equals(13L)
                ) {
                    // 이전에 "1주 전", "3일 전", "1일 전" 알람이 발송된 이력이 있다면 로직 종료
                    return;
                }
                processAlarm(moPigLitter, moPig, moConfigSmsTwoWeek, date, twoWeekPigs);
            }

            if (alarmHistories.isEmpty()) {
                processAlarm(moPigLitter, moPig, moConfigSmsTwoWeek, date, twoWeekPigs);
            }

            // 2주전 양돈이 존재할경우 (알림발송)
            if (!twoWeekPigs.isEmpty()) {
                alarmTwoWeek.setPigAlarmDto(
                        PigAlarmDto
                                .builder()
                                .pigIdentifications(twoWeekPigs)
                                .expectedFarrowingDate(date.format(formatter))
                                .moFarm(moFarm)
                                .build()
                );
                alarmService.setAlarm(alarmTwoWeek);

                MoPigAlarmHistory existingAlarmHistory = moPigAlarmHistoryRepository.findByMoPigLitterAndMoConfigSms(moPigLitter, moConfigSmsTwoWeek);
                if (existingAlarmHistory != null) {
                    existingAlarmHistory.setMessageSent(true);
                    moPigAlarmHistoryRepository.save(existingAlarmHistory);
                }
            }

        }
    }


    private void oneWeekAct(
            MoFarm moFarm,
            MoPigBreath moPigBreath,
            MoPigLitter moPigLitter,
            MoPig moPig,
            AlarmDto alarmOneWeek,
            MoConfigSms moConfigSmsOneWeek,
            LocalDate date,
            List<String> oneWeekPigs) {

        // 1주전 체크 로직 (호흡수 120초과 && 140이하)
        if (moPigBreath.getAvgBreathLastWeek() != null &&
                moPigBreath.getAvgBreathToday() > 120 &&
                moPigBreath.getAvgBreathToday() <= 140
        ) {

            // 1주 전 조건이 만족되면 이전 알람 이력 확인
            List<MoPigAlarmHistory> alarmHistories = moPigAlarmHistoryRepository.findByMoPigLitter(moPigLitter);

            for (MoPigAlarmHistory alarmHistory : alarmHistories) {
                // 각 조건에 해당하는 CONFIG_SMS_CODE를 확인하여 이력 존재 여부 확인
                // 해당 산차의 1주전 알람이 등록되어있다면 문자발송이 되지 않은경우 || 3일전 알람이 등록된경우 || 1일전 알람이 등록된경우 를 건너뛴다.
                if ((alarmHistory.getMoConfigSms().getId().equals(11L) && alarmHistory.isMessageSent()) ||
                        alarmHistory.getMoConfigSms().getId().equals(12L) ||
                        alarmHistory.getMoConfigSms().getId().equals(13L)
                ) {
                    // 이전에 "3일 전", "1일 전" 알람이 발송된 이력이 있다면 로직 종료
                    return;
                }
                processAlarm(moPigLitter, moPig, moConfigSmsOneWeek, date, oneWeekPigs);
            }

            if (alarmHistories.isEmpty()) {
                processAlarm(moPigLitter, moPig, moConfigSmsOneWeek, date, oneWeekPigs);
            }

            // 2주전 양돈이 존재할경우 (알림발송)
            if (!oneWeekPigs.isEmpty()) {
                alarmOneWeek.setPigAlarmDto(
                        PigAlarmDto
                                .builder()
                                .pigIdentifications(oneWeekPigs)
                                .expectedFarrowingDate(date.format(formatter))
                                .moFarm(moFarm)
                                .build()
                );
                alarmService.setAlarm(alarmOneWeek);

                MoPigAlarmHistory existingAlarmHistory = moPigAlarmHistoryRepository.findByMoPigLitterAndMoConfigSms(moPigLitter, moConfigSmsOneWeek);
                if (existingAlarmHistory != null) {
                    existingAlarmHistory.setMessageSent(true);
                    moPigAlarmHistoryRepository.save(existingAlarmHistory);
                }
            }

        }
    }


    private void threeDaysAct(
            MoFarm moFarm,
            MoPigBreath moPigBreath,
            MoPigLitter moPigLitter,
            MoPig moPig,
            AlarmDto alarmThreeDays,
            MoConfigSms moConfigSmsThreeDays,
            LocalDate date,
            List<String> threeDaysPigs) {

        // 3일전 체크 로직 (호흡수 140초과 && 160이하)
        if (moPigBreath.getAvgBreathLastWeek() != null &&
                moPigBreath.getAvgBreathToday() > 140 &&
                moPigBreath.getAvgBreathToday() <= 160
        ) {

            // 3일전 조건이 만족되면 이전 알람 이력 확인
            List<MoPigAlarmHistory> alarmHistories = moPigAlarmHistoryRepository.findByMoPigLitter(moPigLitter);

            for (MoPigAlarmHistory alarmHistory : alarmHistories) {
                // 각 조건에 해당하는 CONFIG_SMS_CODE를 확인하여 이력 존재 여부 확인
                // 해당 산차의 3일전 알람이 등록되어있다면 문자발송이 되지 않은경우 || 1일전 알람이 등록된경우 를 건너뛴다.
                if ((alarmHistory.getMoConfigSms().getId().equals(12L) && alarmHistory.isMessageSent()) ||
                        alarmHistory.getMoConfigSms().getId().equals(13L)
                ) {
                    // 이전에 "1일 전" 알람이 발송된 이력이 있다면 로직 종료
                    return;
                }
                processAlarm(moPigLitter, moPig, moConfigSmsThreeDays, date, threeDaysPigs);
            }

            if (alarmHistories.isEmpty()) {
                processAlarm(moPigLitter, moPig, moConfigSmsThreeDays, date, threeDaysPigs);
            }

            // 2주전 양돈이 존재할경우 (알림발송)
            if (!threeDaysPigs.isEmpty()) {
                alarmThreeDays.setPigAlarmDto(
                        PigAlarmDto
                                .builder()
                                .pigIdentifications(threeDaysPigs)
                                .expectedFarrowingDate(date.format(formatter))
                                .moFarm(moFarm)
                                .build()
                );
                alarmService.setAlarm(alarmThreeDays);

                MoPigAlarmHistory existingAlarmHistory = moPigAlarmHistoryRepository.findByMoPigLitterAndMoConfigSms(moPigLitter, moConfigSmsThreeDays);
                if (existingAlarmHistory != null) {
                    existingAlarmHistory.setMessageSent(true);
                    moPigAlarmHistoryRepository.save(existingAlarmHistory);
                }
            }

        }
    }


    private void oneDaysAct(
            MoFarm moFarm,
            MoPigBreath moPigBreath,
            MoPigLitter moPigLitter,
            MoPig moPig,
            AlarmDto alarmOneDays,
            MoConfigSms moConfigSmsOneDays,
            LocalDate date,
            List<String> oneDaysPigs) {

        // 1일전 체크 로직 (호흡수 160초과)
        if (moPigBreath.getAvgBreathLastWeek() != null &&
                moPigBreath.getAvgBreathToday() > 160
        ) {

            // 3일전 조건이 만족되면 이전 알람 이력 확인
            List<MoPigAlarmHistory> alarmHistories = moPigAlarmHistoryRepository.findByMoPigLitter(moPigLitter);

            for (MoPigAlarmHistory alarmHistory : alarmHistories) {
                // 각 조건에 해당하는 CONFIG_SMS_CODE를 확인하여 이력 존재 여부 확인
                // 해당 산차의 1일전 알람이 등록되어있다면 문자발송이 되지 않은경우
                if ((alarmHistory.getMoConfigSms().getId().equals(13L) && alarmHistory.isMessageSent())) {
                    return;
                }
                processAlarm(moPigLitter, moPig, moConfigSmsOneDays, date, oneDaysPigs);
            }

            if (alarmHistories.isEmpty()) {
                processAlarm(moPigLitter, moPig, moConfigSmsOneDays, date, oneDaysPigs);
            }

            // 2주전 양돈이 존재할경우 (알림발송)
            if (!oneDaysPigs.isEmpty()) {
                alarmOneDays.setPigAlarmDto(
                        PigAlarmDto
                                .builder()
                                .pigIdentifications(oneDaysPigs)
                                .expectedFarrowingDate(date.format(formatter))
                                .moFarm(moFarm)
                                .build()
                );
                alarmService.setAlarm(alarmOneDays);

                MoPigAlarmHistory existingAlarmHistory = moPigAlarmHistoryRepository.findByMoPigLitterAndMoConfigSms(moPigLitter, moConfigSmsOneDays);
                if (existingAlarmHistory != null) {
                    existingAlarmHistory.setMessageSent(true);
                    moPigAlarmHistoryRepository.save(existingAlarmHistory);
                }
            }

        }
    }

    private void emergencyAct(
            MoFarm moFarm,
            MoPigBreath moPigBreath,
            MoPig moPig,
            AlarmDto alarmEmergency,
            MoConfigSms moConfigEmergency) {

        // 긴급 체크 로직 (하루전 호흡수보다 2시간전 호흡수가 20%이상 증가 && 2시간 호흡수 180초과)
        if (moPigBreath.getAvgBreathLastWeek() != null &&
                moPigBreath.getAvgBreathTwoHours() > moPigBreath.getAvgBreathYesterday() * 1.2 &&
                moPigBreath.getAvgBreathTwoHours() > 180
        ) {


            // 1일경과 응급상황 전부 삭제
            moPigEmergencyRepository.deleteOlderThanTenDays(LocalDateTime.now().minusDays(1));


            // 응급알림 발송이력이 존재하지 않는 양돈 출력
            MoPigEmergencyHistory moPigEmergencyHistory = moPigEmergencyRepository.findByMoPig(moPig).orElse(null);

            if (moPigEmergencyHistory == null) {
                alarmEmergency.setMoConfigSms(moConfigEmergency);
                alarmEmergency.setPigAlarmDto(
                        PigAlarmDto
                                .builder()
                                .pigIdentification(moPigBreath.getPigCode().getPigIdentification())
                                .moFarm(moFarm)
                                .avgBreathTwoHours(moPigBreath.getAvgBreathTwoHours())
                                .build()
                );
                alarmService.setAlarm(alarmEmergency);


                moPigEmergencyRepository.save(
                        MoPigEmergencyHistory
                                .builder()
                                .moPig(moPig)
                                .regDate(LocalDateTime.now())
                                .build()
                );
            }

        }
    }

    @Override
    public void setPigAlarmHistory() {

        LocalDate now = LocalDate.now();
        moFarmRepository.findAll().forEach(moFarm -> {
            // 2주전 알람 발송
            MoConfigSms moConfigSmsTwoWeek = moConfigSmsRepository.findById(10L).orElseThrow(() -> new RuntimeException("Config SMS not found"));
            AlarmDto alarmTwoWeek = AlarmDto.builder().moConfigSms(moConfigSmsTwoWeek).build();
            List<String> twoWeekPigs = new ArrayList<>();

            // 1주전 알람 발송
            MoConfigSms moConfigSmsOneWeek = moConfigSmsRepository.findById(11L).orElseThrow(() -> new RuntimeException("Config SMS not found"));
            AlarmDto alarmOneWeek = AlarmDto.builder().moConfigSms(moConfigSmsOneWeek).build();
            List<String> oneWeekPigs = new ArrayList<>();

            // 3일전 알람 발송
            MoConfigSms moConfigSmsThreeDays = moConfigSmsRepository.findById(12L).orElseThrow(() -> new RuntimeException("Config SMS not found"));
            AlarmDto alarmThreeDays = AlarmDto.builder().moConfigSms(moConfigSmsThreeDays).build();
            List<String> threeDaysPigs = new ArrayList<>();

            // 1일전 알람 발송
            MoConfigSms moConfigSmsOneDays = moConfigSmsRepository.findById(13L).orElseThrow(() -> new RuntimeException("Config SMS not found"));
            AlarmDto alarmOneDays = AlarmDto.builder().moConfigSms(moConfigSmsOneDays).build();
            List<String> oneDaysPigs = new ArrayList<>();

            // 긴급 알람 발송
            MoConfigSms moConfigEmergency = moConfigSmsRepository.findById(9L).orElseThrow(() -> new RuntimeException("Config SMS not found"));
            AlarmDto alarmEmergency = AlarmDto.builder().moConfigSms(moConfigEmergency).build();

            // 먼저 호흡통계가 잡힌 양돈중 해당 농장에 소속된 양돈을 순회한다.
            moPigBreathRepository.findByFarm(moFarm).forEach(moPigBreath -> {
                // 양돈의 정보
                MoPig moPig = moPigBreath.getPigCode();
                Optional<MoPigLitter> moPigLitterOptional = moPigLitterRepository.findLatestLitterByPigCode(moPig, PageRequest.of(0, 1))
                        .stream().findFirst();

                // 등록된 산차가 존재할경우
                if (moPigLitterOptional.isPresent()) {

                    MoPigLitter moPigLitter = moPigLitterOptional.get();
                    // 2주전
                    twoWeekAct(moFarm, moPigBreath, moPigLitter, moPig, alarmTwoWeek, moConfigSmsTwoWeek, now.plusWeeks(2), twoWeekPigs);

                    // 1주전
                    oneWeekAct(moFarm, moPigBreath, moPigLitter, moPig, alarmOneWeek, moConfigSmsOneWeek, now.plusWeeks(1), oneWeekPigs);

                    // 3일전
                    threeDaysAct(moFarm, moPigBreath, moPigLitter, moPig, alarmThreeDays, moConfigSmsThreeDays, now.plusDays(3), threeDaysPigs);

                    // 1일전
                    oneDaysAct(moFarm, moPigBreath, moPigLitter, moPig, alarmOneDays, moConfigSmsOneDays, now.plusDays(1), oneDaysPigs);
                }

                // 긴급
                emergencyAct(moFarm, moPigBreath, moPig, alarmEmergency, moConfigEmergency);

            });
        });
    }

    @Override
    public void setFarrowingDaysAlarm() {
        LocalDate now = LocalDate.now();
        MoConfigSms moConfigSms = moConfigSmsRepository.findById(1L).orElseThrow(() -> new RuntimeException("Config SMS not found"));
        AlarmDto alarmDto = AlarmDto.builder().moConfigSms(moConfigSms).build();
        moFarmRepository.findAll().forEach(moFarm -> {
            List<String> farrowingDayPigs = new ArrayList<>();

            // 각 농장별 분만 예정 양돈중 예정일이 당일이고, realFarrowingDate가 입력되지 않은 양돈의 목록을 가져옴
            List<MoPigFarrowingSchedule> schedules = moPigFarrowingScheduleRepository.findUnconfirmedFarrowingSchedulesByFarmAndDate(moFarm, now);
            for (MoPigFarrowingSchedule schedule : schedules) {
                String pigIdentification = schedule.getMoPig().getPigIdentification();
                farrowingDayPigs.add(pigIdentification);
            }

            if (!farrowingDayPigs.isEmpty()) {
                alarmDto.setMoConfigSms(moConfigSms);
                alarmDto.setPigAlarmDto(
                        PigAlarmDto
                                .builder()
                                .pigIdentifications(farrowingDayPigs)
                                .expectedFarrowingDate(now.format(formatter))
                                .moFarm(moFarm)
                                .build()
                );
                alarmService.setAlarm(alarmDto);
            }
        });
    }

    @Override
    public void setFarrowingDelayAlarm() {
        LocalDate now = LocalDate.now();
        MoConfigSms moConfigSms = moConfigSmsRepository.findById(2L).orElseThrow(() -> new RuntimeException("Config SMS not found"));
        AlarmDto alarmDto = AlarmDto.builder().moConfigSms(moConfigSms).build();

        moFarmRepository.findAll().forEach(moFarm -> {

            List<String> farrowingPigs = new ArrayList<>();
            // 각 농장별 분만 예정 양돈중 예정일이 당일보다 작고, realFarrowingDate가 입력되지 않은 양돈의 목록을 가져옴
            List<MoPigFarrowingSchedule> schedules = moPigFarrowingScheduleRepository.findOverdueUnconfirmedFarrowingSchedulesByFarm(moFarm, now);
            for (MoPigFarrowingSchedule schedule : schedules) {
                String pigIdentification = schedule.getMoPig().getPigIdentification();
                farrowingPigs.add(pigIdentification);
            }

            if (!farrowingPigs.isEmpty()) {
                alarmDto.setMoConfigSms(moConfigSms);
                alarmDto.setPigAlarmDto(
                        PigAlarmDto
                                .builder()
                                .pigIdentifications(farrowingPigs)
                                .expectedFarrowingDate(now.format(formatter))
                                .moFarm(moFarm)
                                .build()
                );
                alarmService.setAlarm(alarmDto);
            }
        });
    }
}
