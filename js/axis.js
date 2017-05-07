function plotxAxis(id, xAxisLabels) {
    var xAxis = document.getElementById(id)
    var layout = {
        autosize: false,
        height: 100,
        margin: {l:20,r:0,b:100,t:0},
        barmode: 'stack',
        bargap: 0,
        showlegend: true,
        legend: {x: -0.25, y:1},
        yaxis: {
            range: [0, 1],
            showticklabels: false
            },
        xaxis: {
            type: 'date',
            autotick: true,
            ticks: 'outside',
            tickangle: 90,
            nticks: 24
            },
        paper_bgcolor: 'rgba(0,0,0,0)',
        plot_bgcolor: 'rgba(0,0,0,0)'
        };

    console.log(xAxisLabels)
    Plotly.plot(xAxis, xAxisLabels, layout, {displayModeBar: false});
    }

function updateTimeRange() {
    var form = document.getElementById('timerangeform')
    start = form.elements["start_date"].value
    end = form.elements["end_date"].value
    request_update_start = new XMLHttpRequest()
    request_update_start.open('POST', 'http://localhost:5000/set_user_setting')
    request_update_start.setRequestHeader("Content-type", "application/x-www-form-urlencoded")
    request_update_start.send('setting=start_date&value=' + start)    
    request_update_start = new XMLHttpRequest()
    request_update_start.open('POST', 'http://localhost:5000/set_user_setting')
    request_update_start.onload = function() {
        location.reload()
        }
    request_update_start.setRequestHeader("Content-type", "application/x-www-form-urlencoded")
    request_update_start.send('setting=end_date&value=' + end)    
    }

var request_xaxis_data = new XMLHttpRequest();
request_xaxis_data.open('GET', 'http://localhost:5000/get_xaxis_data', true);
request_xaxis_data.onload = function() {
    var xAxisData = JSON.parse(request_xaxis_data.responseText);
    plotxAxis("xLabels1", xAxisData.labels);
    plotxAxis("xLabels2", xAxisData.labels);
    var form = document.getElementById('timerangeform')
    form.elements["start_date"].value = xAxisData.start_month
    form.elements["end_date"].value = xAxisData.end_month
    }
request_xaxis_data.send();


