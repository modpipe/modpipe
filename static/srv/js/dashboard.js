function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

function makeId(length) {
    let result = '';
    const characters = 'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789';
    const charactersLength = characters.length;
    let counter = 0;
    while (counter < length) {
      result += characters.charAt(Math.floor(Math.random() * charactersLength));
      counter += 1;
    }
    return result;
}


// Define Main Content Section
const dashboardWrapper = document.getElementById('dashboard_wrapper');

// Show Command Modal
const newCommandModal = new Modal(document.getElementById('new_command-popup'), {
    placement: 'center'
});

// Hide Command Modal
document.getElementById('close-new_command').addEventListener('click', function() {
    document.getElementsByTagName('body').classList.add('overflow-hidden')
    newCommandModal.hide();

});

// Show Config Modal
const configModal = new Modal(document.getElementById('config-popup'), {
    placement: 'center'
});

// Hide Config Modal
document.getElementById('close-config').addEventListener('click', function() {
    configModal.hide();
});

function showCommandModal(){
    newCommandModal.show();
}

function initConfigModal(){
    // Shows Config Modal if querystring has ?'config=1' in it.
    const queryParams = new URLSearchParams(window.location.search);
    if (queryParams.has('config')){
        configModal.show()
    }
}


function toggleEditCommands() {
    var edit_button = document.getElementById('edit_commands');
    var elements = document.querySelectorAll('[id$="-edit"]')
    if (edit_button.innerHTML === "Edit") {
        edit_button.innerHTML = "Cancel Edit"
        for (let i = 0; i < elements.length; i++) {
            elements[i].classList.remove("invisible")
        }
    } else {
        edit_button.innerHTML = "Edit"
        for (let i = 0; i < elements.length; i++) {
            elements[i].classList.add("invisible")
        }
    }
}

function changeCommandLabel(select){
    let command_label = document.getElementById('command_label');
    let commnad = document.getElementById('command')
    if (select.value === "chat_message"){
        command_label.innerHTML = "Chat Message";
        command.placeholder = "Enter Chat Message";
    } else {
        command_label.innerHTML = "Command Parameters";
        command.placeholder = "Enter Command Parameters"
    }
}

function commandFeedback(id,result) {
    if (result.timeout === "None" || result.timeout === "0" ){
        commandTimeout = 10000;
    } else {
        commandTimeout = parseInt(result.timeout) * 1000;
    }
    commandStatusCode = result.status.code;
    commandMessage = result.feedback;
    if (commandStatusCode === 200){
        feedbackBg = "bg-emerald-400/25";
        feedbackTextBg = "bg-green-950"
        feedbackColor = "text-white";
    } else {
        feedbackBg = "bg-red-400";
        feedbackColor = "text-red-950/25";
    }

    feedbackEl = document.getElementById(id);
    feedbackTextEl = document.getElementById(id+'-text');
    console.log(commandStatusCode);
    console.log(commandTimeout);
    console.log(feedbackBg);
    console.log(feedbackColor);
    console.log(commandMessage);

    feedbackEl.classList.add(feedbackBg);
    feedbackEl.classList.add(feedbackColor);
    feedbackTextEl.classList.add(feedbackTextBg);
    feedbackTextEl.innerHTML = commandMessage;
    feedbackEl.classList.remove("invisible");
    sleep(commandTimeout).then(() => {
        feedbackEl.classList.add("invisible");
        feedbackEl.classList.remove(feedbackBg);
        feedbackEl.classList.remove(feedbackColor);
        feedbackTextEl.classList.remove(feedbackTextBg);
        feedbackTextEl.innerHTML = "";
    })
    
}

function launchCommand(cmd){
    endpoint = "command/"+cmd+"?chk="+makeId(10)
    fetch(endpoint)
    .then(response => {
        if (!response.ok) {
        throw new Error('Network response was not ok');
        }
        // Handle response data (e.g., convert to JSON)
        return response.json();
    })
    .then(data => {
        // Do something with the data
        // Make the command block glow green and fade back to normal after timeout is over
        console.log(data);
        commandFeedback(cmd+'-feedback',data.result)

    })
    .catch(error => {
        
    });
}

function confirmDelete() {
    console.log('confirm delete')
}


initConfigModal()