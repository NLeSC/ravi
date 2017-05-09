var engineers = {}

function createEngineerTable(engineerList) {
    for(i=0; i<engineerList.length; i++) {
        var e_data = engineerList[i]
        addEngineerTableRow(e_data.eid)
        e = new Engineer(e_data)
        e.plot()
        engineers[e_data.eid] = e
        }
    }

function addEngineerTableRow(eid) {
    var engineerTable = document.getElementById('engineer_table')
    var newrow = engineerTable.insertRow(0)
    var cell1 = newrow.insertCell(0)
    var cell2 = newrow.insertCell(1)
    newrow.id = eid
    cell1.style.width = "100px"
    cell1.innerHTML = eid
    cell2.id = "plot_" + eid
    document.getElementById(eid).addEventListener("click", selectEngineer)
    }

function Engineer(engineer_data) {
    this.eid = engineer_data.eid
    this.exact_id = engineer_data.exact_id
    this.start = engineer_data.start
    this.end = engineer_data.end
    this.fte = engineer_data.fte
    
    this.plot = function () {
        var engineerPlot = document.getElementById("plot_" + this.eid)
        var request = new XMLHttpRequest();

        request.open('POST', 'http://localhost:5000/get_engineer_data');
        request.onload = function() {
            var data = JSON.parse(request.responseText);
            var layout = {
                autosize: false,
                height: 100,
                margin: {l:20,r:0,b:20,t:10},
                barmode: 'stack',
                bargap: 0,
                showlegend: true,
                legend: {x: -0.25, y:1},
                xaxis: {
                    autotick: false,
                    ticks: 'outside',
                    showticklabels: false},
                yaxis: {range: [0, this.fte+0.1]},
                paper_bgcolor: 'rgba(0,0,0,0)',
                plot_bgcolor: 'rgba(0,0,0,0)'
                };

            Plotly.newPlot(engineerPlot, data, layout, {displayModeBar: false});
            }
        request.setRequestHeader("Content-type", "application/x-www-form-urlencoded")
        request.send('eid=' + this.eid);
        }
    }

function plotEngineer() {
    var eid = document.getElementById('engineerform').elements['name'].value
    var exact_id = document.getElementById('engineerform').elements['exact'].value
    console.log(exact_id)
    var request = new XMLHttpRequest();
    request.open('POST', 'http://localhost:5000/get_engineer_plot');
    request.onload = function() {
        var data = JSON.parse(request.responseText)
        console.log(data)
        var plot_detailed = document.getElementById("plot_detailed")
        var layout = {
            title: eid,
            autosize: true,
            height: 250,
            margin: {l:50,r:0,b:100,t:25},
            showlegend: true,
            xaxis: {
                type: 'date',
                autotick: true,
                ticks: 'outside',
                tickangle: 90,
                nticks: 24
                },
            };

        Plotly.newPlot(plot_detailed, data, layout, {displayModeBar: false});
        }
    request.setRequestHeader("Content-type", "application/x-www-form-urlencoded")
    request.send('eid=' + eid + '&exact=' + exact_id);
    }

function selectEngineer() {
    engineer = engineers[this.id]
    if (this.style.backgroundColor == "lavender") {
        clearEngineerSelection()
        }
    else {
        document.getElementById("engineer_name").value = engineer.eid
        document.getElementById("engineer_fte").value = engineer.fte
        document.getElementById("engineer_start").value = engineer.start
        document.getElementById("engineer_end").value = engineer.end
        document.getElementById("engineer_exact").value = engineer.exact_id
        document.getElementById("assignment_eid").value = engineer.eid
        unhighlightEngineers()
        this.style.backgroundColor = "lavender"
        }
    updateAssignments()
    }

function clearEngineerSelection() {
    document.getElementById("engineerform").reset()
    document.getElementById("assignment_eid").value = ""
    unhighlightEngineers()
    updateAssignments()
    }

function unhighlightEngineers() {
    var tableRows = document.getElementById("engineer_table").getElementsByTagName("tr")
    for(r=0; r<tableRows.length; r++) {
        tableRows[r].style.backgroundColor = "white"
        }
    }

function addEngineer() {
    eid = document.getElementById("engineer_name").value
    fte = document.getElementById("engineer_fte").value
    start = document.getElementById("engineer_start").value
    end = document.getElementById("engineer_end").value
    exact = document.getElementById("engineer_exact").value
    engineer_data = {
        "eid": eid,
        "fte": fte,
        "start": start,
        "end": end,
        "exact_id": exact
        }
    if (!(eid in engineers)) {
        addEngineerTableRow(eid)
        }
    engineers[eid] = new Engineer(engineer_data)

    request_add_engineer = new XMLHttpRequest()
    request_add_engineer.open('POST', 'http://localhost:5000/add_engineer')
    request_add_engineer.onload = function() {engineers[eid].plot()}
    request_add_engineer.setRequestHeader("Content-type", "application/x-www-form-urlencoded")
    request_add_engineer.send('data=' + JSON.stringify(engineer_data))    
    }

function delEngineer() {
    eid = document.getElementById("engineer_name").value
    if (confirm("Do you want to remove engineer " + eid + " and all his/her assignments?") == true) {
        document.getElementById(eid).remove()
        request_del_engineer = new XMLHttpRequest()
        request_del_engineer.open('POST', 'http://localhost:5000/del_engineer')
        request_del_engineer.setRequestHeader("Content-type", "application/x-www-form-urlencoded")
        request_del_engineer.send('eid=' + eid)    
        }
    }

function printEngineers()
{
    var print_window = window.open('', 'PRINT', 'height=600,width=1000')

    print_window.document.write('<html><head><title>' + document.title  + '</title>')
    print_window.document.write('</head><body><h1>Engineer planning</h1><div style="height:100%">')
    print_window.document.write(document.getElementById("engineers").innerHTML)
    print_window.document.write('<table><tr><td style="width: 100px"></td><td>')
    print_window.document.write(document.getElementById("xLabels1").innerHTML)
    print_window.document.write('</td></tr></table></div><script src="js/plotly-latest.min.js"></script></body></html>')
    print_window.document.close(); // necessary for IE >= 10
    print_window.focus(); // necessary for IE >= 10*/
//    print_window.print();
//    print_window.close();

    return true;
}

var request_engineers = new XMLHttpRequest();
request_engineers.open('GET', 'http://localhost:5000/get_engineers');
request_engineers.onload = function() {
    var engineerList = JSON.parse(request_engineers.responseText);
    createEngineerTable(engineerList);
    }
request_engineers.send();


