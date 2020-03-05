% rebase('base.tpl', title=f'shh! - Secret Link', post_scripts=['submit_result'])
<main>
  <div class="header">
    % if defined('user_id') and user_id:
    <span class="spacer"></span>
    <a href="/logout">Log out</a>
    % else:
    <span class="spacer"></span>
    <a href="/login">Log in</a>
    % end
  </div>
  <h1>shh!</h1>
  <p>This link will expire in <span class="nowrap">{{ttl}}.</span></p>
  <pre id="secretLink" class="wide">{{secret_url}}</pre>
  <button id="copyButton" class="mainButton" type="button" class="hidden"
          title="Copy link to clipboard">Copy Link</button>
  <p>It will only work once, so don't open it by mistake!</p>
  <p><a href="/">Got another secret?</a></p>
</main>
