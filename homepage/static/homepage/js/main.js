// Выводит текущий год в подвале сайта, чтобы не менять его вручную.
const yearElement = document.getElementById("current-year");

if (yearElement) {
    yearElement.textContent = new Date().getFullYear();
}
