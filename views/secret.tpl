% rebase('base.tpl', title=f'shh! - View Secret', post_scripts=['secret'])
<main>
  <h1>shh!</h1>
  <pre id="secret" class="wide">{{secret}}</pre>
  <button id="showSecretToggle" type="button" title="Show secret"
          style="display: none">Show Secret</button>
  <button id="copyButton" class="mainButton" type="button" title="Copy link to clipboard"
          style="display: none">Copy Secret</button>
  <p>This link won't work again, so make sure to take note of the secret!</p>
  <p><a href="/">Got a secret?</a></p>
</main>
