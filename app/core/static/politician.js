jQuery(function ($){
  "use strict";

  $('.slider').each(function() {
    var value = $(this).data('value')
    $(this).slider({
      max: 10,
      min: 0,
      value: value,
      step: 2
    })
  })

  if ($('select[name="party"]').val() != 'party_other') {
    $('input[name="party_other"]').val('').hide()
  }

  $('select[name="party"]').on('change', function(){
    if ($(this).val() == 'party_other') {
      $('input[name="party_other"]').show()
    }
    else {
      $('input[name="party_other"]').val('').hide()
    }
  })

  $('.slider').on('slidechange', saveAnswer)
  $('.note').on('focusout', saveAnswer)

  function saveAnswer(e) {
    var form = $(e.target).closest('form')
    var slider = form.children('.slider')
    var value = slider.slider('value')
    form.find('input[name="agreement_level"]').val(value)

    $.post(Urls.politician_answer(), form.serialize())
  }

  $('#unpublish').click(function(e) {
    e.preventDefault()
    $.post(Urls.unpublish(), $(e.target).closest('form').serialize(), location.reload())
  })

  $('#links').on('click', '#link input[type="submit"]', function(e) {
    e.preventDefault()
    $.post(
        Urls.add_link(),
        $(e.target).closest('form').serialize(),
        function(data){
            $('#links').html(data)
        }
    )
  })

  $('#links').on('click', '.glyphicon-trash', function(e) {
    e.preventDefault()
    $.post(
        Urls.delete_link(),
        $(e.target).closest('form').serialize(),
        function(data){
            $('#links').html(data)
        }
    )
  })

  $('#publish').click(function(e) {
    // save all questions responded with zero
    // this happens if someone doesnt use the slider
    e.preventDefault()

    $('.slider').each(function(){
      var form = $(this).closest('form')
      var slider = form.children('.slider')
      var value = slider.slider('value')
      var input = form.find('input[name="agreement_level"]')

      if (input.val() === '') {
        input.val(value)
        $.post(Urls.politician_answer(), form.serialize())
      }
    })

    $.post(Urls.publish(), $(e.target).closest('form').serialize(), location.reload())
  })
});