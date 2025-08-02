document.addEventListener("DOMContentLoaded", function () {
  const searchInput = document.getElementById("search-input");
  const suggestionsBox = document.getElementById("suggestions");

  if (!window.allSpots || !searchInput || !suggestionsBox) return;

  searchInput.addEventListener("input", () => {
    const query = searchInput.value.toLowerCase();
    suggestionsBox.innerHTML = "";

    if (query.length === 0) return;

    const matches = allSpots.filter(spot =>
      spot.spot_name.toLowerCase().includes(query)
    ).slice(0, 10); // max 10 results
    console.log(allSpots)

    matches.forEach(spot => {
      const div = document.createElement("div");
      div.innerHTML = `<strong>${spot.spot_name}</strong><br>Lat: ${spot.lat}, Lon: ${spot.lon} <br><em>${spot.availability}</em>`;
      div.onclick = () => {
        searchInput.value = spot.spot_name;
        suggestionsBox.innerHTML = "";
      };
      suggestionsBox.appendChild(div);
    });
  });
});
