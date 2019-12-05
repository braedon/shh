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
      <button id="showButton" type="button" title="Show secret"
              onclick="showSecret()" style="display: none">Show Secret</button>
      <button id="hideButton" type="button" title="Hide secret"
              onclick="hideSecret()" style="display: none">Hide Secret</button>
      <button id="copyButton" class="mainButton" type="button" title="Copy link to clipboard"
              onclick="copyToClipboard()" style="display: none">Copy Secret</button>
      <p>This link won't work again, so make sure to take note of the secret!</p>
      <p><a href="/">Got a secret?</a></p>
    </main>
  </body>
  <script type="text/javascript">
    const secret = document.getElementById('secret');
    const showButton = document.getElementById('showButton');
    const hideButton = document.getElementById('hideButton');
    const copyButton = document.getElementById('copyButton');

    function showSecret() {
      showButton.style.display = 'none';
      secret.style.removeProperty('display');
      hideButton.style.removeProperty('display');
    }

    function hideSecret() {
      hideButton.style.display = 'none';
      secret.style.display = 'none';
      showButton.style.removeProperty('display');
    }

    function copyToClipboard() {
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
    }

    secret.style.display = 'none';
    showButton.style.removeProperty('display');
    copyButton.style.removeProperty('display');
  </script>
</html>
