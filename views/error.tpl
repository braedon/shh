% rebase('base.tpl', title='shh! - Error')
<main>
  <span class="spacer"></span>
  <div class='content'>
    <h1>shh!</h1>
    <p>Oops, something went wrong.</p>
    % if error.body:
    <p>{{error.body}}</p>
    % end
    <a class="buttonLike" href="/">Got a secret?</a>
  </div>
  <span class="spacer"></span>
</main>
