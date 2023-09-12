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

            ,
        function2: function(feature) {
            let pct = feature.properties.pct_change;
            let col = "#C0C0C0";
            let pctLow = 0.05
            if (pct > pctLow) {
                col = "#ff0000" // (pct > 0.07) ? "#ff0000" : "#8B0000";
            } else if (pct < -pctLow) {
                col = "#00ff00" //(pct < -0.07) ? "#00ff00" : "#013220";
            }
            return {
                color: col
            };
        }
    }
});