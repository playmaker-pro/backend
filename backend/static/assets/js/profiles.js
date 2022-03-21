


function copy() {
  $(this);
  var copyText = document.getElementById("myInput");
  copyText.select();
  copyText.setSelectionRange(0, 99999);
  document.execCommand("copy");
  
  var tooltip = document.getElementById("myTooltip");
  tooltip.innerHTML = "Copied: " + copyText.value;
}

$(document).ready(function() {

 
  if ($('#id_agent_status').val() == '1') {
    
    $('#div_id_agent_name').show();
    $('#div_id_agent_phone').show();
  } else {
    $('#div_id_agent_name').hide();
    $('#div_id_agent_phone').hide();
  }


  $('#id_agent_status').change(function() {
    //console.log('ssssssssssss', $('#id_agent_status').val())
    if ($(this).val() == '1') {
      $('#div_id_agent_name').show();
      $('#div_id_agent_phone').show();
    } else {
      $('#div_id_agent_name').hide();
      $('#div_id_agent_phone').hide();
    }
    /* $.each($.viewMap, function() { this.hide(); }); */
    // show current
    /* $.viewMap[$(this).val()].show();  */
  });
});

function outFunc() {
  var tooltip = document.getElementById("myTooltip");
  tooltip.innerHTML = "Copy to clipboard";
}



function get_add_announcement_form(event, id = null, announcement_type = null, action_name = null){
  $("#add-announcement-form-body").empty();
  $('#add-ann-out').hide();
  $('#add-ann-left').hide();
  $.ajax({
      url: "/marketplace/add/",
      type: "get",
//      data: {'id': id, 'announcement_type': announcement_type},
      data: {'id': id, 'announcement_type': announcement_type, 'action_name': action_name},
      /*data: {slug: slug},*/
      success: function(json) {
        if (json.form === null) {
          $('#add-ann-out').show();
          $('#add-ann-left').hide();
          $("#add-announcement-form-body").empty();
        } else if(Object.keys(json).length > 0) {
          $('#add-ann-out').hide();
          $('#add-ann-left').show();
          $("#add-announcement-form-body").html(json.form);
          try{
            $('#addAnnouncementModalLabel').html(json.modal.title);
            $('#add-announcement-submit').html(json.modal.button.name);
            $('#add-announcement-form-body select').addClass("selectpicker").selectpicker('refresh'); 
          } catch(e){}
        }
      
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
        
            if($('#id_has_team_1').is(':checked')) { 
              console.log('=', $("#select_team_div"))
              $("#select_team_div").fadeIn()
              $("#text_team_div").hide()
          }
          
        
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

function checkIfTeamNotFound() {
  if($('#id_team_not_found').is(':checked')) {

    $("#text_team_div").fadeIn()
    $("#div_id_team").hide()
    $("#hint_id_team_club_league_voivodeship_ver").text("Wprowadź ręcznie nazwę klubu, poziom rozgrywkowy, region i kraj jeśli jest inny niż Polska")
    $('label[for="id_team_not_found"]').text('odznacz jeśli chesz wybrać klub z listy')
    
  } else {
    $("#text_team_div").hide()
    $("#div_id_team").fadeIn()
    $('label[for="id_team_not_found"]').text('zaznacz jeśli nie znalazłeś swojego klubu na liście')
  }
}

function setHasClubDefaults() {
  console.log('xxx')
  $("#select_team_div").fadeIn()
  $("#text_team_div").hide()
  checkIfTeamNotFound()


}

function setHasntClubDefaults() {
  $("#select_team_div").hide()
  $("#hint_id_team_club_league_voivodeship_ver").text("Jeśli wcześniej grałeś w rozgrywkach PZPN - wprowadź nazwę ostatniego klubu, poziom rozgrywkowy, region oraz sezon. My poszukamy Twoich statystyk historycznych.")
  $("#text_team_div").fadeIn()
}


function setVerificationDefaults() {
    if($('#id_has_team_1').is(':checked')) { 
      setHasClubDefaults()

    } else if ($('#id_has_team_2').is(':checked')) { 
      setHasntClubDefaults()
    }
}

$(document).on("click", "#div_id_team_not_found", function(){ 

  checkIfTeamNotFound()


});

$(document).on("click", "#id_has_team_1", function(){
  
    if($('#id_has_team_1').is(':checked')) { 
        setHasClubDefaults()
      } 
 });

$(document).on("click", "#id_has_team_2", function(){
    if($('#id_has_team_2').is(':checked')) { 
      setHasntClubDefaults()
      }
});

$(document).on('submit', '#verification-form', function(e){

    e.preventDefault(); // avoid to execute the actual submit of the form.

    var form = $(this);
    var url = form.attr('action');
    $.ajax({
           type: "POST",
           url: url,
           data: form.serialize(),
           success: function(json)
           {
                if (json.success == true ) {
                    location.reload();
                } else { 
                    $("#verification-form-body").html(json.form);
                    $('select').selectpicker();
                    setVerificationDefaults()
                }
           }
         });

    
});

$(document).on('submit', '#add-announcement-form', function(e){

  e.preventDefault(); // avoid to execute the actual submit of the form.

  var form = $(this);
  var url = form.attr('action');
  var data = form.serialize() + '&id=' + $('#add-ann-number').val() + '&announcement_type=' + $('#add-ann-type').val() + '&action_name=' + $('#add-ann-action-name').val();

  $.ajax({
         type: "POST",
         url: url,
         data:  data, // serializes the form's elements.
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