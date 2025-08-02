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
  const map = L.map("map").setView([53.35, -6.26], 12);  // Zoom into Dublin center

  L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    maxZoom: 19,
  }).addTo(map);

  let markerCount = 0;

  // ✅ Add markers
  parkingResults.forEach((spot) => {
    if (spot.lat && spot.lon) {
      markerCount++;
      const marker = L.marker([spot.lat, spot.lon]).addTo(map);
      marker.bindPopup(`
        <strong>${spot.spot_name}</strong><br>
        Availability: ${spot.availability}<br>
        Lat: ${spot.lat}, Lon: ${spot.lon}
      `);
    }
  });

  console.log(`📍 Rendered ${markerCount} parking markers`);
});


