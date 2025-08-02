// document.addEventListener("DOMContentLoaded", function () {
//   if (typeof parkingResults === "undefined" || parkingResults.length === 0) {
//     console.warn("⚠️ No parkingResults available.");
//     return;
//   }

//   console.log("✅ Map JS loaded");
//   console.log("📦 parkingResults:", parkingResults);

//   const mapContainer = document.createElement("div");
//   mapContainer.id = "map";
//   mapContainer.style.height = "500px";
//   mapContainer.style.marginTop = "20px";

//   const attachPoint = document.querySelector(".results") || document.querySelector(".search-bar");
//   attachPoint.appendChild(mapContainer);

//   const map = L.map("map").setView([53.3498, -6.2603], 13);
//   L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
//     maxZoom: 19,
//   }).addTo(map);

//   let markerCount = 0;

//   parkingResults.forEach((spot) => {
//     if (spot.lat && spot.lon) {
//       markerCount++;
//       const marker = L.marker([spot.lat, spot.lon]).addTo(map);
//       marker.bindPopup(
//         `<strong>${spot.spot_name}</strong><br>
//          Availability: ${spot.availability}<br>
//          Lat: ${spot.lat}, Lon: ${spot.lon}`
//       );
//     }
//   });

//   console.log(`📍 Rendered ${markerCount} parking markers`);
// });

document.addEventListener("DOMContentLoaded", function () {
  // ✅ Read from the <script type="application/json"> blocks
  const resultsTag = document.getElementById("parking-data");
  const parkingResults = resultsTag ? JSON.parse(resultsTag.textContent) : [];

  if (!parkingResults || parkingResults.length === 0) {
    console.warn("⚠️ No parkingResults available for map.");
    return;
  }

  console.log("📦 Loaded parkingResults:", parkingResults);

  // ✅ Insert map container dynamically
  const mapContainer = document.createElement("div");
  mapContainer.id = "map";
  mapContainer.style.height = "400px";
  mapContainer.style.marginTop = "40px";

  const attachPoint = document.querySelector(".results") || document.querySelector(".search-bar");
  attachPoint.appendChild(mapContainer);

  // ✅ Initialize Leaflet map
  const map = L.map("map");

  // Default fallback view
  map.setView([53.35, -6.26], 12);

  // If there’s at least one valid result, center on it
  if (parkingResults.length > 0 && parkingResults[0].lat && parkingResults[0].lon) {
    map.setView([parkingResults[0].lat, parkingResults[0].lon], 14);
  }
  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
  }).addTo(map);

  let markerCount = 0;
  const filterSelect = document.getElementById("filter-select");


  // ✅ Add markers
  // ✅ Add markers with filter logic
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
      // marker.bindPopup(`
      //   <strong>${spot.spot_name}</strong><br>
      //   Availability: ${spot.availability}<br>
      //   Lat: ${spot.lat}, Lon: ${spot.lon}
      // `);
      marker.bindPopup(`
  <strong>${spot.spot_name}</strong><br>
  Availability: ${spot.availability}<br>
  Lat: ${spot.lat}, Lon: ${spot.lon}<br>
  <button class="book-now-btn" data-name="${spot.spot_name}" data-lat="${spot.lat}" data-lon="${spot.lon}">
    Book Now
  </button>
`);

    }
  });

  // ✅ Refresh map on filter change
  if (filterSelect) {
    filterSelect.addEventListener("change", () => {
      location.reload();  // Simple refresh for now — can optimize later
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
  });

});
static / js / map.js
static / js / map.js




