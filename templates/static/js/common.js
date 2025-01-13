const common = {
  getRequest: function (url, params, successFunc, failFunc) {
    $.ajax({
      url: url,
      type: "GET",
      contentType: "application/json",
      data: JSON.stringify(params),
      beforeSend: function () {
        showLoading(); // 요청 전 로딩 표시
      },
      success: function (data) {
        if (successFunc) successFunc(data);
      },
      fail: function (data) {
        if (failFunc) failFunc(data);
      },
      complete: function () {
        hideLoading(); // 요청 완료 후 로딩 숨김
      },
    });
  },
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
      fail: function (data) {
        if (failFunc) failFunc(data);
      },
      complete: function () {
        hideLoading(); // 요청 완료 후 로딩 숨김
      },
    });
  },
  postStreamRequest: function (url, params, onprogress, successFunc, failFunc) {
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
    });
  },
};
