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
  zoomMin: 15768000000,  // Half a year
  zoomMax: 157680000000, // 5 years
  editable: {
    add: true,           // add new items by double tapping
    updateTime: true,    // drag items horizontally
    updateGroup: false,  // drag items from one group to another
    remove: true,        // delete an item by tapping the delete button top right
    overrideItems: false // allow these options to override item.editable
  },
  groupEditable: true,
  type: 'range',
  template: function (item, element, data) {
    var html = "<div>" + item.content + "</div>";
    return html;
  },
  groupTemplate: function (item, element) {
    var html = "<div>" + item.content + "</div>";
    return html;
  },
  groupOrder: 'id',
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

    var currentFA = fullAssignments.get(aid);
    var currentEA = engineerAssignments.get(aid);
    var currentPA = projectAssignments.get(aid);

    currentFA.start = item.start.getFullYear() + '-' + (item.start.getMonth() + 1);
    currentFA.end = item.end.getFullYear() + '-' + (item.end.getMonth() + 1);
    applyFullAssignmentUpdate(currentFA);
    sendAssignmentToServer(currentFA);

    // just to be sure the visjs framework sets the same value
    // as the one we set above (ie. a year-month string, not a Date object)
    item.start = currentFA.start;
    item.end = currentFA.end;
    callback(item);
  },
  onAdd: function (item, callback) {
    var currentFA = {
      start : item.start.getFullYear() + '-' + item.start.getMonth(),
      end : item.end.getFullYear() + '-' + item.end.getMonth(),
      fte : 0.5,
      aid : 5000, // FIXME
    }
    currentFA.id = currentFA.aid;

    if (engineerGroups.get(item.group)) {
      // adding on engineers timeline, the group is the engineer
      currentFA.eid = item.group;
      currentFA.pid = projectGroups.get()[0].id;
      applyFullAssignmentUpdate(currentFA);
    } else if (projectGroups.get(item.group)) {
      // adding on projects timeline, the group is the project
      currentFA.eid = engineerGroups.get()[0].id;
      currentFA.pid = item.group;
      applyFullAssignmentUpdate(currentFA);
    }

    // high-light the added assignment and zoom to it
    engineersTimeline.setSelection([currentFA.id]);
    engineersTimeline.focus([currentFA.id]);

    projectsTimeline.setSelection([currentFA.id]);
    projectsTimeline.focus([currentFA.id]);

    callback(null);
  }
};
timelineOptions.onUpdate = timelineOptions.onMove;

/**
 * apply changes to a full assignment
 *
 * after entering new values for the assignment in the dialogs,
 * and after having updated the currentFA,  we now need to
 * update the three DataSet instance (which will also update the timeline plots)
 *
 * arguments:
 *    currentFA  full assignment object to sync to the DataSets
 */
function applyFullAssignmentUpdate (currentFA) {
  var currentPA = {};
  currentPA.content = currentFA.fte + ' FTE: ' + currentFA.eid;
  currentPA.fte = currentFA.fte;
  currentPA.group = currentFA.pid;
  currentPA.start = currentFA.start;
  currentPA.end = currentFA.end;
  currentPA.id = currentFA.aid;

  var currentEA = {};
  currentEA.content = currentFA.fte + ' FTE: ' + currentFA.pid;
  currentEA.fte = currentFA.fte;
  currentEA.group = currentFA.eid;
  currentEA.start = currentFA.start;
  currentEA.end = currentFA.end;
  currentEA.id = currentFA.aid;

  fullAssignments.update(currentFA);
  engineerAssignments.update(currentEA);
  projectAssignments.update(currentPA);
};

// Projects and Engineers Timelines
// --------------------------------
var projectsContainer = document.getElementById('visjs-projects-container');
var projectsTimeline = new vis.Timeline(projectsContainer, projectAssignments, projectGroups, timelineOptions);

var engineersContainer = document.getElementById('visjs-engineers-container');
var engineersTimeline = new vis.Timeline(engineersContainer, engineerAssignments, engineerGroups, timelineOptions);

// map contextmenu (ie. right mouse button)
// to open a modal window to update assignments
function openAssignmentModal (properties) {
  properties.event.preventDefault(); // prevent default browser pop-up menu

  var currentFA = fullAssignments.get(properties.item);
  if (! properties.item || ! currentFA) {
    // double clicked somewhere else (not on an assignment)
    return;
  }

  // set the assignemnt id in the title
  $('#inputAid').text(currentFA.aid);

  // pre-select the right engineer in the dropdown
  $('#inputEngineer').val(currentFA.eid);

  // pre-select the right project in the dropdown
  $('#inputProject').val(currentFA.pid);

  // enter the FTE in the input field
  $('#inputFTE').val(currentFA.fte);

  // enter the start and end in the input fields
  $('#inputStart').val(currentFA.start);
  $('#inputEnd').val(currentFA.end);

  // start the model dialog continue processing on #assignmentUpdateApply.on('click')
  $('#assignmentModal').modal();
}

// update the assignment when the user clicks on the 'Apply changes' button
$('#assignmentUpdateApply').on('click', function () {
  var assignment = {
    aid : $('#inputAid').text(), // a span, not an input
    eid : $('#inputEngineer').val(),
    pid : $('#inputProject').val(),
    fte : $('#inputFTE').val(),
    start : $('#inputStart').val(),
    end : $('#inputEnd').val()
  };
  assignment.id = assignment.aid; // re-use the aid as DataSet id

  applyFullAssignmentUpdate(assignment);
  sendAssignmentToServer(assignment);
  $('#assignmentModal').modal('hide');

  // high-light the updated assignment and zoom to it
  engineersTimeline.setSelection([assignment.id]);
  engineersTimeline.focus([assignment.id]);

  projectsTimeline.setSelection([assignment.id]);
  projectsTimeline.focus([assignment.id]);

});

