% rebase('base.tpl', title=f'shh! - View Secret', post_scripts=['secret'], do_indent=False)
<main>
  <span class="spacer"></span>
  <div class="content limitWidth">
    <h1>shh!</h1>
    <div class="section">
      % if defined('description') and description:
      <p>{{description}}</p>
      % end
      <pre id="secret">{{secret}}</pre>
      <button id="showSecretToggle" type="button" class="hidden"
              title="Show Secret">Show Secret</button>
      <button id="copyButton" type="button" class="hidden"
              title="Copy link to clipboard">Copy Secret</button>
      <p class="description">This link won't work again, so make sure to take note of the secret!</p>
    </div>
  </div>
  <span class="spacer"></span>
  <div class="linkRow">
    <a href="/">Got a secret?</a>
  </div>
</main>
