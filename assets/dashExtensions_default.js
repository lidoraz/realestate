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
            let col = "#5a5a5a"; //"#C0C0C0";
            let pctLow = feature.properties.type == "N" ? 0.05 : 0.03;
            if (pct > pctLow) {
                col = "#ff0000";
            } else if (pct < -pctLow) {
                col = "#00ff00";
            }
            return {
                color: col
            };
        }
    }
});