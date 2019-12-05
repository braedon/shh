<!DOCTYPE html>
<html>
  <head>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <link rel="stylesheet" type="text/css" href="https://necolas.github.io/normalize.css/8.0.1/normalize.css">
    <link rel="stylesheet" type="text/css" href="/main.css">
    <title>shh!</title>
  </head>
  <body>
    <main>
      <h1>shh!</h1>
      <p>Oops, something went wrong.</p>
      %if error.body:
        <p>{{error.body}}</p>
      %end
      <p><a href="/">Got a secret?</a></p>
    </main>
  </body>
</html>
