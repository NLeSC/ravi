/**
 * Add engineers to the engineer timeline
 * Add engineers to the project assignment popup
 *
 * An engineer is an object with the following properties:
 * Engineer {
 *   active
 *   comments
 *   coordinator
 *   eid
 *   end
 *   start
 *   exact_id
 *   fte
 * }
 *
 * arguments:
 *    engineers: Array[engineer]
 *
 * uses the following global variables:
 *    engineerGroups
 */
function initializeEngineers (engineers) {
  engineers.forEach(function(engineer) {
    engineerGroups.update({
      id: engineer.eid,
      content: engineer.eid
    });
  });

  // TODO: remove old options
  // add to the modal pop up on the project timeline
  inputBox = $('#inputProjectsTimelineEngineer');
  engineerGroups.forEach(function(engineer) {
    $('<option />', {
      value: engineer.id,
      text: engineer.content
    }).appendTo(inputBox);
  });
}

/**
 * Request the engineer loads from the server
 */
function get_engineer_load () {
  var request = new XMLHttpRequest();

  request.open('POST', 'http://localhost:5000/get_engineer_load');
  request.onload = (function(pid) {
    return function() {
      var old_backgrounds = [];
      engineerAssignments.forEach(function (a) {
        if (a.type == 'background') {
          old_backgrounds.push(a.id);
        }
      })
      engineerAssignments.remove(old_backgrounds);

      var data = JSON.parse(request.responseText);
      data.forEach(function (load) {
        if (load.fte < -0.5) {
          color = 'green';
        } else if (load.fte < -0.2) {
          color = 'yellow';
        } else if (load.fte < 0.0) {
          color = 'white';
        } else if (load.fte < 0.2) {
          color = 'orange';
        } else {
          color = 'red';
        }
        engineerAssignments.add({
          group: load.eid,
          type: 'background',
          start: load.start,
          end: load.end,
          editable: false,
          style: "opacity: " + load.fte + ";background-color: " + color
        });
      })
    };
  })(this.pid);
  request.setRequestHeader("Content-type", "application/x-www-form-urlencoded")
  request.send();
}

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
    var newrow = engineerTable.insertRow(-1)
    var cell1 = newrow.insertCell(0)
    var cell2 = newrow.insertCell(1)
    newrow.id = eid
    cell1.innerHTML = '<div style="width:135px">' + eid + '</div>'
    cell2.id = "plot_" + eid
    document.getElementById(eid).addEventListener("click", function() {
        selectEngineer(eid)
        })
    }

function Engineer(engineer_data) {
    this.eid = engineer_data.eid
    this.exact_id = engineer_data.exact_id
    this.start = engineer_data.start
    this.end = engineer_data.end
    this.fte = engineer_data.fte
    this.comments = engineer_data.comments
    this.active = engineer_data.active
    
    this.plot = function () {
        var engineerPlot = document.getElementById("plot_" + this.eid)
        var request = new XMLHttpRequest();

        request.open('POST', 'http://localhost:5000/get_engineer_data');
        request.onload = function() {
            plotPlanning(JSON.parse(request.responseText), engineerPlot);
            }
        request.setRequestHeader("Content-type", "application/x-www-form-urlencoded")
        request.send('eid=' + this.eid);
        }
    }

function plotEngineer(popup=false) {
    var eid = document.getElementById('engineerform').elements['name'].value
    var exact_id = document.getElementById('engineerform').elements['exact'].value
    var request = new XMLHttpRequest();
    request.open('POST', 'http://localhost:5000/get_engineer_plot');
    request.onload = function() {
        plotDetails(JSON.parse(request.responseText), eid, 0.95, 'right', popup);
        }
    request.setRequestHeader("Content-type", "application/x-www-form-urlencoded")
    request.send('eid=' + eid + '&exact=' + exact_id);
    }

function selectEngineer(eid) {
    var engineer = engineers[eid]
    var row = document.getElementById(eid)
    if (row.style.backgroundColor == "lavender") {
        clearEngineerSelection()
        }
    else {
        document.getElementById("engineer_name").value = engineer.eid
        document.getElementById("engineer_fte").value = engineer.fte
        document.getElementById("engineer_start").value = engineer.start
        document.getElementById("engineer_end").value = engineer.end
        document.getElementById("engineer_exact").value = engineer.exact_id
        document.getElementById("engineer_comments").value = engineer.comments
        document.getElementById("engineer_active").checked = engineer.active
        resetAssignmentForm()
        unhighlightEngineers()
        row.style.backgroundColor = "lavender"
        plotEngineer()
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
            console.log(eid)
            if (eid.toLowerCase().indexOf(document.getElementById("engineer_name").value.toLowerCase()) == 0) {
                document.getElementById(eid).scrollIntoView();
                break;
                }
            }
        }
    }

function updateInactiveEngineers() {
    var tableRows = document.getElementById("engineer_table").getElementsByTagName("tr")
    var showInactives = document.getElementById('timerangeform').elements['inactive_engineers'].checked
    for(r=0; r<tableRows.length; r++) {
        if (engineers[tableRows[r].id].active || showInactives) {
            tableRows[r].style.display = "";
            }
        else {
            tableRows[r].style.display = "none";
            }
        }
    }

function addEngineer() {
    var eid = document.getElementById("engineer_name").value
    var fte = document.getElementById("engineer_fte").value
    var start = document.getElementById("engineer_start").value
    var end = document.getElementById("engineer_end").value
    var exact = document.getElementById("engineer_exact").value
    var comments = document.getElementById("engineer_comments").value
    var active = document.getElementById("engineer_active").checked
    var engineer_data = {
        "eid": eid,
        "fte": fte,
        "start": start,
        "end": end,
        "exact_id": exact,
        "comments": comments,
        "active": active
        }
    request_add_engineer = new XMLHttpRequest()
    request_add_engineer.open('POST', 'http://localhost:5000/add_engineer')
    request_add_engineer.onload = function() {
        if (checkResponse(request_add_engineer)) {
            if (!(eid in engineers)) {
                addEngineerTableRow(eid)
                }
            engineers[eid] = new Engineer(engineer_data)
            engineers[eid].plot()
            updateInactiveEngineers()
            }
        }
    request_add_engineer.setRequestHeader("Content-type", "application/x-www-form-urlencoded")
    request_add_engineer.send('data=' + JSON.stringify(engineer_data))    
    }

function renameEngineer() {
    var eid = document.getElementById("engineer_name").value
    if (eid) {
        var newID = prompt("Change name of engineer \"" + eid + "\" into:", eid)
        request_rename_engineer = new XMLHttpRequest()
        request_rename_engineer.open('POST', 'http://localhost:5000/rename_engineer')
        request_rename_engineer.onload = function() {
            location.reload()
            }
        request_rename_engineer.setRequestHeader("Content-type", "application/x-www-form-urlencoded")
        request_rename_engineer.send('eid=' + eid + '&newid=' + newID)
        }
    }

function delEngineer() {
    var eid = document.getElementById("engineer_name").value
    if (eid) {
        if (confirm("Do you want to remove engineer \"" + eid + "\" and all his/her assignments?") == true) {
            document.getElementById(eid).remove()
            delete engineers[eid]
            request_del_engineer = new XMLHttpRequest()
            request_del_engineer.open('POST', 'http://localhost:5000/del_engineer')
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
    initializeEngineers(engineerList);
    createEngineerTable(engineerList);
    updateInactiveEngineers();
    }
request_engineers.send();
