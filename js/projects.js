var projects = {}

function createProjectTable(projectList) {
    for(i=0; i<projectList.length; i++) {
        var p_data = projectList[i]
        addProjectTableRow(p_data.project_id, p_data.sname)
        p = new Project(p_data)
        p.plot()
        projects[p_data.project_id] = p
        }
    togglePlanningHistory(); // Make sure to show the right totals
    }

function addProjectTableRow(pid, sname) {
    var projectTable = document.getElementById('project_table')
    var newrow = projectTable.insertRow(-1)
    var cell1 = newrow.insertCell(0)
    var cell2 = newrow.insertCell(1)
    newrow.id = 'p' + pid
    cell1.innerHTML = '<div style="width:135px">' + sname + '</div>' +
              '<div id="planned_' + pid + '"></div>' + // This will be displayed with Planning history checked
              '<div id="combined_' + pid + '"></div>' // This will be displayed with Planning history unchecked
    cell2.id = "pplot_" + pid
    document.getElementById('p' + pid).addEventListener("click", function() {
        selectProject(pid)
        })
    }

function togglePlanningHistory() {
    var history = document.getElementById('timerangeform').elements['planning_history'].checked;
    for (pid in projects) {
        planned_id = document.getElementById("planned_" + pid);
        combined_id = document.getElementById("combined_" + pid);
        if (history) { // Show total of planned person-years only
            planned_id.style.display = "";
            combined_id.style.display = "none";
            }
        else { // Show combined result of written and planned person-years
            planned_id.style.display = "none";
            combined_id.style.display = "";
            }
        }
    if (document.getElementById("project_name").value != "") {
        plotProject(); // Update the project plot
        }
    }

function Project(project_data) {
    this.project_id = project_data.project_id
    this.sname = project_data.sname
    this.exact = project_data.exact_id
    this.start = project_data.project_start
    this.end = project_data.project_end
    this.fte = project_data.fte
    this.coordinator = project_data.coordinator
    this.comments = project_data.comments
    this.active = (project_data.status == 'active')
    
    this.plot = function () {
        var projectPlot = document.getElementById("pplot_" + this.project_id)
        var request = new XMLHttpRequest();

        request.open('POST', 'http://localhost:5000/get_project_data');
        request.onload = (function(pid) {
            return function() {
                var data = JSON.parse(request.responseText);
                plotPlanning(data.plot, projectPlot)
                document.getElementById("planned_" + pid).innerHTML = data.planned
                document.getElementById("combined_" + pid).innerHTML = data.combined
                };
            })(this.project_id);
        request.setRequestHeader("Content-type", "application/x-www-form-urlencoded")
        request.send('pid='+this.project_id);
        }
    }

function plotProject(popup=false) {
    var pid = document.getElementById('projectform').elements['name'].value
    var project_id = document.getElementById('projectform').elements['project_id'].value
    var history = document.getElementById('timerangeform').elements['planning_history'].checked;
    var request = new XMLHttpRequest();
    request.open('POST', 'http://localhost:5000/get_project_plot');
    request.onload = function() {
        plotDetails(JSON.parse(request.responseText), pid, 0.05, 'left', popup);
        }
    request.setRequestHeader("Content-type", "application/x-www-form-urlencoded")
    request.send('pid=' + project_id + '&history=' + history);
    }


function selectProject(pid) {
    var project = projects[pid]
    var row = document.getElementById('p' + pid)
    if (row.style.backgroundColor == "lavender") {
        clearProjectSelection()
        }
    else {
        document.getElementById("project_name").value = project.sname
        document.getElementById("project_id").value = project.project_id
        document.getElementById("project_fte").value = project.fte
        document.getElementById("project_start").value = project.start
        document.getElementById("project_end").value = project.end
        document.getElementById("project_coordinator").value = project.coordinator
        document.getElementById("project_exact").value = project.exact
        document.getElementById("project_comments").value = project.comments
        document.getElementById("project_active").checked = project.active
        resetAssignmentForm()
        unhighlightProjects()
        row.style.backgroundColor = "lavender"
        plotProject()
        }
    updateAssignments()
    }

function clearProjectSelection() {
    document.getElementById("projectform").reset()
    document.getElementById("project_coordinator").value = 0
    unhighlightProjects()
    resetAssignmentForm()
    updateAssignments()
    }

function unhighlightProjects() {
    var tableRows = document.getElementById("project_table").getElementsByTagName("tr")
    for(r=0; r<tableRows.length; r++) {
        tableRows[r].style.backgroundColor = "white"
        }
    }

function scrollToProject() {
    var query = document.getElementById("project_name").value.toLowerCase()
    var showInactives = document.getElementById('timerangeform').elements['inactive_projects'].checked
    if (query.length > 0) {
        for(pid in projects) {
            if ((projects[pid].active || showInactives) &&
                    projects[pid].sname.toLowerCase().indexOf(document.getElementById("project_name").value.toLowerCase()) != -1) {
                document.getElementById('p' + pid).scrollIntoView();
                break;
                }
            }
        }
    }

