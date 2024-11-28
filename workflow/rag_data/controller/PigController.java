package com.modon.control.pig.controller;

import com.modon.control.common.type.TypeService;
import com.modon.control.common.util.CommUtil;
import com.modon.control.domain.entity.MoType;
import com.modon.control.domain.type.GenderType;
import com.modon.control.domain.type.LitterStatus;
import com.modon.control.domain.type.PigStatus;
import com.modon.control.domain.type.SensorStatus;
import com.modon.control.dto.common.ListDto;
import com.modon.control.dto.common.PageableDto;
import com.modon.control.dto.pig.*;
import com.modon.control.dto.sensor.*;
import com.modon.control.pig.service.PigService;
import jakarta.servlet.http.HttpServletRequest;
import lombok.RequiredArgsConstructor;
import org.springframework.data.domain.*;
import org.springframework.stereotype.Controller;
import org.springframework.ui.Model;
import org.springframework.web.bind.annotation.*;

import java.util.Arrays;
import java.util.Collections;
import java.util.List;
import java.util.Optional;

@Controller
@RequiredArgsConstructor
public class PigController {

    private final TypeService typeService;
    private final PigService pigService;

    private Optional<List<MoType>> getPigTypes() {
        return typeService.searchActiveType("2");
    }

    private Optional<List<PigStatus>> getPigStatues() {
        return Optional.of(Arrays.asList(PigStatus.values()));
    }

    private Optional<List<GenderType>> getPigGender() {
        return Optional.of(Arrays.asList(GenderType.values()));
    }

    @GetMapping("pig")
    public String pigMain(Model model, @ModelAttribute PigSearchDto pigSearchDto, HttpServletRequest request) {
        /* 검색필드용 유형 호출 */
        Optional<List<MoType>> moTypes = getPigTypes();

        /* 검색필드용 상태 호출 */
        Optional<List<PigStatus>> pigStatuses = getPigStatues();

        /* 검색필드용 성별 호출 */
        Optional<List<GenderType>> pigGender = getPigGender();

        model.addAttribute("pigTypes", moTypes.orElse(Collections.emptyList()));
        model.addAttribute("pigStatuses", pigStatuses.orElse(Collections.emptyList()));
        model.addAttribute("pigGender", pigGender.orElse(Collections.emptyList()));
        model.addAttribute("searchData", pigSearchDto);

        return CommUtil.determineViewPath(request, "pig/pig", null);
    }


    @GetMapping("pig/search")
    public String pigSearch(Model model, @ModelAttribute PigSearchDto pigSearchDto, HttpServletRequest request) {
        /* 검색필드용 유형 호출 */
        Optional<List<MoType>> moTypes = getPigTypes();

        /* 검색필드용 상태 호출 */
        Optional<List<PigStatus>> pigStatuses = getPigStatues();

        /* 검색필드용 성별 호출 */
        Optional<List<GenderType>> pigGender = getPigGender();

        model.addAttribute("pigTypes", moTypes.orElse(Collections.emptyList()));
        model.addAttribute("pigStatuses", pigStatuses.orElse(Collections.emptyList()));
        model.addAttribute("pigGender", pigGender.orElse(Collections.emptyList()));
        model.addAttribute("searchData", pigSearchDto);

        return CommUtil.determineViewPath(request, "pig/search", null);
    }

    @PostMapping("pig/list")
    public String pigList(Model model, @RequestBody ListDto listDto, HttpServletRequest request) {

        List<PigDto> pigs = (List<PigDto>) listDto.getContent();
        PageableDto pageableDto = listDto.getPageable();

        // Pageable 객체 생성
        Pageable pageable = PageRequest.of(pageableDto.getPageNumber(), pageableDto.getPageSize(), Sort.unsorted());

        // PageImpl 객체 생성
        Page<PigDto> pigPage = new PageImpl<>(pigs, pageable, listDto.getTotalElements());

        // 모델에 Page 객체 추가
        model.addAttribute("paging", pigPage);
        model.addAttribute("lists", pigs); // 내용 데이터 추가

        return CommUtil.determineViewPath(request, "pig/pig_list", null);
    }


