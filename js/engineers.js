var engineers = {}

function createEngineerTable(engineerList) {
    for(i=0; i<engineerList.length; i++) {
        var e_data = engineerList[i]
        addEngineerTableRow(e_data.person_id, e_data.sname)
        e = new Engineer(e_data)
        e.plot()
        engineers[e_data.person_id] = e
        }
    }

function addEngineerTableRow(eid, sname) {
    var engineerTable = document.getElementById('engineer_table')
    var newrow = engineerTable.insertRow(-1)
    var cell1 = newrow.insertCell(0)
    var cell2 = newrow.insertCell(1)
    newrow.id = 'e' + eid
    cell1.innerHTML = '<div style="width:135px">' + sname + '</div>'
    cell2.id = "eplot_" + eid
    document.getElementById('e' + eid).addEventListener("click", function() {
        selectEngineer(eid)
        })
    }

function Engineer(engineer_data) {
    this.person_id = engineer_data.person_id
    this.sname = engineer_data.sname
    this.exact_id = engineer_data.exact_id
    this.start = engineer_data.contract_start
    this.end = engineer_data.contract_end
    this.fte = engineer_data.fte
    this.comments = engineer_data.comments
    this.active = (engineer_data.status == 'active')
    
    this.plot = function () {
        var engineerPlot = document.getElementById("eplot_" + this.person_id)
        var request = new XMLHttpRequest();

        request.open('POST', 'http://localhost:5000/get_engineer_data');
        request.onload = function() {
            plotPlanning(JSON.parse(request.responseText), engineerPlot);
            }
        request.setRequestHeader("Content-type", "application/x-www-form-urlencoded")
        request.send('eid=' + this.person_id);
        }
    }

function plotEngineer(person_id, popup=false) {
    var eid = document.getElementById('engineerform').elements['name'].value
    var exact_id = document.getElementById('engineerform').elements['exact'].value
    var request = new XMLHttpRequest();
    request.open('POST', 'http://localhost:5000/get_engineer_plot');
    request.onload = function() {
        plotDetails(JSON.parse(request.responseText), eid, 0.95, 'right', popup);
        }
    request.setRequestHeader("Content-type", "application/x-www-form-urlencoded")
    request.send('eid=' + person_id + '&exact=' + exact_id);
    }

function selectEngineer(eid) {
    var engineer = engineers[eid]
    var row = document.getElementById('e' + eid)
    if (row.style.backgroundColor == "lavender") {
        clearEngineerSelection()
        }
    else {
        document.getElementById("engineer_name").value = engineer.sname
        document.getElementById("engineer_id").value = engineer.person_id
        document.getElementById("engineer_fte").value = engineer.fte
        document.getElementById("engineer_start").value = engineer.start
        document.getElementById("engineer_end").value = engineer.end
        document.getElementById("engineer_exact").value = engineer.exact_id
        document.getElementById("engineer_comments").value = engineer.comments
        document.getElementById("engineer_active").checked = engineer.active
        resetAssignmentForm()
        unhighlightEngineers()
        row.style.backgroundColor = "lavender"
        plotEngineer(engineer.person_id)
        }
    updateAssignments()
    }

function clearEngineerSelection() {
    document.getElementById("engineerform").reset()
    unhighlightEngineers()
    resetAssignmentForm()
    updateAssignments()
    }

function unhighlightEngineers() {
    var tableRows = document.getElementById("engineer_table").getElementsByTagName("tr")
    for(r=0; r<tableRows.length; r++) {
        tableRows[r].style.backgroundColor = "white"
        }
    }

function scrollToEngineer() {
    var query = document.getElementById("engineer_name").value.toLowerCase()
    if (query.length > 0) {
        for(eid in engineers) {
            if (engineers[eid].sname.toLowerCase().indexOf(document.getElementById("engineer_name").value.toLowerCase()) == 0) {
                document.getElementById('e' + eid).scrollIntoView();
                break;
                }
            }
        }
    }

function updateInactiveEngineers() {
    var tableRows = document.getElementById("engineer_table").getElementsByTagName("tr")
    var showInactives = document.getElementById('timerangeform').elements['inactive_engineers'].checked
    for(r=0; r<tableRows.length; r++) {
        if (engineers[tableRows[r].id.substr(1)].active || showInactives) {
            tableRows[r].style.display = "";
            }
        else {
            tableRows[r].style.display = "none";
            }
        }
    }

