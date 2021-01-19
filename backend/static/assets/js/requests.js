function seenRequests(event, ids = null){
    
    $.ajax({
        url: "/users/me/query/see/",
        type: "POST",
       
        data: {'ids': ids,  csrfmiddlewaretoken:$('input[name=csrfmiddlewaretoken]').val(), action: 'post'},
        /*data: {slug: slug},*/
        success: function(json) {
            if (json.status == true ){
                $(event.target).find('span').remove()
            }
        
        },
        error: function (xhr, ajaxOptions, thrownError) {
          
        }
    })
    }