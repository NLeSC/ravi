/**
 * Add assignments to the projects and engineers timelines
 *
 * An assignment is an object with the following properties:
 * Assignment {
 *   aid    : assignemnt ID
 *   eid    : engineer ID (name + first letter of last name)
 *   pid    : project ID (human understandable abbreviation)
 *   fte    : FTE (float in [0,1])
 *   start  : start date (integer, YYYY-MM)
 *   end    : end data (integer, YYYY-MM)
 * }
 *
 * arguments:
 *    assignments: Array[assignment]
 *
 * uses the following global variables:
 *    engineerTLItems, projectTLItems
 */
function initializeAssignments (assignments) {
  // assignmenents: Array[assignment]
  assignments.forEach(function (assignment) {
    // sanitize data
    var start = assignment.start || '2015-01';
    var end = assignment.end || '2050-01';

    engineerTLItems.update({
      id: assignment.aid,
      group: assignment.eid,
      start: start,
      end: end,
      content: assignment.fte + ' FTE: ' + assignment.pid,
      editable: true
    });

    projectTLItems.update({
      id: assignment.aid,
      group: assignment.pid,
      start: start,
      end: end,
      content: assignment.fte + ' FTE: ' + assignment.eid,
      editable: true
    });

    allAssignments.update({
      id: assignment.aid, // re-use the assignment id as DataSet id
      aid: assignment.aid,
      eid: assignment.eid,
      pid: assignment.pid,
      start: start,
      end: end,
      fte: assignment.fte
    });
  });

  // remove dummy assignment (issue with empty plots)
  allProjects.remove(1);
  engineerTLItems.remove(1);
  projectTLItems.remove(1);
}

/**
 * Send a full assignment object to the server
 *
 * arguments:
 *    assignment
 */
function sendAssignmentToServer(assignment) {
  req = new XMLHttpRequest()
  req.open('POST', 'http://localhost:5000/update_assignment')
  req.setRequestHeader("Content-type", "application/x-www-form-urlencoded")
  req.send('data=' + JSON.stringify({
    aid: assignment.aid,
    eid: assignment.eid,
    pid: assignment.pid,
    fte: assignment.fte,
    start: assignment.start,
    end: assignment.end
  }));
}

function updateAssignments() {
    // clearAssignmentTable()
    // var eid = document.getElementById("assignment_eid").value
    // var pid = document.getElementById("assignment_pid").value
    var eid = ""
    var pid = ""
    request_assignments = new XMLHttpRequest()
    request_assignments.open('POST', 'http://localhost:5000/get_assignments')
    request_assignments.onload = function() {
        var assignments = JSON.parse(request_assignments.responseText)
        initializeAssignments(assignments);
        // fillAssignmentTable(assignments)
        }
    request_assignments.setRequestHeader("Content-type", "application/x-www-form-urlencoded")
    request_assignments.send('eid=' + eid + '&pid=' + pid)    
    }

function fillAssignmentTable(assignments) {
    var assignmentTable = document.getElementById('assignment_table')
    for(i=0; i<assignments.length; i++){
        a = assignments[i]
        var newrow = assignmentTable.insertRow(i)
        var c1 = newrow.insertCell(0)
        c1.innerHTML = '<input type="button" value="' + a.eid + '" onClick="selectEngineer(\'' + a.eid + '\');scrollToEngineer();">'
        var c2 = newrow.insertCell(1)
        c2.innerHTML = '<input type="button" value="' + a.pid + '" onClick="selectProject(\'' + a.pid + '\');scrollToProject();">'
        var c3 = newrow.insertCell(2)
        c3.innerHTML = a.fte
        var c4 = newrow.insertCell(3)
        c4.innerHTML = a.start
        var c5 = newrow.insertCell(4)
        c5.innerHTML = a.end
        var c6 = newrow.insertCell(5)
        c6.innerHTML = '<span title="This deletes the assignment, allowing to make changes and to add it back to the list.">' +
                       '<input type="button" name="button" value="Change" onClick="delAssignment('+a.aid+');">' +
                       '</span>'
        }
    }

function clearAssignmentTable() {
    var assignmentTable = document.getElementById('assignment_table')
    table_length = assignment_table.rows.length
    for(i=table_length-1; i>=0; i--) {
        assignmentTable.deleteRow(i)
        }
    }

function resetAssignmentForm() {
    var aform = document.getElementById('assignmentsform')
    aform.elements['eid'].value = document.getElementById('engineer_name').value
    aform.elements['pid'].value = document.getElementById('project_name').value
    aform.elements['fte'].value = ''
    aform.elements['start'].value = document.getElementById('project_start').value
    aform.elements['end'].value = document.getElementById('project_end').value
    }

function checkResponse(request_object) {
    if (request_object.readyState == 4 && request_object.status == 200) {
        return true
        }
    else {
        alert(JSON.parse(request_object.responseText)['error'])
        return false
        }
    }

function addAssignment(data) {
    var form = document.getElementById('assignmentsform')
    assignment_data = {
        "eid": form.elements["eid"].value,
        "pid": form.elements["pid"].value,
        "fte": form.elements["fte"].value,
        "start": form.elements["start"].value,
        "end": form.elements["end"].value
        }
    request_add_assignment = new XMLHttpRequest()
    request_add_assignment.open('POST', 'http://localhost:5000/add_assignment')
    request_add_assignment.onload = function() {
        if (checkResponse(request_add_assignment)) {
            resetAssignmentForm()
            updateAssignments()
            engineers[assignment_data['eid']].plot()
            projects[assignment_data['pid']].plot()
            plotProject()
            }
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
        plotProject()
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

function plotTotalAssignments() {
    var request = new XMLHttpRequest();
    request.open('GET', 'http://localhost:5000/get_total_assignments_plot');
    request.onload = function() {
        plotDetails(JSON.parse(request.responseText), 'Total assignments', 0.05, 'left', true);
        }
    request.send();
    }

updateAssignments()

