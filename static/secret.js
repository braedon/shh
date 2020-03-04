const secret = document.getElementById('secret');
const showSecretToggle = document.getElementById('showSecretToggle');
const copyButton = document.getElementById('copyButton');

var secretVisible = false;

function toggleSecret() {
  if (secretVisible) {
    secret.style.display = 'none';
    showSecretToggle.title = 'Show Secret';
    showSecretToggle.innerHTML = 'Show Secret';
    secretVisible = false;
  } else {
    secret.style.removeProperty('display');
    showSecretToggle.title = 'Hide Secret';
    showSecretToggle.innerHTML = 'Hide Secret';
    secretVisible = true;
  }
}

function copyToClipboard() {
  if (!secretVisible) {
    secret.style.removeProperty('display');
  }
  if(document.body.createTextRange) {
    // Internet Explorer
    var range = document.body.createTextRange();
    range.moveToElementText(secret);
    range.select();
    document.execCommand('Copy');
  }
  else if(window.getSelection) {
    // Other browsers
    var selection = window.getSelection();
    var range = document.createRange();
    range.selectNodeContents(secret);
    selection.removeAllRanges();
    selection.addRange(range);
    document.execCommand('Copy');
  }
  if (!secretVisible) {
    secret.style.display = 'none';
  }
}

showSecretToggle.addEventListener('click', toggleSecret);
copyButton.addEventListener('click', copyToClipboard);

secret.style.display = 'none';
showSecretToggle.style.removeProperty('display');
copyButton.style.removeProperty('display');
