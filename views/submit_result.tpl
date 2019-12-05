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
      <p>This link will expire in <span class="nowrap">{{ttl}}.</span></p>
      <pre id="secretLink" class="wide">{{secret_url}}</pre>
      <button id="copyButton" class="mainButton" type="button" title="Copy link to clipboard"
              onclick="copyToClipboard()" style="display: none">Copy Link</button>
      <p>It will only work once, so don't open it by mistake!</p>
      <p><a href="/">Got another secret?</a></p>
    </main>
  </body>
  <script type="text/javascript">
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

    copyButton.style.removeProperty('display');
  </script>
</html>
