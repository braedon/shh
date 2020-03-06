const expireElems = document.getElementsByClassName('expireDateTime');

for (var i = 0; i < expireElems.length; i++) {
    const dateTime = new Date(expireElems[i].innerHTML);
    expireElems[i].innerHTML = dateTime.toLocaleTimeString();
}