engineersTimeline.on('contextmenu', openAssignmentModal);
projectsTimeline.on('contextmenu', openAssignmentModal);

// Link the Engineers and Project timelines
// ----------------------------------------

// automatically select the assignments on the other timeline
engineersTimeline.on('select', function (properties) {
  if (! properties || ! properties.items) {
    return;
  }
  var firstSelectedAssignment = fullAssignments.get(properties.items[0]);

  if (properties.items[0] && firstSelectedAssignment) {
    projectsTimeline.setSelection([firstSelectedAssignment.id]);
    projectsTimeline.focus([firstSelectedAssignment.id]);

    selectEngineer(firstSelectedAssignment.eid);
    selectProject(firstSelectedAssignment.pid);
  }
});

projectsTimeline.on('select', function (properties) {
  if (! properties || ! properties.items) {
    return;
  }
  var firstSelectedAssignment = fullAssignments.get(properties.items[0]);


  if (properties.items[0] && firstSelectedAssignment) {
    engineersTimeline.setSelection([firstSelectedAssignment.id]);
    engineersTimeline.focus([firstSelectedAssignment.id]);

    selectEngineer(firstSelectedAssignment.eid);
    selectProject(firstSelectedAssignment.pid);
  }
});

// Hash containing all filterable properties
// Apply filtering using the 'applyFilterSettings' function below
var filterSettings = {
  'projects': 'all', // all, active, inactive
};

/**
 * Apply the filtering described in the filterSettings on the following:
 *   - engineerAssignments
 *   - projectAssignments
 *   - projects
 * As the timelines are bound to the DataSet, updating the views is automatic
 *
 * uses global args:
 *   filterSettings, fullAssignments
 *
 * datasets filtered:
 *   engineerAssignments, projectAssignments
 */
function applyFilterSettings () {
  // projects are groups on the timeline and have
  // a boolean 'visibile'
  // This also hides the item for the duration (type 'background', in green)
  projectGroups.forEach(function (project) {
    project.visible = false;

    if (
      filterSettings.project == 'all' ||
      filterSettings.project == 'active' && project.active == true ||
      filterSettings.project == 'inactive' && project.active == false) {
      project.visible = true;
    }
    projectGroups.update(project);
  });

  // assignments are items on a timeline, that cannot be individually hidden/shown
  // so actually remove or add them where necessary
  // however, project assignments are hidden with their project (ie. group) so skip them for now
  var addEAs = [];
  // var addPAs = [];
  var removeAid = [];
  fullAssignments.forEach(function (assignment) {
    var show = false;
    var project = projectGroups.get(assignment.pid);
    var egineer = engineerGroups.get(assignment.eid);

    if (
      filterSettings.project == 'all' ||
      filterSettings.project == 'active' && project.active == true ||
      filterSettings.project == 'inactive' && project.active == false) {
      show = true;
    }

    if (show) {
      addEAs.push({
        id: assignment.aid,
        group: assignment.eid,
        start: assignment.start,
        end: assignment.end,
        content: assignment.fte + ' FTE: ' + assignment.pid,
        editable: true
      });

      // addPAs.push({
      //   id: assignment.aid,
      //   group: assignment.pid,
      //   start: assignment.start,
      //   end: assignment.end,
      //   content: assignment.fte + ' FTE: ' + assignment.eid,
      //   editable: true
      // });
    } else {
      removeAid.push(assignment.id);
    }

  });

  engineerAssignments.remove(removeAid);
  engineerAssignments.update(addEAs);

  // projectAssignments.remove(removeAid);
  // projectAssignments.update(addPAs);
}

$('#inputWindowOptions').on('change', function () {
  var option = $('#inputWindowOptions').val();

  var projTL = $('#visjs-projects-container');
  var engTL = $('#visjs-engineers-container');

  if (option == 'eng_and_proj') {
    projTL.removeClass('w-100');
    projTL.addClass('w-50');
    projTL.show();

    engTL.removeClass('w-100');
    engTL.addClass('w-50');
    engTL.show();
  } else if (option == 'eng') {
    engTL.removeClass('w-50');
    engTL.addClass('w-100');
    engTL.show();

    projTL.hide();
  } else if (option == 'proj') {
    projTL.removeClass('w-50');
    projTL.addClass('w-100');
    projTL.show();

    engTL.hide();
  } else if (option == 'eng_sum') {
    projTL.removeClass('w-100');
    projTL.addClass('w-50');
    projTL.show();

    engTL.removeClass('w-100');
    engTL.addClass('w-50');
    engTL.show();
  } else if (option == 'proj_sum') {
    projTL.removeClass('w-100');
    projTL.addClass('w-50');
    projTL.show();

    engTL.removeClass('w-100');
    engTL.addClass('w-50');
    engTL.show();
  }
});

$('#inputProjectOptions').on('change', function () {
  filterSettings.project = $('#inputProjectOptions').val();
  applyFilterSettings();
});

$('#inputSortOptions').on('change', function () {
  var sort = $('#inputSortOptions').val();

  engineersTimeline.setOptions({groupOrder: 'id'});

  if (sort == 'name') {
    projectsTimeline.setOptions({groupOrder: 'id'});
  } else if (sort == 'start') {
    projectsTimeline.setOptions({groupOrder: 'start'});
  } else if (sort == 'end') {
    projectsTimeline.setOptions({groupOrder: 'end'});
  }
});
