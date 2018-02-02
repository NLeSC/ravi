function plotDetails(data, title, x, xanchor, popup=false) {
    var plot_detailed = document.getElementById("plot_detailed")
    var layout = {
        autosize: true,
        height: 270,
        margin: {l:50,r:0,b:100,t:0},
        barmode: 'stack',
        showlegend: true,
        xaxis: {
            type: 'category',
            autotick: true,
            ticks: 'outside',
            tickangle: 30,
            nticks: 25
            },
        annotations: [{
            xref: 'paper',
            yref: 'paper',
            x: x,
            xanchor: xanchor,
            y: 1,
            yanchor: 'top',
            font: {
                size: 20
                },
            borderwidth: 0,
            text: '<b>' + title + '</b>',
            showarrow: false
            }],
        };

    new_plot = Plotly.newPlot(plot_detailed, data, layout, {displayModeBar: false})
    if(popup) {
        popupDetailedPlot(new_plot);
        }
    }

function popupDetailedPlot(new_plot) {
    plot_image = new_plot.then(
        function(gd) {
            Plotly.toImage(gd,{format:'jpeg',height:700,width:1200}).then(
                function(image) {
                    var print_window = window.open('', 'RaviDetailedPlot', 'height=720,width=1220')
                    print_window.document.write('<html><head><title>RAVI Plot</title>')
                    print_window.document.write('</head><body><div style="height:100%">')
                    print_window.document.write('<img src="')
                    print_window.document.write(image)
                    print_window.document.write('"></img></div>')
                    print_window.document.write('</body></html>')
                    print_window.document.close(); // necessary for IE >= 10
                    print_window.focus(); // necessary for IE >= 10*/
                    });
            });

    return true;
    }

