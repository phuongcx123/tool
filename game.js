
//加载服务器信息
function GetServerList(url,serverElement){
    $.ajax({
        type: 'get',
        url: url,
        data: {},
        async: true,
        processData: false,
        contentType: false,
        dataType: 'json',
        success: function(data) {
            $(serverElement).html('');
            if (data.data.length <= 0) {
                $(serverElement).append('<option value="">暂无服务器信息</option>');
                return false;
            }
    
            $.each(data.data, function(k, v) {
                let option = $('<option></option>');
                option.val(v['server']);
                option.text(v['name']);
                $(serverElement).append(option);
            });
        },
        error: function(jqXHR, textStatus, errorThrown) {
            $('#model-1').find('.modal-body').text(textStatus + ':' + errorThrown);
            $('#model-1').modal('show');
        },
        complete: function() {
    
        }
    });
}

// 获取角色
function GetRoleList(url,GetBtn,serverElement,accountElement,roleElement){
    let lock = false;
    $(GetBtn).click(function() {

        if($(accountElement).val().length == 0 || $(serverElement).val().length == 0){
            return false;
        }

        if (lock) return false;
        lock = true;
        BtnLoad($(GetBtn)[0], "获取中...");
        let formData = new FormData();
        formData.append('serverID', $(serverElement).val());
        formData.append('account', $(accountElement).val());
        $.ajax({
            type: 'post',
            url: url,
            data: formData,
            async: true,
            processData: false,
            contentType: false,
            dataType: 'json',
            success: function(data) {
                $(roleElement).html('');
                if (data.data.length <= 0) {
                    $(roleElement).append('<option value="">未找到你的角色</option>');
                    return false;
                }
                $(roleElement).append('<option value="">获取角色成功！请选择角色</option>');
                $.each(data.data, function(k, v) {
                    let option = $('<option></option>');
                    option.val(v['roleID']);
                    option.text(v['name'] + ' / ' + v['level'] + '级');
                    $(roleElement).append(option);
                });
            },
            error: function(jqXHR, textStatus, errorThrown) {
                $('#model-1').find('.modal-body').text(textStatus + ':' + errorThrown);
                $('#model-1').modal('show');
            },
            complete: function() {
                BtnUnLoad($(GetBtn), "获取");
                lock = false;
            }
        });
    });

    //账号框的回车事件
    $(accountElement).keydown(function(e) {
        if (e.keyCode == 13) {
            e.preventDefault();
            $(GetBtn).trigger('click');
        }
    });
}

// 获取数值
function GetNumber(url,GetBtn,serverElement,accountElement,roleElement,numberElement,typeElement){
    let lock = false;
    $(GetBtn).click(function() {

        if($(accountElement).val().length == 0 || $(serverElement).val().length == 0 || $(roleElement).val().length == 0 || $(typeElement).val().length == 0){
            return false;
        }

        if (lock) return false;
        lock = true;
        BtnLoad($(GetBtn)[0], "获取中...");
        let formData = new FormData();
        formData.append('type', $(typeElement).val());
        formData.append('serverID', $(serverElement).val());
        formData.append('account', $(accountElement).val());
        formData.append('role', $(roleElement).val());

        $.ajax({
            type: 'post',
            url: url,
            data: formData,
            async: true,
            processData: false,
            contentType: false,
            dataType: 'json',
            success: function(data) {
                $(numberElement).val(data.data);
            },
            error: function(jqXHR, textStatus, errorThrown) {
                $('#model-1').find('.modal-body').text(textStatus + ':' + errorThrown);
                $('#model-1').modal('show');
            },
            complete: function() {
                BtnUnLoad($(GetBtn), "获取");
                lock = false;
            }
        });
    });
}