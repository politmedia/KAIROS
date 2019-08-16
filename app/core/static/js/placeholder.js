$.fn.insertAtCaret = function (text) {
    return this.each(function () {
        if (document.selection && this.tagName == 'TEXTAREA') {
            //IE textarea support
            this.focus();
            sel = document.selection.createRange();
            sel.text = text;
            this.focus();
        } else if (this.selectionStart || this.selectionStart == '0') {
            //MOZILLA/NETSCAPE support
            startPos = this.selectionStart;
            endPos = this.selectionEnd;
            scrollTop = this.scrollTop;
            this.value = this.value.substring(0, startPos) + text + this.value.substring(endPos, this.value.length);
            this.focus();
            this.selectionStart = startPos + text.length;
            this.selectionEnd = startPos + text.length;
            this.scrollTop = scrollTop;
        } else {
            // IE input[type=text] and other browsers
            this.value += text;
            this.focus();
            this.value = this.value; // forces cursor to end
        }
    });
};

$(document).ready(function(){
	$(".insert_placeholder_subject, .insert_placeholder_message").click(function(event){
        var filler = $(this).attr("class").replace("insert_placeholder_","")
		event.preventDefault();
		$(this).closest('div.form-group').find('[name*="' + filler + '"]').insertAtCaret($(this).attr('title') + ' ');
	});

    $('#languageTabs a').click(function (e) {
      e.preventDefault()
      $(this).tab('show')
    })
});