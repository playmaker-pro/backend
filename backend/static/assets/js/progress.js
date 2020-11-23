


$(function() {

    $(".progress-circle").each(function() {
  
      var value = $(this).attr('data-value');
      var shift = $(this).attr('data-shift');
      var left = $(this).find('.progress-left .progress-bar');
      var right = $(this).find('.progress-right .progress-bar');
  
      var whole = $(this).find('.progress-circle');
      var signature  = $(this).find('.progress-circle-text');
    
      if (shift > 0){ 
          signature.css('transform', 'rotate(' + percentageToDegrees(-shift) + 'deg)')
          $(this).css('transform', 'rotate(' + percentageToDegrees(shift) + 'deg)')
  
  
  
      };
      if (value > 0) {
        if (value <= 50) {
          
          right.css('transform', 'rotate(' + percentageToDegrees(value) + 'deg)')
  
        } else {
          right.css('transform', 'rotate(180deg)')
          left.css('transform', 'rotate(' + percentageToDegrees(value - 50) + 'deg)')
        }
      }
  
    })
  
    function percentageToDegrees(percentage) {
  
      return percentage / 100 * 360
  
    }
  
  });