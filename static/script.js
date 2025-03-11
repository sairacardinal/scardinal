function confirmLogout(event) {
    event.preventDefault();
    if (confirm("Are you sure you want to log out?")) {
        window.location.href = event.target.href;
    }
}