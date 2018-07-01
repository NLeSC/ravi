var datasetOptions = {};

// The full assignments containing all information necessary to
// sync with the server
var fullAssignments = new vis.DataSet(datasetOptions);

// Datasets bound to the timelines:
//  * for the engineer timeline
var engineerAssignments = new vis.DataSet(datasetOptions);
var engineerGroups = new vis.DataSet(datasetOptions);

// * for the project timeline
var projectAssignments = new vis.DataSet(datasetOptions);
var projectGroups = new vis.DataSet(datasetOptions);

// current (selected) assignments; they should point to the same assignment,
// but on the two different views
var currentPA; // on the project timeline
var currentEA; // on the engineer timeline
var currentFA; // the corresponding full assignment

// Configuration for the Timeline
var d = new Date();
var year = d.getFullYear();
var month = d.getMonth();
var day = d.getDate();
var timelineOptions = {
  height: '120%',
  verticalScroll: true,
  start: new Date(year - 1, month, day),
  end: new Date(year + 1, month, day),
  zoomMin: 15768000000, // Half a year
  zoomMax: 157680000000, // 5 years
  editable: {
    add: true,         // add new items by double tapping
    updateTime: true,  // drag items horizontally
    updateGroup: false, // drag items from one group to another
    remove: true,       // delete an item by tapping the delete button top right
    overrideItems: true // allow these options to override item.editable
  },
  type: 'range',
  template: function (item, element, data) {
    var html = "<div>" + item.content + "</div>";
    return html;
  },
  // individual item events
  // these have to be passed to the options object on construction of the timeline
  onRemove: function (item, callback) {
    engineerAssignments.remove(item);
    projectAssignments.remove(item);
    fullAssignments.remove(item);

    delAssignment(item);
    callback(null); // we already removed the assignment ourselves, so block any further action
  },
  onMove: function (item, callback) {
    var aid = item.id;

    currentFA = fullAssignments.get(aid);
    currentEA = engineerAssignments.get(aid);
    currentPA = projectAssignments.get(aid);

    currentFA.start = item.start.getFullYear() + '-' + (item.start.getMonth() + 1);
    currentFA.end = item.end.getFullYear() + '-' + (item.end.getMonth() + 1);
    applyFullAssignmentUpdate();
    sendAssignmentToServer(currentFA);

    // just to be sure the visjs framework sets the same value
    // as the one we set above (ie. a year-month string, not a Date object)
    item.start = currentFA.start;
    item.end = currentFA.end;
    callback(item);
  }
};
timelineOptions.onUpdate = timelineOptions.onMove;

function applyFullAssignmentUpdate () {
  // after entering new values for the assignment in the dialogs,
  // and after having updated the currentFA,  we now need to
  // update the three DataSet instance (which will also update the timeline plots)
  currentPA.content = currentFA.fte + ' FTE: ' + currentFA.eid;
  currentPA.fte = currentFA.fte;
  currentPA.group = currentFA.pid;
  currentPA.start = currentFA.start;
  currentPA.end = currentFA.end;

  currentEA.content = currentFA.fte + ' FTE: ' + currentFA.pid;
  currentEA.fte = currentFA.fte;
  currentEA.group = currentFA.eid;
  currentEA.start = currentFA.start;
  currentEA.end = currentFA.end;

  fullAssignments.update(currentFA);
  engineerAssignments.update(currentEA);
  projectAssignments.update(currentPA);
};

// Projects Timeline
// ------------------
var projectsContainer = document.getElementById('visjs-projects-container');
var projectsTimeline = new vis.Timeline(projectsContainer, projectAssignments, projectGroups, timelineOptions);

projectsTimeline.on('contextmenu', function (properties) {
  properties.event.preventDefault(); // prevent default browser pop-up menu

  currentPA = projectAssignments.get(properties.item);
  currentEA = engineerAssignments.get(properties.item);
  currentFA = fullAssignments.get(properties.item);
  if (! properties.item || ! currentPA || ! currentEA || ! currentFA || currentPA.id != currentEA.id) {
    // double clicked somewhere else (not on an assignment)
    return;
  }

  // pre-select the right engineer in the dropdown
  $('#inputProjectsTimelineEngineer').val(currentFA.eid);

  // enter the FTE in the input field
  $('#inputProjectsTimelineFTE').val(currentFA.fte);

  // start the model dialog continue; processing on #inputProjectsTimelineApply.on('click')
  $('#projectAssignmentModal').modal();
});

// update the full assignment with values from the modal dialog
$('#inputProjectsTimelineApply').on('click', function () {
  currentFA.eid = $('#inputProjectsTimelineEngineer').val();
  currentFA.fte = $('#inputProjectsTimelineFTE').val();

  applyFullAssignmentUpdate ();
  sendAssignmentToServer(currentFA);
  $('#projectAssignmentModal').modal('hide');
});

// Engineers Timeline
// ------------------
var engineersContainer = document.getElementById('visjs-engineers-container');
var engineersTimeline = new vis.Timeline(engineersContainer, engineerAssignments, engineerGroups, timelineOptions);

engineersTimeline.on('contextmenu', function (properties) {
  properties.event.preventDefault(); // prevent default browser pop-up menu

  currentPA = projectAssignments.get(properties.item);
  currentEA = engineerAssignments.get(properties.item);
  currentFA = fullAssignments.get(properties.item);
  if (! properties.item || ! currentPA || ! currentEA || ! currentFA || currentPA.id != currentEA.id) {
    // double clicked somewhere else (not on an assignment)
    return;
  }

  // pre-select the right project in the dropdown
  $('#inputEngineersTimelineProject').val(currentFA.pid);

  // enter the FTE in the input field
  $('#inputEngineersTimelineFTE').val(currentFA.fte);

  // start the model dialog continue processing on #inputEngineersTimelineApply.on('click')
  $('#engineerAssignmentModal').modal();
});

// update the full assignment with values from the modal dialog
$('#inputEngineersTimelineApply').on('click', function () {
  currentFA.pid = $('#inputEngineersTimelineProject').val();
  currentFA.fte = $('#inputEngineersTimelineFTE').val();

  applyFullAssignmentUpdate ();
  sendAssignmentToServer(currentFA);
  $('#engineerAssignmentModal').modal('hide');
});

// Link the Engineers and Project timelines
// ----------------------------------------

// automatically select the assignments on the other timeline
engineersTimeline.on('select', function (properties) {
  projectsTimeline.setSelection(properties.items);
  projectsTimeline.focus(properties.items);

  var firstSelectedAssignment = fullAssignments.get(properties.items[0]);
  if (firstSelectedAssignment) {
    selectEngineer(firstSelectedAssignment.eid);
    selectProject(firstSelectedAssignment.pid);
  }
});

projectsTimeline.on('select', function (properties) {
  engineersTimeline.setSelection(properties.items);
  engineersTimeline.focus(properties.items);

  var firstSelectedAssignment = fullAssignments.get(properties.items[0]);
  if (firstSelectedAssignment) {
    selectEngineer(firstSelectedAssignment.eid);
    selectProject(firstSelectedAssignment.pid);
  }
});
