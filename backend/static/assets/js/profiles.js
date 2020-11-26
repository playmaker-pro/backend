function get_verification_form(slug)
{
        $.ajax({
            url: "/users/me/verification/",
            type: "get",
            data: {slug: slug},
            success: function(json) {
              // console.log(response);
              // response is form in html format
                $("#verification-form-body").html(json.form);

                // if (response['errors'] != null ) {

                //     let field;
                //     let txt = "<div class='error-message banner alert alert-danger'>";
                //     for (field in response['errors']) {
                //         txt += '<div><strong>'+error['field']+'</strong>'
                //         let error;
                //         for (error of response['errors'][field]) {
                //             txt += '<div>' + error+'</div>'
                //         }
                //         txt += '</div>'
                //     }

                //     $("#needVerificationFormErrors").html = txt;
                // }

            }
        })
  }

  function copyToClipboard() {
    var copyText = document.getElementById("copyToClipBoard");
    copyText.select(); 
    copyText.setSelectionRange(0, 99999); /*For mobile devices*/
    document.execCommand("copy");
  }

  $(document).on('submit', '#verification-form', function(e){

    e.preventDefault(); // avoid to execute the actual submit of the form.

    var form = $(this);
    var url = form.attr('action');
    console.log('sssssss')
    $.ajax({
           type: "POST",
           url: url,
           data: form.serialize(), // serializes the form's elements.
           success: function(json)
           {
                if (json.success == true ) {
                    location.reload();
                } else { 
                        $("#verification-form-body").html(json.form);
                }
           }
         });

    
});