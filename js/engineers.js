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
    var start = engineers.start || '2015-01';
    var end = engineers.end || '2050-01';

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

    allEngineers.update({
      id: engineer.eid,
      eid: engineer.eid,
      content: engineer.eid,

      active: engineer.active,
      comments: engineer.comments,
      coordinator: engineer.coordinator,
      start: engineer.start,
      end: engineer.end,
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


  // add to the modal pop up on the project timeline
  inputBox = $('#inputEngineer');
  filterBox = $('#inputEngineerOptions');

  inputBox.empty();
  filterBox.empty();

  $('<option />', { value: 'all', text: 'All' }).appendTo(filterBox);

  allEngineers.forEach(function(engineer) {
    $('<option />', { value: engineer.id, text: engineer.content }).appendTo(inputBox);
    $('<option />', { value: engineer.id, text: engineer.content }).appendTo(filterBox);
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
  fetch('http://localhost:5000/get_engineers')
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
 * Send a request for engineer load to the server.
 *
 * The response is parsed, and the allLoads global variable is update()-ed
 * via a call to initializeEngineerLoads()
 *
 */
function sendRequestForEngineerLoadsToServer (eid, pid) {
  fetch('http://localhost:5000/get_engineer_load')
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

sendRequestForEngineersToServer();
sendRequestForEngineerLoadsToServer();
