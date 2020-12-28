

$("#filter-button").click(function(){
    $("input").each(function(){
        if($(this).val() == '') {
            $(this).remove();
        }
    });
    $("select").each(function(){
        if($(this).val() == '') {
            $(this).remove();
        }
    });
    $("#filter-button").submit();
});


$("#filter-button-mobile").click(function(){
    $("input").each(function(){
        if($(this).val() == '') {
            $(this).remove();
        }
    });
    $("select").each(function(){
        if($(this).val() == '') {
            $(this).remove();
        }
    });
    $("#filter-button-mobile").submit();
});