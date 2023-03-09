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
                console.log("1");
                // console.log(feature.properties.icon);
                const x = L.divIcon({
                    className: 'marker-div-icon',
                    html: `<img class="marker-div-image" src="${feature.properties.icon}"/>
        <div class="marker-div">
        <span class="marker-div-span" style="background-color: ${feature.properties._c1}">${feature.properties._t1}</span>
        <span class="marker-div-span" style="background-color: ${feature.properties._c2}">${feature.properties._t2}</span>
        <span class="marker-div-span" style="background-color: ${feature.properties._c3}">${feature.properties._t3}</span>
        </div>`
                })
                console.log("2");
                return L.marker(latlng, {
                    icon: x
                });
            }

            ,
        function2: function(feature, latlng) {
            console.log("1");
            // console.log(feature.properties.icon);
            const x = L.divIcon({
                className: 'marker-div-icon',
                html: `
        <div class="marker-div">
        <span class="marker-div-span" style="background-color: ${feature.properties._marker_color}">${feature.properties._marker_text}</span>
        </div>`
            })
            console.log("2");
            return L.marker(latlng, {
                icon: x
            });
        }

    }
});