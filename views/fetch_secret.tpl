% rebase('base.tpl', title=f'shh! - View Secret', post_scripts=['fetch_secret'])
<main>
  <span class="spacer"></span>
  <div class="content limitWidth">
    <h1>shh!</h1>
    <form class="section" action="/secrets/{{secret_id}}" method="POST">
      % if defined('description') and description:
      <p>{{description}}</p>
      % end
      <p>
        % from rfc3339 import datetimetostr
        This secret expires at
        <span id="expireDateTime" class="nowrap">{{datetimetostr(expire_dt)}}</span>
      </p>
      <button class="mainButton">Fetch Secret</button>
      <p class="description">You can only fetch a secret once, so make sure you want it now!</p>
    </form>
  </div>
  <span class="spacer"></span>
  <div class="linkRow">
    <a href="/">Got a secret?</a>
  </div>
</main>
