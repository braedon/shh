<!DOCTYPE html>
<html lang="en">
  <head>
    <title>{{title}}</title>

    % if defined('description'):
    <meta name="Description" content="{{description}}">
    % end
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">

    <link rel="stylesheet" type="text/css" href="https://necolas.github.io/normalize.css/8.0.1/normalize.css">
    <link rel="stylesheet" type="text/css" href="/main.css">
  </head>
  <body>
% from shh.misc import indent
{{!indent(base, 4)}}

    % if defined('post_scripts'):
    % for script in post_scripts:
    <script src="/{{script}}.js"></script>
    % end
    % end
  </body>
</html>
