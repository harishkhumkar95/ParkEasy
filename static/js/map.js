
function createPopupHTML(spot) {
  const lat = spot.lat;
  const lon = spot.lon;
  const avail = spot.availability || spot.status || "N/A";

  // Show emoji + label
  let statusBadge = "";
  if (avail === "0" || avail === "occupied" || avail === 0) {
    statusBadge = `<span style="color:red;">🔴 Spot Full</span>`;
  } else {
    statusBadge = `<span style="color:green;">✅ Spot Available</span>`;
  }

  return `
    <strong>${spot.spot_name}</strong><br>
    Availability: ${avail} ${statusBadge}<br>
    Lat: ${lat}, Lon: ${lon}<br><br>

    <button class="predict-btn" 
      data-lat="${lat}" 
      data-lon="${lon}">
      🔮 Predict Availability
    </button>

    <div class="prediction-result"></div><br>

    <button class="book-now-btn" disabled style="opacity: 0.5; cursor: not-allowed;"
      data-name="${spot.spot_name}" 
      data-lat="${lat}" 
      data-lon="${lon}">
      Book Now
    </button>
  `;
}



const greenIcon = new L.Icon({
  iconUrl: 'https://maps.gstatic.com/mapfiles/ms2/micons/green-dot.png',
  iconSize: [32, 32],
  iconAnchor: [16, 32],
  popupAnchor: [0, -30]
});

const redIcon = new L.Icon({
  iconUrl: 'https://maps.gstatic.com/mapfiles/ms2/micons/red-dot.png',
  iconSize: [32, 32],
  iconAnchor: [16, 32],
  popupAnchor: [0, -30]
});

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

  L.tileLayer("https://{s}.basemaps.cartocdn.com/light_all/{z}/{x}/{y}{r}.png", {
    maxZoom: 19,
    attribution: '&copy; <a href="https://carto.com/">CARTO</a>'
  }).addTo(map);


  let markerCount = 0;
  const filterSelect = document.getElementById("filter-select");
  if (filterSelect) {
    filterSelect.addEventListener("change", () => {
      location.reload();
    });
  }


  const markerMap = {}; // 🔁 Add this just before forEach loop

  parkingResults.forEach((spot) => {
    // const lat = spot.lat;
    // const lon = spot.lon;
    const name = spot.spot_name;
    const lat = parseFloat(spot.lat);
    const lon = parseFloat(spot.lon);
    const key = `${lat}_${lon}`;

    const avail = parseInt(spot.availability);


    if (filterSelect) {
      const selected = filterSelect.value;
      if (selected === "available" && avail <= 0) return;
      if (selected === "full" && avail > 0) return;
    }

    if (spot.lat && spot.lon) {
      markerCount++;
      const marker = L.marker([spot.lat, spot.lon]).addTo(map);
      markerMap[key] = marker // ✅ Save each spot to markerMap by key

      marker.bindPopup(createPopupHTML(spot));



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
      document.getElementById("booking-spot-location").value = name;
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
            const bookBtn = popup.querySelector(".book-now-btn");

            resultDiv.textContent = `✅ Predicted: ${data.prediction}`;

            if (data.prediction === "Available") {
              bookBtn.disabled = false;
              bookBtn.style.opacity = "1";
              bookBtn.style.cursor = "pointer";
            } else {
              bookBtn.disabled = true;
              bookBtn.style.opacity = "0.5";
              bookBtn.style.cursor = "not-allowed";
              resultDiv.innerHTML += `<br><span style="color:red;">❌ Booking disabled. Spot is full.</span>`;
            }
          } else {
            resultDiv.textContent = "⚠️ Prediction failed.";
          }
        })

        .catch(err => {
          resultDiv.textContent = "❌ Prediction error.";
        });
    }
  });


  setInterval(() => {
    const coordinates = Object.keys(markerMap).map(key => {
      const [lat, lon] = key.split("_");
      return { lat: parseFloat(lat), lon: parseFloat(lon) };
    });

    fetch("/api/filtered-status", {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ coordinates })
    })
      .then(res => res.json())
      .then(updatedSpots => {
        updatedSpots.forEach(spot => {
          const key = `${spot.latitude}_${spot.longitude}`;
          const marker = markerMap[key];

          if (marker) {
            const original = parkingResults.find(s =>
              parseFloat(s.lat).toFixed(4) == parseFloat(spot.latitude).toFixed(4) &&
              parseFloat(s.lon).toFixed(4) == parseFloat(spot.longitude).toFixed(4)
            );

            const newHTML = createPopupHTML({
              ...spot,
              lat: spot.latitude,
              lon: spot.longitude,
              spot_name: original ? original.spot_name : "Unknown"
            });

            const popup = marker.getPopup();
            if (popup && map.hasLayer(popup)) {
              popup.setContent(`<div>⏳ Checking availability...</div>`);
            }

            if (popup && map.hasLayer(popup)) {
              popup.setContent(newHTML); // live update if popup is open
            } else {
              marker.bindPopup(newHTML); // update for next open
            }
          }

        });
      })
      .catch(err => console.error("🔴 Error updating filtered markers:", err));
  }, 15000);


});
