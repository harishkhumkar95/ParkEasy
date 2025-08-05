// Extracted from <script id="parking-data"> and <script id="all-spots-data">
const parkingResults = JSON.parse(document.getElementById('parking-data').textContent);
const allSpots = JSON.parse(document.getElementById('all-spots-data').textContent);
console.log("📦 parkingResults:", parkingResults);
console.log("📍 allSpots:", allSpots);

// Toggle parking results list
const toggleBtn = document.getElementById("toggle-list");
const list = document.getElementById("result-list");

if (toggleBtn && list) {
  toggleBtn.addEventListener("click", () => {
    const isVisible = list.style.display !== "none";
    list.style.display = isVisible ? "none" : "block";
    toggleBtn.textContent = isVisible ? "Show List" : "Hide List";
  });
}

// Handle booking modal form
function submitBooking(e) {
  e.preventDefault();
  alert("✅ Booking confirmed!");
  document.getElementById("booking-modal").style.display = "none";
}


// Navbar toggle for mobile
document.getElementById('menu-toggle').addEventListener('click', function () {
  document.getElementById('nav-menu').classList.toggle('show');
});

// Footer section toggle
function toggleFooterSection(section) {
  const about = document.getElementById("about-footer");
  const contact = document.getElementById("contact-footer");

  if (section === "about") {
    about.style.display = about.style.display === "none" ? "block" : "none";
    contact.style.display = "none";
  }

  if (section === "contact") {
    contact.style.display = contact.style.display === "none" ? "block" : "none";
    about.style.display = "none";
  }

  document.querySelector(".main-footer").scrollIntoView({ behavior: "smooth" });
}
