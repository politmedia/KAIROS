jQuery(function ($){
  "use strict";

  $('select.answer').on('change', function(e) {
    e.preventDefault()
     var form = $(e.target).closest('form')
     form.submit()
  })
});
