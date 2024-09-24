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

function changeCommandType(select){
    var command_label = document.getElementById('command_label');
    var command = document.getElementById('command')
    var command_wrapper = document.getElementById('command_wrapper')
    
    // Make command_wrapper visible if not none

    if (select.value === "none"){
        command_wrapper.classList.add('invisible')
    } else if (select.value === "chat_message"){
        command_wrapper.classList.remove('invisible')
        command_label.innerHTML = "Chat Message";
        command.placeholder = "Enter Chat Message";
        command.rows = 4;
    } else if ( select.value === "nightbot_command"){
        command_wrapper.classList.remove('invisible');
        command_label.innerHTML = "Nightbot Command";
        command.placeholder = "Enter Nightbot Command Name";
        command.rows = 1;
    } else if ( select.value === "game"){
        command_wrapper.classList.remove('invisible');
        command_label.innerHTML = "Game";
        command.placeholder = "Enter Current Game Name";
        command.rows = 1;
    } else if ( select.value === "winner"){
        command_wrapper.classList.add('invisible');
    } else {
        command_label.innerHTML = "Command Parameters";
        command.placeholder = "Enter Command Parameters";
        command.rows = 2;
    }
}
const feedbackColorsOK = {
    bg:     "bg-emerald-400/40",
};

const feedbackColorsFAIL = {
    bg:    "bg-red-400/40",
};

function commandFeedbackOK(id) {
    let feedbackEl = document.getElementById(id);
    feedbackEl.classList.remove(feedbackColorsFAIL.bg)
    feedbackEl.classList.add(feedbackColorsOK.bg);
    feedbackEl.classList.remove("invisible");
}

function commandFeedbackFAIL(id){
    let feedbackEl = document.getElementById(id);
    feedbackEl.classList.add(feedbackColorsFAIL.bg);
    feedbackEl.classList.remove(feedbackColorsOK.bg)
    feedbackEl.classList.remove("invisible");
}

function commandFeedbackEnd(id) {
    let feedbackEl = document.getElementById(id);
    feedbackEl.classList.remove(feedbackColorsFAIL.bg);
    feedbackEl.classList.remove(feedbackColorsOK.bg);
    feedbackEl.classList.add('invisible');
    
}

async function commandFeedback(id,result) {
    if (result.timeout === "None" || result.timeout === "0" ){
        var commandTimeout = 5000;
    } else {
        var commandTimeout = parseInt(result.timeout) * 1000;
    }
    commandStatusCode = result.status.code;
    commandMessage = result.feedback;
    if (commandStatusCode === 200){
        commandFeedbackOK(id)
    } else {
        commandFeedbackFAIL(id)
    }

    let feedbackEl = document.getElementById(id);
    let feedbackTextEl = document.getElementById(id+'-text');
    await sleep(commandTimeout);
    console.log('id: '+id+' ## timer ended');
    commandFeedbackEnd(id)
}

function launchCommand(cmd){
    let feebackElId=cmd+'-feedback';
    commandFeedbackOK(feebackElId);
    endpoint = "command/"+cmd+"?chk="+makeId(10)
    //endpoint = "/nightbot/api/channel/send/"+cmd+"?chk="+makeId(10)
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
        commandFeedback(feebackElId,data.result);

    })
    .catch(error => {
        commandFeedbackEnd(feebackElId);
    });
}

function confirmDelete() {
    console.log('confirm delete')
}

function updateCharCount(input,label,length){
    var labelSpan = document.getElementById(label)
    var maxLength = length;
    var strLength = input.value.length;
    if (maxLength <=15){
        warnLength = maxLength*(3/4)
    }else if (maxLength < 20){
        warnLength = maxLength*(2/3)
    }else if (maxLength < 100){
            warnLength = maxLength-10
    }else{
        warnLength = maxLength - 20
    }

    if(strLength > warnLength){
        labelSpan.classList.add('warning')
    } else {
        labelSpan.classList.remove('warning')
    }
    labelSpan.innerHTML = strLength + "/"+maxLength
}


initConfigModal()