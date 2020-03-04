const smallSecret = document.getElementById('smallSecret');
const largeSecret = document.getElementById('largeSecret');
const expandToggle = document.getElementById('expandToggle');

var secretExpanded = false;

function toggleExpand() {
  if (secretExpanded) {
    largeSecret.disabled = true;
    largeSecret.style.display = 'none';
    smallSecret.style.removeProperty('display');
    smallSecret.disabled = false;
    expandToggle.title = 'Expand to text block mode';
    expandToggle.innerHTML = 'Expand';
    secretExpanded = false;
  } else {
    smallSecret.disabled = true;
    smallSecret.style.display = 'none';
    largeSecret.style.removeProperty('display');
    largeSecret.disabled = false;
    expandToggle.title = 'Shrink to single line mode';
    expandToggle.innerHTML = 'Shrink';
    secretExpanded = true;
  }
}

expandToggle.addEventListener('click', toggleExpand);

expandToggle.style.removeProperty('display');
