<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet" type="text/css" href="https://necolas.github.io/normalize.css/8.0.1/normalize.css">
    <link rel="stylesheet" type="text/css" href="/main.css">
    <title>shh!</title>
  </head>
  <body>
    <main>
      <h1>shh!</h1>
      <pre id="secret" class="wide">{{secret}}</pre>
      <button id="showSecretToggle" type="button" title="Show secret"
              onclick="toggleSecret()" style="display: none">Show Secret</button>
      <button id="hideButton" type="button" title="Hide secret"
              onclick="toggleSecret()" style="display: none">Hide Secret</button>
      <button id="copyButton" class="mainButton" type="button" title="Copy link to clipboard"
              onclick="copyToClipboard()" style="display: none">Copy Secret</button>
      <p>This link won't work again, so make sure to take note of the secret!</p>
      <p><a href="/">Got a secret?</a></p>
    </main>
  </body>
  <script type="text/javascript">
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

    secret.style.display = 'none';
    showSecretToggle.style.removeProperty('display');
    copyButton.style.removeProperty('display');
  </script>
</html>
