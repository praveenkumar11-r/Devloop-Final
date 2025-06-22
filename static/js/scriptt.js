

function toggleProfileMenu()
{
    const menu = document.getElementById("profileMenu");
    menu.classList.toggle("hidden");
}

function showAddPanel()
{
    const modal = document.getElementById("addPanelModal");
    modal.classList.remove("hidden");
}

function closeAddPanel()
{
    const modal = document.getElementById("addPanelModal");
    modal.classList.add("hidden");
}

