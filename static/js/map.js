document.addEventListener("DOMContentLoaded", function () {
  const resultsTag = document.getElementById("parking-data");
  const parkingResults = resultsTag ? JSON.parse(resultsTag.textContent) : [];

  if (!parkingResults || parkingResults.length === 0) {
    console.warn("⚠️ No parkingResults available for map.");
    return;
  }

  console.log("📦 Loaded parkingResults:", parkingResults);

  const mapContainer = document.createElement("div");
  mapContainer.id = "map";
  mapContainer.style.height = "400px";
  mapContainer.style.marginTop = "40px";

  const attachPoint = document.querySelector(".results") || document.querySelector(".search-bar");
  attachPoint.appendChild(mapContainer);

  const map = L.map("map");
  map.setView([53.35, -6.26], 12);

  if (parkingResults.length > 0 && parkingResults[0].lat && parkingResults[0].lon) {
    map.setView([parkingResults[0].lat, parkingResults[0].lon], 14);
  }

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
  }).addTo(map);

  let markerCount = 0;
  const filterSelect = document.getElementById("filter-select");

  parkingResults.forEach((spot) => {
    const avail = parseInt(spot.availability);

    if (filterSelect) {
      const selected = filterSelect.value;
      if (selected === "available" && avail <= 0) return;
      if (selected === "full" && avail > 0) return;
    }

    if (spot.lat && spot.lon) {
      markerCount++;
      const marker = L.marker([spot.lat, spot.lon]).addTo(map);

 marker.bindPopup(`
  <strong>${spot.spot_name}</strong><br>
  Availability: ${spot.availability}<br>
  Lat: ${spot.lat}, Lon: ${spot.lon}<br><br>

  <button class="predict-btn" 
    data-lat="${spot.lat}" 
    data-lon="${spot.lon}">
    🔮 Predict Availability
  </button>

  <div class="prediction-result"></div>  <!-- ✅ Now just below the prediction button -->

  <br>
  <button class="book-now-btn" 
    data-name="${spot.spot_name}" 
    data-lat="${spot.lat}" 
    data-lon="${spot.lon}">
    Book Now
  </button>
`);



    }
  });

  if (filterSelect) {
    filterSelect.addEventListener("change", () => {
      location.reload(); // Simple reload for filter
    });
  }

  console.log(`📍 Rendered ${markerCount} parking markers`);

 document.addEventListener("click", function (e) {
  if (e.target.classList.contains("book-now-btn")) {
   
     const name = e.target.getAttribute("data-name");
    const lat = e.target.getAttribute("data-lat");
    const lon = e.target.getAttribute("data-lon");

    document.getElementById("booking-spot-name").value = name;
    document.getElementById("booking-modal").style.display = "block";
  }

  if (e.target && e.target.classList.contains("predict-btn")) {
    const lat = e.target.getAttribute("data-lat");
    const lon = e.target.getAttribute("data-lon");

    const date = window.selectedDate;
    const time = window.selectedTime;

    if (!date || !time) {
      alert("⚠️ Please select a date and time before predicting.");
      return;
    }

    const button = e.target;
    const popup = button.closest(".leaflet-popup-content");
    const resultDiv = popup.querySelector(".prediction-result");

    resultDiv.textContent = "⏳ Predicting...";

    fetch("/predict-availability", {
      method: "POST",
      headers: {
        "Content-Type": "application/json"
      },
      body: JSON.stringify({
        lat: parseFloat(lat),
        lon: parseFloat(lon),
        date: date,
        time: time
      })
    })
      .then(res => {
        if (!res.ok) throw new Error("Server error " + res.status);
        return res.json();
      })
      .then(data => {
        if (data.prediction !== undefined) {
          resultDiv.textContent = `✅ Predicted: ${data.prediction}`;
        } else {
          resultDiv.textContent = "⚠️ Prediction failed.";
        }
      })
      .catch(err => {
        resultDiv.textContent = "❌ Prediction error.";
      });
  }
});

});