    @GetMapping("pig/register")
    public String pigRegist(Model model) {
        /* 등록용 유형 호출 */
        Optional<List<MoType>> moTypes = getPigTypes();

        /* 등록용 상태 호출 */
        Optional<List<PigStatus>> pigStatuses = getPigStatues();

        /* 등록용 성별 호출 */
        Optional<List<GenderType>> pigGender = getPigGender();

        model.addAttribute("pigTypes", moTypes.orElse(Collections.emptyList()));
        model.addAttribute("pigStatuses", pigStatuses.orElse(Collections.emptyList()));
        model.addAttribute("pigGender", pigGender.orElse(Collections.emptyList()));

        return "pig/pig_register";
    }


    @GetMapping({
            "/pig/detail/images", // 양돈 이미지
            "/pig/detail/modify", // 기본정보수정
            "/pig/detail/litter", // 산차정보
            "/pig/detail/memo", // 관리메모
            "/pig/detail/change", // 변경이력
            "/pig/detail/history", // 배치이력
            "/pig/detail/data", // 생체데이터
            "/pig/detail/delete" // 정보삭제
    })
    public String pigDetail(
            @RequestParam("id") Long pigId,
            @ModelAttribute PigSearchDto pigSearchDto,
            HttpServletRequest request,
            Model model) {

        // URL 경로를 가져와서 "/"를 기준으로 나눈 후 마지막 부분을 action 변수에 할당
        String[] pathParts = request.getRequestURI().split("/");
        String action = pathParts[pathParts.length - 1];


        // 센서 공통영역은 항상 출력
        Optional<PigDetailDto> pigInfo = pigService.getPigDetail(pigId);

        // action에 따른 추가 정보 처리
        handleActionSpecificDetails(action, model);

        model.addAttribute("pageType", action);
        model.addAttribute("pigInfo", pigInfo.orElse(null));
        model.addAttribute("searchData", pigSearchDto);

        return CommUtil.determineViewPath(request, "pig/detail/" + action, null);
    }


    private void handleActionSpecificDetails(String action, Model model) {
        switch (action) {
            case "images":
                break;

            case "modify":
                prepareModifyPage(model);
                break;

            case "litter":
                prepareLitterPage(model);
                break;

            case "memo":
                break;

            case "change":
                break;

            case "history":
                // history 페이지 준비 로직
                break;

            case "data":
                // data 페이지 준비 로직
                break;
        }
    }

    private void prepareModifyPage(Model model) {
        /* 등록용 유형 호출 */
        Optional<List<MoType>> moTypes = getPigTypes();

        /* 등록용 상태 호출 */
        Optional<List<PigStatus>> pigStatuses = getPigStatues();

        /* 등록용 성별 호출 */
        Optional<List<GenderType>> pigGender = getPigGender();

        model.addAttribute("pigTypes", moTypes.orElse(Collections.emptyList()));
        model.addAttribute("pigStatuses", pigStatuses.orElse(Collections.emptyList()));
        model.addAttribute("pigGender", pigGender.orElse(Collections.emptyList()));
    }

    private void prepareLitterPage(Model model) {
        /* 등록용 상태 호출 */
        Optional<List<LitterStatus>> pigLitterStatuses = Optional.of(Arrays.asList(LitterStatus.values()));

        model.addAttribute("pigLitterStatuses", pigLitterStatuses.orElse(Collections.emptyList()));
    }


