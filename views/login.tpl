% rebase('base.tpl', title='shh! - Log In')
<main>
  <span class="spacer"></span>
  <div class="content">
    <h1>shh!</h1>
    <%
    from urllib.parse import urlencode
    qs_dict = {
        'response_type': 'code',
        'client_id': oidc_client_id,
        'redirect_uri': oidc_redirect_uri,
        'scope': 'openid',
        'state': state,
        'nonce': nonce,
    }
    qs = urlencode(qs_dict)
    %>
    <p>Logging in enables you to track which secret links you create are still active</p>
    <a class="buttonLike mainButton" href="{{oidc_auth_endpoint}}?{{qs}}">Log in with {{oidc_name}}</a>
  </div>
  <span class="spacer"></span>
</main>
