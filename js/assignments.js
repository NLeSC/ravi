function updateAssignments() {
    clearAssignmentTable()
    eid = document.getElementById("assignment_eid").value
    pid = document.getElementById("assignment_pid").value
    request_assignments = new XMLHttpRequest()
    request_assignments.open('POST', 'http://localhost:5000/get_assignments')
    request_assignments.onload = function() {
        var assignments = JSON.parse(request_assignments.responseText)
        fillAssignmentTable(assignments)
        }
    request_assignments.setRequestHeader("Content-type", "application/x-www-form-urlencoded")
    request_assignments.send('eid=' + eid + '&pid=' + pid)    
    }

function fillAssignmentTable(assignments) {
    var assignmentTable = document.getElementById('assignment_table')
    for(i=0; i<assignments.length; i++){
        a = assignments[i]
        var newrow = assignmentTable.insertRow(i+2)
        var c1 = newrow.insertCell(0)
        c1.innerHTML = a.eid
        var c2 = newrow.insertCell(1)
        c2.innerHTML = a.pid
        var c3 = newrow.insertCell(2)
        c3.innerHTML = a.fte
        var c4 = newrow.insertCell(3)
        c4.innerHTML = a.start
        var c5 = newrow.insertCell(4)
        c5.innerHTML = a.end
        var c6 = newrow.insertCell(5)
        c6.innerHTML = '<input type="button" name="button" value="Change" onClick="delAssignment('+a.aid+');">'
        }
    }

function clearAssignmentTable() {
    var assignmentTable = document.getElementById('assignment_table')
    table_length = assignment_table.rows.length
    for(i=table_length-1; i>1; i--) {
        assignmentTable.deleteRow(i)
        }
    }

function addAssignment(data) {
    form = document.getElementById('assignmentsform')
    assignment_data = {
        "eid": form.elements["eid"].value,
        "pid": form.elements["pid"].value,
        "fte": form.elements["fte"].value,
        "start": form.elements["start"].value,
        "end": form.elements["end"].value
        }
    console.log(assignment_data)
    request_add_assignment = new XMLHttpRequest()
    request_add_assignment.open('POST', 'http://localhost:5000/add_assignment')
    request_add_assignment.onload = function() {
        updateAssignments()
        engineers[assignment_data['eid']].plot()
        projects[assignment_data['pid']].plot()
        }
    request_add_assignment.setRequestHeader("Content-type", "application/x-www-form-urlencoded")
    request_add_assignment.send('data=' + JSON.stringify(assignment_data))    
    }

function delAssignment(aid) {
    request_del_assignment = new XMLHttpRequest()
    request_del_assignment.open('POST', 'http://localhost:5000/del_assignment')
    request_del_assignment.onload = function() {
        var assignment = JSON.parse(request_del_assignment.responseText)
        updateAssignments()
        engineers[assignment.eid].plot()
        projects[assignment.pid].plot()
        form = document.getElementById('assignmentsform')
        form.elements["eid"].value = assignment.eid
        form.elements["pid"].value = assignment.pid
        form.elements["fte"].value = assignment.fte
        form.elements["start"].value = assignment.start
        form.elements["end"].value = assignment.end
        }
    request_del_assignment.setRequestHeader("Content-type", "application/x-www-form-urlencoded")
    request_del_assignment.send('aid=' + aid)    
    }

updateAssignments()

