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
 *    allEengineers
 */

var engineers = {}

function initializeEngineers (engineers) {
  engineers.forEach(function(engineer) {

    // sanitize data
    var d;
    var start = engineer.start || '2015-01';
    var end = engineer.end || '2050-01';

    allEngineers.update({
      id: engineer.eid,
      eid: engineer.eid,
      content: engineer.eid,
      assigned: engineer.assigned,
      balance: engineer.assigned - engineer.available,

      active: engineer.active,
      comments: engineer.comments,
      coordinator: engineer.coordinator,
      start: start,
      end: end,
      sortStart: "" + start,
      sortEnd: "" + end,
      exact_id: engineer.exact_id,
      fte: engineer.fte
    });

    // TODO: Linemanagers not yet filled-in in database
    if (engineer.coordinator) {
      allLinemanagers.update({
       id: engineer.coordinator
     });
    }
  });

  // Add engineers to the filter box, subdivide by active / inactive
  filterBox = $('#inputEngineerOptions');
  filterBox.empty();
  $('<option />', { value: 'all', text: 'All' }).appendTo(filterBox);
  var activeList = $('<optgroup>', { label: 'Active' }).appendTo(filterBox);
  var inactiveList = $('<optgroup>', { label: 'Inactive' }).appendTo(filterBox);

  allEngineers.forEach(function(engineer) {
    if (engineer.active) {
      $('<option />', { value: engineer.id, text: engineer.eid }).appendTo(activeList);
    } else {
      $('<option />', { value: engineer.id, text: engineer.eid }).appendTo(inactiveList);
    }
  });

  // Add engineers to the input box
  inputBox = $('#inputEngineer');
  inputBox.empty();
  allEngineers.forEach(function(engineer) {
    $('<option />', { value: engineer.id, text: engineer.eid }).appendTo(inputBox);
  });

  inputBox = $('#inputLinemanager');
  filterBox = $('#inputLinemanagerOptions');

  inputBox.empty();
  filterBox.empty();

  $('<option />', { value: 'all', text: 'All' }).appendTo(filterBox);

  allLinemanagers.forEach(function (linemanager) {
    $('<option />', { value: linemanager.id, text: linemanager.id, }).appendTo(inputBox);
    $('<option />', { value: linemanager.id, text: linemanager.id, }).appendTo(filterBox);
  });
}

/**
 * Parse the server response to get_engineer_load
 * Store the data in the global allLoads variable
 */
function initializeEngineerLoads (loads) {
  allLoads.clear();
  loads.forEach(function (load) {
    // sanitize data
    var d;
    var start = load.start || '2015-01';
    var end = load.end || '2050-01';

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

    allLoads.update({
      eid: load.eid,
      start: load.start,
      end: load.end,
      fte: load.fte
    });
  });
}

/**
 * Send a request for engineers to the server.
 *
 * The response is parsed, and the allEngineers global variable is update()-ed
 * via a call to initializeEngineers()
 *
 */
function sendRequestForEngineersToServer () {
  return fetch('/get_engineers')
  .then(function (response) {
    return response.json();
  })
  .then(function (data) {
    initializeEngineers(data);
  })
  .catch(function (error) {
    alert('Cannot get engineers from server');
    console.error(error);
  });
}

/**
 * Send an engineer object to the server
 *
 * arguments:
 *    engineer
 */
function sendEngineerToServer (engineer) {
  form = new FormData()
  form.append('eid', engineer.eid || '');
  form.append('fte', engineer.fte || '');
  form.append('start', engineer.start || '');
  form.append('end', engineer.end || '');
  form.append('active', engineer.active ? 1 : 0);
  form.append('coordinator', engineer.coordinator || '');

  fetch('/update_engineer', {
    method: 'POST',
    body: form
  })
  .catch(function (error) {
    alert('Cannot update engineer at server');
    console.error(error);
  });
}

/**
 * Send a request for engineer load to the server.
 *
 * The response is parsed, and the allLoads global variable is update()-ed
 * via a call to initializeEngineerLoads()
 *
 */
function sendRequestForEngineerLoadsToServer (eid, pid) {
  return fetch('/get_engineer_load')
  .then(function (response) {
    return response.json();
  })
  .then(function (data) {
    initializeEngineerLoads(data);
  })
  .catch(function (error) {
    alert('Cannot get engineer load from server');
    console.error(error);
  });
}
