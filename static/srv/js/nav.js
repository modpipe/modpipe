// Nav Menu Button
const btn = document.querySelector(".mobile-menu")
const menu = document.querySelector(".navmenu")

// Add Event Listener for Menu Button
btn.addEventListener("click", () =>{
menu.classList.toggle("hidden")
})

function togglePassword(id){
    element = document.getElementById(id)
    if (element.type === "password") {
        element.type = "text"
    } else {
        element.type = "password"
    }
}