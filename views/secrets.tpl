% rebase('base.tpl', title=f'shh! - Active Secrets', post_scripts=['secrets'])
<main>
  <div class="header">
    <span class="spacer"></span>
    <a class="buttonLike" href="/logout">Log out</a>
  </div>
  <span class="spacer"></span>
  <div class="content limitWidth">
    <h1>shh!</h1>
    <div class="section">
      % if secrets:
      <h2>Active Secrets</h2>
      %   for secret in secrets:
      <div class="subSection">
        <pre id="secretLink">{{service_address}}/secrets/{{secret.secret_id}}</pre>
        % from rfc3339 import datetimetostr
        <p class="description">
          % if secret.description:
          {{secret.description}}<br>
          % end
          Expires at <span class="expireDateTime">{{datetimetostr(secret.expire_dt)}}</span>
        </p>
      </div>
      %   end
      % else:
      <p>No active secrets</p>
      % end
    </div>
  </div>
  <span class="spacer"></span>
  <div class="linkRow">
    <a href="/">Got another secret?</a>
  </div>
</main>
