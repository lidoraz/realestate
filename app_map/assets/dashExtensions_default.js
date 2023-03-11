window.dashExtensions = Object.assign({}, window.dashExtensions, {
    default: {
        function0: function(feature, latlng) {
            console.log("A");
            const flag = L.icon({
                iconUrl: feature.properties.icon,
                iconSize: [28, 28],
            });
            console.log(feature.properties.icon);
            return L.marker(latlng, {
                icon: flag
            });
        },
        function1: function(feature, latlng) {
            const x = L.divIcon({
                className: 'marker-div-icon',
                html: `
        <div class="marker-div">
        <span class="marker-div-span" style="background-color: ${feature.properties._marker_color}">${feature.properties._marker_text}</span>
        <span>${feature.properties._price_s}</span>
        </div>`
            })
            return L.marker(latlng, {
                icon: x
            });
        }

    }
});