    @PostMapping("/pig/detail/memo/list")
    public String pigDetailMemoList(@RequestBody ListDto listDto, Model model, HttpServletRequest request) {

        List<PigMemoDto> pigMemos = (List<PigMemoDto>) listDto.getContent();
        PageableDto pageableDto = listDto.getPageable();

        // Pageable 객체 생성
        Pageable pageable = PageRequest.of(pageableDto.getPageNumber(), pageableDto.getPageSize(), Sort.unsorted());

        // PageImpl 객체 생성
        Page<PigMemoDto> sensorHistoryPage = new PageImpl<>(pigMemos, pageable, listDto.getTotalElements());

        // 모델에 Page 객체 추가
        model.addAttribute("paging", sensorHistoryPage);
        model.addAttribute("lists", pigMemos); // 내용 데이터 추가

        return CommUtil.determineViewPath(request, "pig/detail/memo/memo_list", null);
    }

    @PostMapping("/pig/detail/history/list")
    public String pigDetailHistoryList(@RequestBody ListDto listDto, Model model, HttpServletRequest request) {

        List<PigPlacementHistoryDto> pigHistorys = (List<PigPlacementHistoryDto>) listDto.getContent();
        PageableDto pageableDto = listDto.getPageable();

        // Pageable 객체 생성
        Pageable pageable = PageRequest.of(pageableDto.getPageNumber(), pageableDto.getPageSize(), Sort.unsorted());

        // PageImpl 객체 생성
        Page<PigPlacementHistoryDto> sensorHistoryPage = new PageImpl<>(pigHistorys, pageable, listDto.getTotalElements());

        // 모델에 Page 객체 추가
        model.addAttribute("paging", sensorHistoryPage);
        model.addAttribute("lists", pigHistorys); // 내용 데이터 추가

        return CommUtil.determineViewPath(request, "pig/detail/history/history_list", null);
    }

    @PostMapping("/pig/detail/data/list")
    public String pigDetailDataList(@RequestBody ListDto listDto, Model model, HttpServletRequest request) {

        List<SensorDataDto> sensorDatas = (List<SensorDataDto>) listDto.getContent();
        PageableDto pageableDto = listDto.getPageable();

        // Pageable 객체 생성
        Pageable pageable = PageRequest.of(pageableDto.getPageNumber(), pageableDto.getPageSize(), Sort.unsorted());

        // PageImpl 객체 생성
        Page<SensorDataDto> sensorDataPage = new PageImpl<>(sensorDatas, pageable, listDto.getTotalElements());

        // 모델에 Page 객체 추가
        model.addAttribute("paging", sensorDataPage);
        model.addAttribute("lists", sensorDatas); // 내용 데이터 추가

        return CommUtil.determineViewPath(request, "pig/detail/data/data_list", null);
    }

    @GetMapping("/pig/detail/litter/detail")
    public String pigDetailLitterDetail(
            @RequestParam("id") Long pigId,
            @RequestParam("litter") int litter,
            Model model, HttpServletRequest request) {

        Optional<PigDetailDto> pigInfo = pigService.getPigDetail(pigId);
        Optional<PigLitterDto> pigLitterDto = pigService.getPigLitterDetail(pigId, litter);

        handleActionSpecificDetails("litter", model);
        model.addAttribute("pageType", "litter");
        model.addAttribute("pigInfo", pigInfo.orElse(null));
        model.addAttribute("litter", pigLitterDto.orElse(new PigLitterDto()));
        model.addAttribute("litterNum", litter);


        return CommUtil.determineViewPath(request, "pig/detail/litter/detail", null);
    }


    @GetMapping("/pig/detail/data/detail")
    public String pigDetailDataDetail(
            @RequestParam("id") Long pigId,
            @RequestParam("data") Long data,
            Model model, HttpServletRequest request) {

        Optional<PigDetailDto> pigInfo = pigService.getPigDetail(pigId);
        Optional<SensorDataDto> sensorDataDto = pigService.getPigVital(data,pigId);

        handleActionSpecificDetails("data", model);
        model.addAttribute("pageType", "data");
        model.addAttribute("pigInfo", pigInfo.orElse(null));
        model.addAttribute("item", sensorDataDto.orElse(new SensorDataDto()));


        return CommUtil.determineViewPath(request, "pig/detail/data/detail", null);
    }

}
