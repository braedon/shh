% rebase('base.tpl', title='shh! - Error')
<main>
  <span class="spacer"></span>
  <div class='content'>
    <h1>shh!</h1>
    <div class="section">
      <p>Oops, something went wrong.</p>
      % if error.body and error.status_code < 500:
      <p>{{error.body}}</p>
      % end
    </div>
    <a class="buttonLike" href="/">Got a secret?</a>
  </div>
  <span class="spacer"></span>
</main>
