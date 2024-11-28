package com.modon.control.pig.controller;

import com.modon.control.common.annotation.CustomAuth;
import com.modon.control.common.exception.SearchNotFoundException;
import com.modon.control.common.file.ExcelUtil;
import com.modon.control.common.transaction.ResultWrapper;
import com.modon.control.dto.common.RemoveDto;
import com.modon.control.dto.pig.*;
import com.modon.control.dto.sensor.SensorDataDto;
import com.modon.control.pig.service.PigService;
import io.swagger.v3.oas.annotations.Operation;
import io.swagger.v3.oas.annotations.tags.Tag;
import lombok.RequiredArgsConstructor;
import org.springframework.core.io.InputStreamResource;
import org.springframework.data.domain.Page;
import org.springframework.http.HttpHeaders;
import org.springframework.http.MediaType;
import org.springframework.http.ResponseEntity;
import org.springframework.web.bind.annotation.*;
import org.springframework.web.multipart.MultipartFile;

import java.io.*;
import java.util.ArrayList;
import java.util.List;
import java.util.Optional;

@Tag(name = "07 양돈관리 API", description = "양돈관리")
@RestController
@RequiredArgsConstructor
@RequestMapping("/api/pig")
public class PigRESTController {
    private final PigService pigService;

    // 관심양돈 count
    @Operation(summary = "관심양돈 카운트", description = "관심양돈 카운트")
    @PostMapping("/getManagementCnt")
    public ResponseEntity<ResultWrapper<Integer>> getManagementCnt(@RequestBody PigSearchDto pigSearchDto) {
        return pigService.getManagementCnt(pigSearchDto)
                .map(ResultWrapper::success)
                .map(ResponseEntity::ok)
                .orElseGet(() -> ResponseEntity.badRequest().build());
    }

    // 양돈 목록 조회 p07-001
    @Operation(summary = "양돈 목록 조회", description = "양돈 목록 조회")
    @GetMapping("/getPigList")
    @CustomAuth(menuId = "pig", groupId = "pig", permission = "read")
    public ResponseEntity<ResultWrapper<Page<PigDto>>> getPigList(@ModelAttribute PigSearchDto pigSearchDto) {
        return pigService.getListSearchType(pigSearchDto)
//                .filter(result -> !result.getContent().isEmpty()) // 검색결과가 없어도 나와야함
                .map(ResultWrapper::success)
                .map(ResponseEntity::ok)
                .orElseGet(() -> ResponseEntity.badRequest().build());
    }

    // 양돈 상세 조회 p07-002
    @Operation(summary = "양돈 상세 조회", description = "양돈 상세 조회")
    @GetMapping("/getPigDetail")
    @CustomAuth(menuId = "pig", groupId = "pig", permission = "read")
    public ResponseEntity<ResultWrapper<PigDetailDto>> getPigDetail(@RequestBody PigDetailDto pigDetailDto) {
        return pigService.getPigDetail(pigDetailDto.getId())
                .map(ResultWrapper::success)
                .map(ResponseEntity::ok)
                .orElseGet(() -> ResponseEntity.badRequest().build());
    }

    // 양돈 이미지 등록 p07-002
    @Operation(summary = "양돈 이미지 등록", description = "양돈 이미지 등록")
    @PostMapping(path = "/registPigImage", consumes = {"multipart/form-data"})
    @CustomAuth(menuId = "pig", groupId = "pig", permission = "update")
    public ResponseEntity<ResultWrapper<PigDto>> registPigImage(
            @RequestPart(name = "file1", required = false) MultipartFile file1
            , @RequestPart(name = "file2", required = false) MultipartFile file2
            , @RequestPart(name = "file3", required = false) MultipartFile file3
            , @RequestPart(name = "pigDto") PigDto pigDto) {

        // 받은 파일을 넣어준다.
        pigDto.setPigImgId1(file1);
        pigDto.setPigImgId2(file2);
        pigDto.setPigImgId3(file3);

        return pigService.registPigImage(pigDto)
                .map(ResultWrapper::success)
                .map(ResponseEntity::ok)
                .orElseGet(() -> ResponseEntity.badRequest().build());
    }

    // 양돈 이미지 삭제 p07-002
    @Operation(summary = "양돈 이미지 삭제", description = "양돈 이미지 삭제")
    @PostMapping("/deletePigImage")
    @CustomAuth(menuId = "pig", groupId = "pig", permission = "update")
    public ResponseEntity<ResultWrapper<Boolean>> deletePigImage(@RequestBody PigImgDeleteDto pigImgDeleteDto) {
        return pigService.deletePigImage(pigImgDeleteDto)
                .map(ResultWrapper::success)
                .map(ResponseEntity::ok)
                .orElseGet(() -> ResponseEntity.badRequest().build());

    }

