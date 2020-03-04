const secretLink = document.getElementById('secretLink');
const copyButton = document.getElementById('copyButton');

function copyToClipboard() {
  if(document.body.createTextRange) {
    // Internet Explorer
    var range = document.body.createTextRange();
    range.moveToElementText(secretLink);
    range.select();
    document.execCommand('Copy');
  }
  else if(window.getSelection) {
    // Other browsers
    var selection = window.getSelection();
    var range = document.createRange();
    range.selectNodeContents(secretLink);
    selection.removeAllRanges();
    selection.addRange(range);
    document.execCommand('Copy');
  }
}

copyButton.addEventListener('click', copyToClipboard);

copyButton.style.removeProperty('display');
