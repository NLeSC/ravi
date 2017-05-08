var projects = {}

function createProjectTable(projectList) {
    for(i=0; i<projectList.length; i++) {
        var p_data = projectList[i]
        addProjectTableRow(p_data.pid)
        p = new Project(p_data)
        p.plot()
        projects[p_data.pid] = p
        }
    }

function addProjectTableRow(pid) {
    var projectTable = document.getElementById('project_table')
    var newrow = projectTable.insertRow(0)
    var cell1 = newrow.insertCell(0)
    var cell2 = newrow.insertCell(1)
    newrow.id = pid
    cell1.style.width = "100px"
    cell1.innerHTML = pid
    cell2.id = "plot_" + pid
    document.getElementById(pid).addEventListener("click", selectProject)
    }

function Project(project_data) {
    this.pid = project_data.pid
    this.exact_id = project_data.exact_id
    this.start = project_data.start
    this.end = project_data.end
    this.fte = project_data.fte
    
    this.plot = function () {
        var projectPlot = document.getElementById("plot_" + this.pid)
        var request = new XMLHttpRequest();

        request.open('POST', 'http://localhost:5000/get_project_data');
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

            Plotly.newPlot(projectPlot, data, layout, {displayModeBar: false});
            }
        request.setRequestHeader("Content-type", "application/x-www-form-urlencoded")
        request.send('pid='+this.pid);
        }
    }

function plotProject() {
    var pid = document.getElementById('projectform').elements['name'].value
    var request = new XMLHttpRequest();
    request.open('POST', 'http://localhost:5000/get_project_plot');
    request.onload = function() {
        var data = JSON.parse(request.responseText)
        console.log(Plotly.d3.scale.category20())
        var plot_detailed = document.getElementById("plot_detailed")
        var layout = {
            autosize: true,
            height: 250,
            margin: {l:50,r:0,b:100,t:10},
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
    request.send('pid=' + pid);
    }


function selectProject() {
    project = projects[this.id]
    if (this.style.backgroundColor == "lavender") {
        clearProjectSelection()
        }
    else {
        document.getElementById("project_name").value = project.pid
        document.getElementById("project_fte").value = project.fte
        document.getElementById("project_start").value = project.start
        document.getElementById("project_end").value = project.end
        document.getElementById("project_exact").value = project.code
        document.getElementById("assignment_pid").value = project.pid
        document.getElementById("assignment_start").value = project.start
        document.getElementById("assignment_end").value = project.end
        unhighlightProjects()
        this.style.backgroundColor = "lavender"
        }
    updateAssignments()
    }

function clearProjectSelection() {
    document.getElementById("projectform").reset()
    document.getElementById("assignment_pid").value = ""
    document.getElementById("assignment_start").value = ""
    document.getElementById("assignment_end").value = ""
    unhighlightProjects()
    updateAssignments()
    }

function unhighlightProjects() {
    var tableRows = document.getElementById("project_table").getElementsByTagName("tr")
    for(r=0; r<tableRows.length; r++) {
        tableRows[r].style.backgroundColor = "white"
        }
    }

function addProject() {
    pid = document.getElementById("project_name").value
    fte = document.getElementById("project_fte").value
    start = document.getElementById("project_start").value
    end = document.getElementById("project_end").value
    exact = document.getElementById("project_exact").value
    project_data = {
        "pid": pid,
        "fte": fte,
        "start": start,
        "end": end,
        "exact": exact
        }
    if (!(pid in projects)) {
        addProjectTableRow(pid)
        }
    projects[pid] = new Project(project_data)

    request_add_project = new XMLHttpRequest()
    request_add_project.open('POST', 'http://localhost:5000/add_project')
    request_add_project.onload = function() {projects[pid].plot()}
    request_add_project.setRequestHeader("Content-type", "application/x-www-form-urlencoded")
    request_add_project.send('data=' + JSON.stringify(project_data))    
    }

function delProject() {
    pid = document.getElementById("project_name").value
    if (confirm("Do you want to remove project " + pid + " and all its assignments?") == true) {
        document.getElementById(pid).remove()
        request_del_project = new XMLHttpRequest()
        request_del_project.open('POST', 'http://localhost:5000/del_project')
        request_del_project.setRequestHeader("Content-type", "application/x-www-form-urlencoded")
        request_del_project.send('pid=' + pid)    
        }
    }

function printProjects()
{
    var print_window = window.open('', 'PRINT', 'height=600,width=1000')

    print_window.document.write('<html><head><title>' + document.title  + '</title>')
    print_window.document.write('</head><body><h1>Project planning</h1><div style="height:100%">')
    print_window.document.write(document.getElementById("projects").innerHTML)
    print_window.document.write('<table><tr><td style="width: 100px"></td><td>')
    print_window.document.write(document.getElementById("xLabels2").innerHTML)
    print_window.document.write('</td></tr></table></div><script src="js/plotly-latest.min.js"></script></body></html>')
    print_window.document.close(); // necessary for IE >= 10
    print_window.focus(); // necessary for IE >= 10*/
//    print_window.print();
//    print_window.close();

    return true;
}

var request_projects = new XMLHttpRequest();
request_projects.open('GET', 'http://localhost:5000/get_projects');
request_projects.onload = function() {
    var projectList = JSON.parse(request_projects.responseText);
    createProjectTable(projectList);
    }
request_projects.send();