    // 양돈 정보 수정 p07-003
    // 양돈 수정 p07-011
    @Operation(summary = "양돈 정보 수정", description = "양돈 정보 수정")
    @PostMapping("/updatePig")
    @CustomAuth(menuId = "pig", groupId = "pig", permission = "update")
    public ResponseEntity<ResultWrapper<Boolean>> updatePig(@RequestBody PigDto pigDto) {
        return pigService.updatePig(pigDto)
                .map(ResultWrapper::success)
                .map(ResponseEntity::ok)
                .orElseGet(() -> ResponseEntity.badRequest().build());
    }

    // 양돈 산차정보 등록/수정 p07-004
    @Operation(summary = "양돈 산차정보 등록/수정", description = "양돈 산차정보 등록/수정")
    @PostMapping("/registPigBirth")
    @CustomAuth(menuId = "pig", groupId = "pig", permission = "update")
    public ResponseEntity<ResultWrapper<PigLitterDto>> registPigBirth(@RequestBody PigLitterDto pigLitterDto) {
        return pigService.registPigBirth(pigLitterDto)
                .map(ResultWrapper::success)
                .map(ResponseEntity::ok)
                .orElseGet(() -> ResponseEntity.badRequest().build());
    }

    // 양돈 산차이력 조회 p07-004-01
    @Operation(summary = "양돈 산차이력 조회", description = "양돈 산차이력 조회")
    @GetMapping("/getPigLitterHistory")
    @CustomAuth(menuId = "pig", groupId = "pig", permission = "read")
    public ResponseEntity<ResultWrapper<List<PigLitterDto>>> getPigLitterHistory(@RequestBody PigDto pigDto) {
        return pigService.getPigLitterList(pigDto.getId())
                .map(ResultWrapper::success)
                .map(ResponseEntity::ok)
                .orElseGet(() -> ResponseEntity.badRequest().build());
    }

    // 양돈 관리메모 찾기 p07-005
    @Operation(summary = "양돈 관리메모 찾기", description = "양돈 관리메모 찾기")
    @GetMapping("/getPigMemoList")
    @CustomAuth(menuId = "pig", groupId = "pig", permission = "read")
    public ResponseEntity<ResultWrapper<Page<PigMemoDto>>> getPigMemoList(@ModelAttribute PigSearchDto pigSearchDto) {
        return pigService.getPigMemoList(pigSearchDto)
//                .filter(result -> !result.getContent().isEmpty())
                .map(ResultWrapper::success)
                .map(ResponseEntity::ok)
                .orElseGet(() -> ResponseEntity.badRequest().build());
    }


    // 양돈 관리메모 등록 p07-005
    @Operation(summary = "양돈 관리메모 등록", description = "양돈 관리메모 등록")
    @PostMapping("/registPigMemo")
    @CustomAuth(menuId = "pig", groupId = "pig", permission = "create")
    public ResponseEntity<ResultWrapper<Boolean>> registPigMemo(@RequestBody PigMemoDto pigMemoDto) {
        return pigService.registPigMemo(pigMemoDto)
                .map(ResultWrapper::success)
                .map(ResponseEntity::ok)
                .orElseGet(() -> ResponseEntity.badRequest().build());
    }

    // 양돈 변경이력 찾기 p07-006
    @Operation(summary = "양돈 변경이력 찾기", description = "양돈 변경이력 찾기")
    @GetMapping("/getPigHistory")
    @CustomAuth(menuId = "pig", groupId = "pig", permission = "read")
    public ResponseEntity<ResultWrapper<Page<PigHistoryDto>>> getPigChangeHistory(@ModelAttribute PigSearchDto pigSearchDto) {
        return pigService.getPigChangeHistory(pigSearchDto)
                .map(ResultWrapper::success)
                .map(ResponseEntity::ok)
                .orElseGet(() -> ResponseEntity.badRequest().build());
    }

    // 양돈 배치이력 찾기 p07-007
    @Operation(summary = "양돈 배치이력 찾기", description = "양돈 배치이력 찾기")
    @GetMapping("/getPigPlacementHistory")
    @CustomAuth(menuId = "pig", groupId = "pig", permission = "read")
    public ResponseEntity<ResultWrapper<Page<PigPlacementHistoryDto>>> getPigPlacementHistory(@ModelAttribute PigSearchDto pigSearchDto) {
        return pigService.getPigPlacementHistory(pigSearchDto)
                .map(ResultWrapper::success)
                .map(ResponseEntity::ok)
                .orElseGet(() -> ResponseEntity.badRequest().build());
    }

    // 양돈 생체데이터 찾기 p07-008
    @Operation(summary = "양돈 생체데이터 찾기", description = "양돈 생체데이터 찾기")
    @GetMapping("/getPigVitalData")
    @CustomAuth(menuId = "pig", groupId = "pig", permission = "read")
    public ResponseEntity<ResultWrapper<Page<SensorDataDto>>> getPigVitalData(@ModelAttribute PigSearchDto pigSearchDto) {
        return pigService.getPigVitalData(pigSearchDto)
                .map(ResultWrapper::success)
                .map(ResponseEntity::ok)
                .orElseGet(() -> ResponseEntity.badRequest().build());
    }

