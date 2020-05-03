% rebase('base.tpl', title='shh! - Error')
<main>
  <span class="spacer"></span>
  <div class="content">
    <h1>shh!</h1>
    <div class="section">
      % if error.body and error.status_code < 500:
      <p>{{error.body}}</p>
      % else:
      <p>Oops, something went wrong</p>
      % end
    </div>
  </div>
  <span class="spacer"></span>
  <div class="linkRow">
    <a href="/">Got a secret?</a>
  </div>
</main>
