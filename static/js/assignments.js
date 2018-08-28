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
  assignments.forEach(function (assignment) {
    allAssignments.update({
      id: assignment.aid, // re-use the assignment id as DataSet id
      aid: assignment.aid,
      eid: assignment.eid,
      pid: assignment.pid,
      start: assignment.start || '2000-01-01',
      end: assignment.end || '2100-01-01',
      fte: assignment.fte
    });
  });
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

  fetch('/update_assignment', {
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

  fetch('/del_assignment', {
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

  fetch('/add_assignment', {
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
  var myRequest = new Request('/get_assignments', {
    method: 'POST',
    body: JSON.stringify({
      eid: eid || 'all',
      pid: pid || 'all'
    })
  });

  return fetch(myRequest)
  .then(function (response) {
    console.log(response);
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