    // 양돈 정보 삭제 p07-009
    @Operation(summary = "양돈 정보 삭제", description = "양돈 정보 삭제")
    @PostMapping("/deletePig")
    @CustomAuth(menuId = "pig", groupId = "pig", permission = "delete")
    public ResponseEntity<ResultWrapper<RemoveDto>> deletePig(@RequestBody RemoveDto removeDto) {
        return pigService.deletePig(removeDto)
                .map(ResultWrapper::success)
                .map(ResponseEntity::ok)
                .orElseGet(() -> ResponseEntity.badRequest().build());
    }

    // 양돈 등록 p07-010
    @Operation(summary = "양돈 등록", description = "양돈 등록")
    @PostMapping("/registPig")
    @CustomAuth(menuId = "pig", groupId = "pig", permission = "create")
    public ResponseEntity<ResultWrapper<PigDto>> registPig(
            @RequestPart(name = "file1", required = false) MultipartFile file1
            , @RequestPart(name = "file2", required = false) MultipartFile file2
            , @RequestPart(name = "file3", required = false) MultipartFile file3
            , @RequestPart(name = "pigDto") PigDto pigDto) {

        // 받은 파일을 넣어준다.
        pigDto.setPigImgId1(file1);
        pigDto.setPigImgId2(file2);
        pigDto.setPigImgId3(file3);

        return pigService.registPig(pigDto)
                .map(ResultWrapper::success)
                .map(ResponseEntity::ok)
                .orElseGet(() -> ResponseEntity.badRequest().build());
    }


    //    public ResponseEntity<ResultWrapper<Page<PigDto>>> getPigList(@ModelAttribute PigSearchDto pigSearchDto) {
//        return pigService.getListSearchType(pigSearchDto)
////                .filter(result -> !result.getContent().isEmpty()) // 검색결과가 없어도 나와야함
//                .map(ResultWrapper::success)
//                .map(ResponseEntity::ok)
//                .orElseGet(() -> ResponseEntity.badRequest().build());
//    }
    @Operation(summary = "돼지 엑셀 다운로드", description = "검색양식 유지 & 10,000개까지 분할로 나눠 작업")
    @GetMapping("/getExcel")
    @CustomAuth(menuId = "pig", groupId = "pig", permission = "read")
    public ResponseEntity<?> getExcel(@ModelAttribute PigSearchDto pigSearchDto) throws IOException {
        // 데이터 조회
        Optional<List<PigDto>> optionalDataList = pigService.getAllListSearchType(pigSearchDto);

        if (optionalDataList.isEmpty() || optionalDataList.get().isEmpty()) {
            throw new SearchNotFoundException("변환할 데이터가 존재하지 않습니다.");
        }

        List<PigDto> dataList = optionalDataList.get();

        // 데이터 분할 및 엑셀 파일 생성
        List<File> excelFiles = new ArrayList<>();
        final int chunkSize = 10000;
        ExcelUtil excelUtil = new ExcelUtil(); // ExcelUtil 인스턴스 생성

        // 파일 이름에 현재 시간과 파일 개수를 포함
        String baseFileName = "pig_data";
        String timeStamp = String.valueOf(System.currentTimeMillis());
        String tempDir = System.getProperty("java.io.tmpdir");
        for (int i = 0, fileCount = 1; i < dataList.size(); i += chunkSize, fileCount++) {
            List<PigDto> chunk = dataList.subList(i, Math.min(dataList.size(), i + chunkSize));
            String fileName = baseFileName + "_" + timeStamp + "_" + fileCount + ".xlsx";
            File tempFile = new File(tempDir + File.separator + fileName);

            try (OutputStream os = new FileOutputStream(tempFile)) {
                excelUtil.renderObjectToExcel(os, chunk, PigDto.class);
            }
            excelFiles.add(tempFile);
        }

        // 파일이 여러 개인 경우 ZIP으로 묶기
        File finalFile;
        if (excelFiles.size() > 1) {
            finalFile = excelUtil.createZipFile(excelFiles, "pig_data");
        } else {
            finalFile = excelFiles.get(0);
        }

        // 파일을 클라이언트에게 전송
        HttpHeaders headers = new HttpHeaders();
        headers.add(HttpHeaders.CONTENT_DISPOSITION, "attachment; filename=" + finalFile.getName());

        InputStreamResource resource = new InputStreamResource(new FileInputStream(finalFile));
        return ResponseEntity.ok()
                .headers(headers)
                .contentLength(finalFile.length())
                .contentType(MediaType.parseMediaType("application/octet-stream"))
                .body(resource);
    }

}