function updateInactiveProjects() {
    var tableRows = document.getElementById("project_table").getElementsByTagName("tr")
    var showInactives = document.getElementById('timerangeform').elements['inactive_projects'].checked
    for(r=0; r<tableRows.length; r++) {
        if (projects[tableRows[r].id.substr(1)].active || showInactives) {
            tableRows[r].style.display = "";
            }
        else {
            tableRows[r].style.display = "none";
            }
        }
    }

function addProject() {
    var sname = document.getElementById("project_name").value
    var pid = document.getElementById("project_id").value
    var fte = document.getElementById("project_fte").value
    var start = document.getElementById("project_start").value
    var end = document.getElementById("project_end").value
    var exact = document.getElementById("project_exact").value
    var coordinator = document.getElementById("project_coordinator").value
    var comments = document.getElementById("project_comments").value
    var active = document.getElementById("project_active").checked
    var project_data = {
        "sname": sname,
        "project_id": pid,
        "fte": fte,
        "project_start": (start == "") ? new Date().toISOString().substr(0,7) : start,
        "project_end": (end == "") ? document.getElementById("timerangeform").elements["end_date"].value : end,
        "exact_id": exact,
        "coordinator": coordinator,
        "comments": comments,
        "status": (active) ? "active": "inactive"
        }
    request_add_project = new XMLHttpRequest()
    request_add_project.open('POST', 'http://localhost:5000/add_project')
    request_add_project.onload = function() {
        if (checkResponse(request_add_project)) {
            pid = JSON.parse(request_add_project.responseText)
            project_data["project_id"] = pid
            if (!(pid in projects)) {
                addProjectTableRow(pid, sname)
                }
            projects[pid] = new Project(project_data)
            projects[pid].plot()
            updateInactiveProjects()
            document.getElementById('p' + pid).scrollIntoView();
            selectProject(pid);
            }
        }
    request_add_project.setRequestHeader("Content-type", "application/x-www-form-urlencoded")
    request_add_project.send('data=' + escape(JSON.stringify(project_data)))
    }

function renameProject() {
    var pid = document.getElementById("project_id").value
    if (pid) {
        var newname = prompt("Change name of project \"" + projects[pid].sname + "\" into:", projects[pid].sname)
        request_rename_project = new XMLHttpRequest()
        request_rename_project.open('POST', 'http://localhost:5000/rename_project')
        request_rename_project.onload = function() {
            location.reload()
            }
        request_rename_project.setRequestHeader("Content-type", "application/x-www-form-urlencoded")
        request_rename_project.send('pid=' + pid + '&newname=' + newname)
        }
    }

function delProject() {
    var pid = document.getElementById("project_id").value
    if (pid) {
        if (confirm("Do you want to remove project \"" + projects[pid].sname + "\" and all its assignments?") == true) {
            request_del_project = new XMLHttpRequest()
            request_del_project.open('POST', 'http://localhost:5000/del_project')
            request_del_project.onload = function() {
                location.reload()
                }
            request_del_project.setRequestHeader("Content-type", "application/x-www-form-urlencoded")
            request_del_project.send('pid=' + pid)
            clearProjectSelection()
            }
        }
    }

function printProjects() {
    var print_window = window.open('', 'PRINT', 'height=600,width=1000')

    print_window.document.write('<html><head><title>' + document.title  + '</title>')
    print_window.document.write('<style>tr {page-break-inside: avoid}</style>')
    print_window.document.write('</head><body><h1>Project planning</h1><table>')
    print_window.document.write('<tfoot><tr ><td style="width: 100px"></td><td>')
    print_window.document.write(document.getElementById("xLabels2").innerHTML + '</td></tr></tfoot>')
    print_window.document.write('<tbody>' + document.getElementById("project_table").innerHTML)
    print_window.document.write('</tbody></table><script src="js/plotly-latest.min.js"></script></body></html>')
    print_window.document.close(); // necessary for IE >= 10
    print_window.focus(); // necessary for IE >= 10*/
    print_window.print();
    print_window.close();

    return true;
    }

function date2ym(date) {
    var d = date.split('-');
    return 12 * parseInt(d[0]) + parseInt(d[1]) - 1;
    }

function assignCoordinator() {
    var pid = document.getElementById("project_name").value
    var fte = document.getElementById("project_fte").value
    var start = document.getElementById("project_start").value
    var end = document.getElementById("project_end").value
    var coordinator = document.getElementById("project_coordinator").value
    var form = document.getElementById('assignmentsform')
    form.elements['eid'].value = coordinator
    form.elements['pid'].value = pid
    form.elements['fte'].value = Math.round(fte * 12 / (date2ym(end) - date2ym(start)) * 5) / 100
    form.elements['start'].value = start
    form.elements['end'].value = end
    }

var request_projects = new XMLHttpRequest();
request_projects.open('GET', 'http://localhost:5000/get_projects');
request_projects.onload = function() {
    var projectList = JSON.parse(request_projects.responseText);
    createProjectTable(projectList);
    updateInactiveProjects();
    }
request_projects.send();


