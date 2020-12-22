


function copy() {
  $(this);
  var copyText = document.getElementById("myInput");
  copyText.select();
  copyText.setSelectionRange(0, 99999);
  document.execCommand("copy");
  
  var tooltip = document.getElementById("myTooltip");
  tooltip.innerHTML = "Copied: " + copyText.value;
}

function outFunc() {
  var tooltip = document.getElementById("myTooltip");
  tooltip.innerHTML = "Copy to clipboard";
}



function get_add_announcement_form(){
        $.ajax({
            url: "/marketplace/add/",
            type: "get",
            /*data: {slug: slug},*/
            success: function(json) {
                $("#add-announcement-form-body").html(json.form);
                $('#add-announcement-form-body select').addClass("selectpicker").selectpicker('refresh'); 

            },
            error: function (xhr, ajaxOptions, thrownError) {
              $("#add-announcement-form-body select").addClass("selectpicker").selectpicker('refresh'); 
           }
        })
  }

  function get_filters_form(){
      $.ajax({
          url: "/marketplace/filters/",
          type: "get",
          /*data: {slug: slug},*/
          success: function(json) {
              $("#filters-form-body").html(json.form);
              $("#filters-form-body select").addClass("selectpicker").selectpicker('refresh'); 
          },
          error: function (xhr, ajaxOptions, thrownError) {
             $("#filters-form-body select").addClass("selectpicker").selectpicker('refresh'); 
          }
      })
    }



function get_missingname_form(slug)
{
        $.ajax({
            url: "/users/me/missingname/",
            type: "get",
            data: {slug: slug},
            success: function(json) {
                $("#missingname-form-body").html(json.form);
                $("#missingname-form-body select").addClass("selectpicker").selectpicker('refresh'); 
            }
        })
  }

function get_verification_form(slug)
{
    $.ajax({
        url: "/users/me/verification/",
        type: "get",
        data: {slug: slug},
        success: function(json) {
            $("#verification-form-body").html(json.form);
            $("#verification-form-body select").addClass("selectpicker").selectpicker('refresh'); 
        }
    })
  }

function copyToClipboard() {
    var copyText = document.getElementById("copyToClipBoard");
    copyText.select(); 
    copyText.setSelectionRange(0, 99999); /*For mobile devices*/
    document.execCommand("copy");
  }


function updateSettings(event) {
    $.ajax({
      url: "/users/me/updatesettings/",
      type: "get",
      success: function(json) {
        showToastMessage('Ustawienia zmienione');
          
      }
  })
}



$(document).on('submit', '#missingname-form', function(e){

    e.preventDefault(); // avoid to execute the actual submit of the form.

    var form = $(this);
    var url = form.attr('action');

    $.ajax({
           type: "POST",
           url: url,
           data: form.serialize(), // serializes the form's elements.
           success: function(json)
           {
                if (json.success == true ) {
                    location.reload();
                } else { 
                        $("#missingname-form-body").html(json.form);
                }
           }
         });

    
});
$(document).on('submit', '#verification-form', function(e){

    e.preventDefault(); // avoid to execute the actual submit of the form.

    var form = $(this);
    var url = form.attr('action');
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
$(document).on('submit', '#add-announcement-form', function(e){

  e.preventDefault(); // avoid to execute the actual submit of the form.

  var form = $(this);
  var url = form.attr('action');
  $.ajax({
         type: "POST",
         url: url,
         data: form.serialize(), // serializes the form's elements.
         success: function(json)
         {
              if (json.success == true ) {
                  location.reload();
              } else { 
                      $("#add-announcement-form-body").html(json.form);
              }
         }
       });

  
});