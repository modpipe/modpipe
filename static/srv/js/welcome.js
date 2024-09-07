
// Show Login Modal
const welcomeModal = new Modal(document.getElementById('welcome-popup'), {
    placement: 'center'
});

// Hide Login Modal
document.getElementById('close-welcome').addEventListener('click', function() {
    welcomeModal.hide();
});

welcomeModal.show()