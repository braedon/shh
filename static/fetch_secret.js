const expireElem = document.getElementById('expireDateTime');
const dateTime = new Date(expireElem.innerHTML);
expireElem.innerHTML = dateTime.toLocaleTimeString();
