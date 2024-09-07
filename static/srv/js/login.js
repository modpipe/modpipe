// Show Login Modal
const modalEl = document.getElementById('login-popup');
const loginModal = new Modal(modalEl, {
    placement: 'center'
});
// Hide Login Modal
const closeModalEl = document.getElementById('close-login');
closeModalEl.addEventListener('click', function() {
    loginModal.hide();
});