function addEngineer() {
    var sname = document.getElementById("engineer_name").value
    var eid = document.getElementById("engineer_id").value
    var fte = document.getElementById("engineer_fte").value
    var start = document.getElementById("engineer_start").value
    var end = document.getElementById("engineer_end").value
    var exact = document.getElementById("engineer_exact").value
    var comments = document.getElementById("engineer_comments").value
    var active = document.getElementById("engineer_active").checked
    var engineer_data = {
        "sname": sname,
        "person_id": eid,
        "fte": fte,
        "contract_start": (start == "") ? new Date().toISOString().substr(0,7) : start,
        "contract_end": (end == "") ? document.getElementById("timerangeform").elements["end_date"].value : end,
        "exact_id": exact,
        "comments": comments,
        "status": (active) ? "active" : "inactive"
        }
    request_add_engineer = new XMLHttpRequest()
    request_add_engineer.open('POST', 'http://localhost:5000/add_engineer')
    request_add_engineer.onload = function() {
        if (checkResponse(request_add_engineer)) {
            eid = JSON.parse(request_add_engineer.responseText)
            engineer_data["person_id"] = eid
            if (!(eid in engineers)) {
                addEngineerTableRow(eid, sname)
                }
            engineers[eid] = new Engineer(engineer_data)
            engineers[eid].plot();
            updateInactiveEngineers();
            document.getElementById('e' + eid).scrollIntoView();
            selectEngineer(eid);
            }
        }
    request_add_engineer.setRequestHeader("Content-type", "application/x-www-form-urlencoded")
    request_add_engineer.send('data=' + JSON.stringify(engineer_data))    
    }

function renameEngineer() {
    var eid = document.getElementById("engineer_id").value
    if (eid) {
        var newname = prompt("Change name of engineer \"" + engineers[eid].sname + "\" into:", engineers[eid].sname)
        request_rename_engineer = new XMLHttpRequest()
        request_rename_engineer.open('POST', 'http://localhost:5000/rename_engineer')
        request_rename_engineer.onload = function() {
            location.reload()
            }
        request_rename_engineer.setRequestHeader("Content-type", "application/x-www-form-urlencoded")
        request_rename_engineer.send('eid=' + eid + '&newname=' + newname)
        }
    }

function delEngineer() {
    var eid = document.getElementById("engineer_id").value
    if (eid) {
        if (confirm("Do you want to remove engineer \"" + engineers[eid].sname + "\" and all his/her assignments?") == true) {
            request_del_engineer = new XMLHttpRequest()
            request_del_engineer.open('POST', 'http://localhost:5000/del_engineer')
            request_del_engineer.onload = function() {
                location.reload()
                }
            request_del_engineer.setRequestHeader("Content-type", "application/x-www-form-urlencoded")
            request_del_engineer.send('eid=' + eid)
            clearEngineerSelection()
            }
        }
    }

function printEngineers() {
    var print_window = window.open('', 'PRINT', 'height=600,width=1000')

    print_window.document.write('<html><head><title>' + document.title  + '</title>')
    print_window.document.write('<style>tr {page-break-inside: avoid}</style>')
    print_window.document.write('</head><body><h1>Engineer planning</h1><table>')
    print_window.document.write('<tfoot><tr ><td style="width: 100px"></td><td>')
    print_window.document.write(document.getElementById("xLabels1").innerHTML + '</td></tr></tfoot>')
    print_window.document.write('<tbody>' + document.getElementById("engineer_table").innerHTML)
    print_window.document.write('</tbody></table><script src="js/plotly-latest.min.js"></script></body></html>')
    print_window.document.close(); // necessary for IE >= 10
    print_window.focus(); // necessary for IE >= 10*/
    print_window.print();
    print_window.close();

    return true;
}

var request_engineers = new XMLHttpRequest();
request_engineers.open('GET', 'http://localhost:5000/get_engineers');
request_engineers.onload = function() {
    var engineerList = JSON.parse(request_engineers.responseText);
    createEngineerTable(engineerList);
    updateInactiveEngineers();
    }
request_engineers.send();



