const smallSecret = document.getElementById('smallSecret');
const largeSecret = document.getElementById('largeSecret');
const expandToggle = document.getElementById('expandToggle');

var secretExpanded = false;

function toggleExpand() {
  if (secretExpanded) {
    largeSecret.disabled = true;
    largeSecret.className = 'hidden';
    smallSecret.className = '';
    smallSecret.disabled = false;
    expandToggle.title = 'Expand to text block mode';
    expandToggle.innerHTML = 'Expand';
    secretExpanded = false;
  } else {
    smallSecret.disabled = true;
    smallSecret.className = 'hidden';
    largeSecret.className = '';
    largeSecret.disabled = false;
    expandToggle.title = 'Shrink to single line mode';
    expandToggle.innerHTML = 'Shrink';
    secretExpanded = true;
  }
}

expandToggle.addEventListener('click', toggleExpand);

expandToggle.className = '';
