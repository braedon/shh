% rebase('base.tpl', title=f'shh! - Secret Link', post_scripts=['submit_result'])
<main>
  <div class="header">
    % if defined('user_id') and user_id:
    <a class="buttonLike" href="/secrets">Secrets</a>
    <span class="spacer"></span>
    <a class="buttonLike" href="/logout">Log out</a>
    % else:
    <span class="spacer"></span>
    <a class="buttonLike" href="/login">Log in</a>
    % end
  </div>
  <span class="spacer"></span>
  <div class="content">
    <h1>shh!</h1>
    <div class="section">
      <p>This link will expire in <span class="nowrap">{{ttl}}</span></p>
      <pre id="secretLink">{{service_address}}/secrets/{{secret_id}}</pre>
      <button id="copyButton" type="button" class="hidden"
              title="Copy link to clipboard">Copy Link</button>
      <p>It will only work once, so don't open it by mistake!</p>
    </div>
    <a class="buttonLike" href="/">Got another secret?</a>
  </div>
  <span class="spacer"></span>
</main>
