% rebase('base.tpl', title='shh! - Page Not Found')
<main>
  <span class="spacer"></span>
  <div class="content">
    <h1>shh!</h1>
    % if error.body and not error.body.startswith('Not found: '):
    <p>{{error.body}}</p>
    % else:
    <p>Oops, that page doesn't exist</p>
    % end
  </div>
  <span class="spacer"></span>
  <div class="linkRow">
    <a href="/">Got a secret?</a>
  </div>
</main>
