<%
rebase('base.tpl', title='shh!',
       description='Share passwords (or other secrets) via expiring one-time links.',
       post_scripts=['index'])
%>
<main>
  <h1>shh!</h1>
  <p>Share passwords <span class="nowrap">(or other secrets)</span> via expiring <span class="nowrap">one-time links.</span></p>
  <form action="/secrets" method="POST">
    <input id="smallSecret" type="password" name="secret" autocomplete="off"
           placeholder="Secret" maxlength=100 required autofocus/>
    <textarea id="largeSecret" name="secret"
              autocomplete="off" spellcheck="false" wrap="off"
              placeholder="Secret" maxlength=2000 required  style="display: none" disabled/></textarea>
    <div class="inputWrapper">
      <button id="expandToggle" type="button" title="Expand to text block mode"
              style="display: none">Expand</button>
      <select name="ttl" title="How long before the link expires" required>
        <option value="5m">5 minutes</option>
        <option value="15m">15 minutes</option>
        <option value="30m">30 minutes</option>
        <option value="1h">1 hour</option>
      </select>
    </div>
    <button id="submitButton" class="mainButton">Generate Link</button>
  </form>
</main>
