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
        },
        function3: function(feature) {
            let is_rent = "price_50" in feature.properties;
            let p = is_rent ? feature.properties.price_50 : feature.properties.price_meter_50
            if (!is_rent) {
                switch (true) {
                    case (p >= 0 && p < 5000):
                        col = "#32671d";
                        break;
                    case (p >= 5000 && p < 10000):
                        col = "#3f6e1c";
                        break;
                    case (p >= 10000 && p < 15000):
                        col = "#4e761b";
                        break;
                    case (p >= 15000 && p < 20000):
                        col = "#617e19";
                        break;
                    case (p >= 20000 && p < 25000):
                        col = "#758618";
                        break;
                    case (p >= 25000 && p < 30000):
                        col = "#8d8e16";
                        break;
                    case (p >= 30000 && p < 35000):
                        col = "#978614";
                        break;
                    case (p >= 35000 && p < 40000):
                        col = "#a07911";
                        break;
                    case (p >= 40000 && p < 45000):
                        col = "#a9690f";
                        break;
                    case (p >= 45000 && p < 50000):
                        col = "#b2560c";
                        break;
                    case (p >= 50000 && p < 55000):
                        col = "#bb3f09";
                        break;
                    case (p >= 55000 && p < 60000):
                        col = "#c52405";
                        break;
                    default:
                        col = "#cf0602";
                }
            } else {
                switch (true) {
                    case (p >= 0 && p < 2000):
                        col = "#32671d";
                        break;
                    case (p >= 2000 && p < 3000):
                        col = "#3f6e1c";
                        break;
                    case (p >= 3000 && p < 4000):
                        col = "#4e761b";
                        break;
                    case (p >= 4000 && p < 5000):
                        col = "#617e19";
                        break;
                    case (p >= 5000 && p < 6000):
                        col = "#758618";
                        break;
                    case (p >= 6000 && p < 7000):
                        col = "#8d8e16";
                        break;
                    case (p >= 7000 && p < 8000):
                        col = "#978614";
                        break;
                    case (p >= 8000 && p < 9000):
                        col = "#a07911";
                        break;
                    case (p >= 9000 && p < 10000):
                        col = "#a9690f";
                        break;
                    case (p >= 10000 && p < 11000):
                        col = "#b2560c";
                        break;
                    case (p >= 11000 && p < 12000):
                        col = "#bb3f09";
                        break;
                    case (p >= 12000 && p < 13000):
                        col = "#c52405";
                        break;
                    default:
                        col = "#cf0602";
                }
            }
            return {
                color: col
            };
        }

    }
});