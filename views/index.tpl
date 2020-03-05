<%
rebase('base.tpl', title='shh!',
       description='Share passwords (or other secrets) via expiring one-time links.',
       post_scripts=['index'])
%>
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
  <p>Share passwords <span class="nowrap">(or other secrets)</span> via expiring <span class="nowrap">one-time links.</span></p>
  <form action="/secrets" method="POST">
    <input id="smallSecret" type="password" name="secret" autocomplete="off"
           placeholder="Secret" maxlength=100 required autofocus/>
    <textarea id="largeSecret" name="secret" class="hidden"
              autocomplete="off" spellcheck="false" wrap="off"
              placeholder="Secret" maxlength=2000 required disabled/></textarea>
    <div class="inputWrapper">
      <button id="expandToggle" type="button" class="hidden"
              title="Expand to text block mode">Expand</button>
      <select name="ttl" title="How long before the link expires" required>
        <option value="5m">5 minutes</option>
        <option value="15m">15 minutes</option>
        <option value="30m">30 minutes</option>
        <option value="1h">1 hour</option>
      </select>
    </div>
    % if defined('csrf') and csrf:
    <input name="csrf" type="hidden" value="{{csrf}}" />
    % end
    <button id="submitButton" class="mainButton">Generate Link</button>
  </form>
</main>
