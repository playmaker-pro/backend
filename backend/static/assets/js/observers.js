function modalShow(openmodal) {

    if (openmodal != null){
        var modaID = '#' + openmodal
        console.log('open modal: ', modaID);
        $(modaID).modal('show');
    }
}

function modalHide(openmodal) {

    if (openmodal != null){
        var modaID = '#' + openmodal
        console.log('open modal: ', modaID);
        $(modaID).modal('hide');
    }
}


function observeTeam(event, slug) {
    var button = $(event.target) /* .parent('.btn-obs'); */
    $.ajax({
        type:'POST',
        url:'/users/me/observe/team/',
        data:{
            csrfmiddlewaretoken:$('input[name=csrfmiddlewaretoken]').val(),
            slug: slug,
            action: 'post',
        },
        success: function(json){
            button.toggleClass("observed")
            if (button.hasClass("observed")) {
                button.text('obserwujesz')
            } else {
                button.text('obserwuj')         

            }
            showToastMessage(json.message.body);

            //console.log('ssss', button);
            //modalShow(json.open_modal);
        },
        error : function(xhr, errmsg, err) {
        console.log(xhr.status + ": " + xhr.responseText); // provide a bit more info about the error to the console
    }
    });
};


function observe(event, slug) {
    var button = $(event.target); /*.parent('.btn-obs');*/
    $.ajax({
        type:'POST',
        url:'/users/me/observe/',
        data:{
            csrfmiddlewaretoken:$('input[name=csrfmiddlewaretoken]').val(),
            slug: slug,
            action: 'post',
        },
        success: function(json){
            button.toggleClass("observed")
            if (button.hasClass("observed")) {
                button.text('obserwujesz')
            } else {
                button.text('obserwuj')         

            }
   
            showToastMessage(json.message.body);

            //console.log('ssss', button);
            //modalShow(json.open_modal);
        },
        error : function(xhr, errmsg, err) {
        console.log(xhr.status + ": " + xhr.responseText); // provide a bit more info about the error to the console
    }
    });
};


function inquiryUpdate(event, idTick) {
    var button = $(event.target);
    $.ajax({
        type:'POST',
        url:'/users/me/query/update/',
        data:{
            csrfmiddlewaretoken:$('input[name=csrfmiddlewaretoken]').val(),
            tick: idTick,
            action: 'post'
        },
        success:function(json){ 
            $(".inquiryAnswerButtons").remove();  
            showToastMessage(json.message.body);
            window.setTimeout(location.reload(), 500);
            
        },
        error : function(xhr, errmsg, err) {
        console.log(xhr.status + ": " + xhr.responseText); // provide a bit more info about the error to the console
    }
    });
}

function approve_annoucement(event, slug, type) {

    $.ajax({
        type:'POST',
        url:'/marketplace/approve/',
        data:{
            csrfmiddlewaretoken:$('input[name=csrfmiddlewaretoken]').val(),
            id: slug,
            announcement_type: type,
            action: 'post',
        },
        success:function(json){         
            $('#requestButton').toggleClass("btn-requested")   
            modalHide('inquiryModal');
            if(json.error){
                showToastErrorMessage(json.message)
            } else {
                showToastMessage(json.message);
            }
            window.setTimeout(function(){location.reload()}, 700);
     
        },
        error : function(xhr, errmsg, err) {
        console.log(xhr.status + ": " + xhr.responseText); // provide a bit more info about the error to the console
    }
    });
}

function inquiry(event, slug, category) {
    $.ajax({
        type:'POST',
        url:'/users/me/query/',
        data:{
            csrfmiddlewaretoken:$('input[name=csrfmiddlewaretoken]').val(),
            slug: slug,
            category: category,
            action: 'post'
        },
        success:function(json){         
            $('#requestButton').toggleClass("btn-requested");
            modalHide('inquiryModal');
            showToastMessage(json.message.body);
            window.setTimeout(location.reload(), 500);
            
        },
        error : function(xhr, errmsg, err) {
        console.log(xhr.status + ": " + xhr.responseText); // provide a bit more info about the error to the console
    }
    });
};

/*
    On submiting the form, send the POST ajax
    request to server and after successfull submission
    display the object.
*/



$("#observe").submit(function (e) {
    // preventing from page reload and default actions
    e.preventDefault();
    // serialize the data for sending the form data.
    var serializedData = $(this).serialize();
    // make POST ajax call
    $.ajax({
        type: 'POST',
        url: "{% url 'post_friend' %}",
        data: serializedData,
        success: function (response) {
            // on successfull creating object
            // 1. clear the form.
            $("#friend-form").trigger('reset');
            // 2. focus to nickname input 
            $("#id_nick_name").focus();

            // display the newly friend to table.
            var instance = JSON.parse(response["instance"]);
            var fields = instance[0]["fields"];
            $("#my_friends tbody").prepend(
                `<tr>
                <td>${fields["nick_name"]||""}</td>
                <td>${fields["first_name"]||""}</td>
                <td>${fields["last_name"]||""}</td>
                <td>${fields["likes"]||""}</td>
                <td>${fields["dob"]||""}</td>
                <td>${fields["lives_in"]||""}</td>
                </tr>`
            )
        },
        error: function (response) {
            // alert the error if any error occured
            alert(response["responseJSON"]["error"]);
        }
    })
})


function newItem(slug) {
    var first = document.getElementById("first");
    var xhttp = new XMLHttpRequest();
    xhttp.responseType = 'json';
    //console.log('first=', first);
    var params = 'first_id='+first.value;

    xhttp.onreadystatechange = function() {
        if (this.readyState == 4 && this.status == 200) {
            var newEl = document.createElement('div');

            if (this.response.object === "") {
                console.log('obj= niby pusty', this.response.object);
            } else {

            newEl.innerHTML = this.response.object;

            var list = document.getElementById("accordion");
            first.value = this.response.first;

            var newfirst = document.getElementById("first");
            //
            list.insertBefore(newEl, list.childNodes[1]);
              playAudio();

            }


        }
    };
    xhttp.open("POST", "/orders/" + slug + "/", true);
    xhttp.setRequestHeader('Content-type', 'application/x-www-form-urlencoded');
    xhttp.send(params);
}

