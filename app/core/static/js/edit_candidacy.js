jQuery(function ($){
  "use strict";

  $('select').on('change', function(e) {
    e.preventDefault()

    if($(this).attr('id') == null) {
		var form = $(e.target).closest('form')
    }
    else {
    	var form = $("#" + $(this).attr('id'));
    }

	form.submit()
  })
});
