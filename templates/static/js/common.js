const common = {
  // HTTP Get 요청
  getRequest: function (url, params, successFunc, failFunc) {
    $.ajax({
      url: url,
      type: "GET",
      contentType: "application/json",
      data: params,
      beforeSend: function () {
        showLoading(); // 요청 전 로딩 표시
      },
      success: function (data) {
        if (successFunc) successFunc(data);
      },
      error: function (data) {
        hideLoading();
        console.log("fail:" + data);
        if (failFunc) failFunc(data);

        if (data?.responseJSON?.message) {
          alert(data.responseJSON.message);
        } else if (data?.responseText) {
          alert(data.responseText);
        } else {
          alert("처리 중 오류가 발생하였습니다.");
        }
      },
      complete: function () {
        hideLoading(); // 요청 완료 후 로딩 숨김
      },
    });
  },
  // HTTP Post 요청
  postRequest: function (url, params, successFunc, failFunc) {
    $.ajax({
      url: url,
      type: "POST",
      contentType: "application/json",
      data: JSON.stringify(params),
      beforeSend: function () {
        showLoading(); // 요청 전 로딩 표시
      },
      success: function (data) {
        if (successFunc) successFunc(data);
      },
      error: function (data) {
        hideLoading();
        debugger;
        console.log("fail:" + data);
        if (data?.responseJSON?.message) {
          alert(data.responseJSON.message);
        } else if (data?.responseText) {
          alert(data.responseText);
        } else {
          alert("처리 중 오류가 발생하였습니다.");
        }

        if (failFunc) failFunc(data);
      },
      complete: function () {
        hideLoading(); // 요청 완료 후 로딩 숨김
      },
    });
  },
  //HTTP 스트림 요청
  postStreamRequest: function (url, params, onprogress, successFunc, failFunc, completeFunc) {
    $.ajax({
      url: url,
      type: "POST",
      contentType: "application/json",
      data: JSON.stringify(params),
      xhrFields: {
        onprogress: function (e) {
          if (onprogress) onprogress(e);
        },
      },

      // xhrFields: function (e) {
      //   debugger;
      //   if (onprogress) onprogress(e);
      // },
      success: function (data) {
        if (successFunc) successFunc(data);
      },
      fail: function (data) {
        if (failFunc) failFunc(data);
      },
      complete: function () {
        if (completeFunc) completeFunc();
      },
    });
  },
  //플러그인으로 메시지 전송
  sendTextToPlugin: function (type, message, successFunc, failFunc) {
    if (!window.cefQuery) {
      alert("Eclipse Plugin에서 실행되지 않았거나, 플러그인 설정이 올바르지 않습니다.");
      return;
    }

    let request = { type: type, message: message };

    window.cefQuery({
      request: JSON.stringify(request),
      onSuccess: function () {
        console.log("success");
        if (successFunc) successFunc();
      },
      onFailure: function () {
        console.log("error");
        if (failFunc) failFunc();
      },
    });
  },
  //클립보드 복사
  copyTextToClipboard: function (text, successFunc, failFunc) {
    navigator.clipboard.writeText(text).then(
      function () {
        if (successFunc) successFunc();
      },
      function (err) {
        if (failFunc) failFunc();
      }
    );
  },
};
