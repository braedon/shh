% rebase('base.tpl', title='shh! - Log In')
<main>
  <span class="spacer"></span>
  <div class="content limitWidth">
    <h1>shh!</h1>
    <p>Logging in enables you to track which secret links you create are still active</p>
    <div class="section">
      <a class="mainButton" href="{{oidc_login_uri}}">
        Log In with {{oidc_name}}
      </a>
      <div class="linkRow">
        <a href="{{oidc_about_url}}" target="_blank" rel="noopener noreferrer">
          What's {{oidc_name}}?
        </a>
      </div>
    </div>
  </div>
  <span class="spacer"></span>
</main>
