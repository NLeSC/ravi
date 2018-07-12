/**
 * An assignment is an object with the following properties:
 *
 * Assignment {
 *   aid    : assignemnt ID
 *   eid    : engineer ID (name + first letter of last name)
 *   pid    : project ID (human understandable abbreviation)
 *   fte    : FTE (float in [0,1])
 *   start  : start date (integer, YYYY-MM)
 *   end    : end data (integer, YYYY-MM)
 * }
 */

/**
 * Add assignments to the projects and engineers timelines
 *
 * arguments:
 *    assignments: Array[assignment]
 *
 * uses the following global variables:
 *    allAssignments
 */
function initializeAssignments (assignments) {
  // assignmenents: Array[assignment]
  assignments.forEach(function (assignment) {
    // sanitize data
    var d;
    var start = assignment.start || '2015-01';
    var end = assignment.end || '2050-01';

    d = new Date(start);
    if (d.getMonth() < 9) {
      start = d.getFullYear() + '-0' + (d.getMonth() + 1);
    } else {
      start = d.getFullYear() + '-' + (d.getMonth() + 1);
    }

    d = new Date(end);
    if (d.getMonth() < 9) {
      end = d.getFullYear() + '-0' + (d.getMonth() + 1);
    } else {
      end = d.getFullYear() + '-' + (d.getMonth() + 1);
    }

    engineerTLItems.update({
      id: assignment.aid,
      group: assignment.eid,
      start: start,
      end: end,
      content: assignment.fte + ' FTE: ' + assignment.pid,
      editable: itemEditableOptions
    });

    projectTLItems.update({
      id: assignment.aid,
      group: assignment.pid,
      start: start,
      end: end,
      content: assignment.fte + ' FTE: ' + assignment.eid,
      editable: itemEditableOptions
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
function sendAssignmentToServer (assignment) {
  form = new FormData()
  form.append('aid', assignment.aid || '');
  form.append('eid', assignment.eid || '');
  form.append('pid', assignment.pid || '');
  form.append('fte', assignment.fte || '');
  form.append('start', assignment.start || '');
  form.append('end', assignment.end || '');
  console.log(form);

  fetch('http://localhost:5000/update_assignment', {
    method: 'POST',
    body: form
  })
  .catch(function (error) {
    alert('Cannot update assignment at server');
    console.error(error);
  });
}

/**
 * Delete an assignment at the server
 *
 * arguments:
 *    assignmentID : typically assignment.aid
 */
function sendDeleteAssignmentToServer (assignmentID) {

  form = new FormData();
  form.append('aid', assignmentID);

  fetch('http://localhost:5000/del_assignment', {
    method: 'POST',
    body: form
  })
  .catch(function (error) {
    alert('Cannot delete assignment from server');
    console.error(error);
  });
}

/**
 * Create a new assignment at the server.
 *
 * Note that the caller should take care to update its list of assignments
 * by a call to sendRequestForAssignmentsToServer() later.
 *
 * arguments:
 *    assignment  : assignemnt object
 */
function sendCreateAssignmentToServer (assignment) {
  form = new FormData()
  form.append('eid', assignment.eid || '');
  form.append('pid', assignment.pid || '');
  form.append('fte', assignment.fte || '');
  form.append('start', assignment.start || '');
  form.append('end', assignment.end || '');

  fetch('http://localhost:5000/add_assignment', {
    method: 'POST',
    body: form
  }).then(function (response) {
    return response.json();
  }).then(function (assignment) {
    assignment.id = assignment.aid
    allAssignments.update(assignment);
    resetViews();
  })
  .catch(function (error) {
    alert('Cannot create assignment at server');
    console.error(error);
  });
}

/**
 * Send a request for (a subset of) assignments to the server.
 *
 * arguments:
 *    eid : Optional, engineer ID; only request assignments for this engineer
 *    pid : Optional, project ID; only request assignments for this project
 */
function sendRequestForAssignmentsToServer (eid, pid) {

  form = new FormData()
  form.append('eid', eid || '');
  form.append('pid', pid || '');

  return fetch('http://localhost:5000/get_assignments', {
    method: 'POST',
    body: form
  })
  .then(function (response) {
    return response.json();
  })
  .then(function (data) {
    initializeAssignments(data);
  })
  .catch(function (error) {
    alert('Cannot get assignments from server');
    console.error(error);
  });
}
