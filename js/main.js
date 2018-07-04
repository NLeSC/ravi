var datasetOptions = {};

// The full datasets, containing all information necessary to
// sync with the server
var allAssignments = new vis.DataSet(datasetOptions);
var allEngineers = new vis.DataSet(datasetOptions);
var allProjects = new vis.DataSet(datasetOptions);
var allLinemanagers = new vis.DataSet(datasetOptions);
var allCoordinators = new vis.DataSet(datasetOptions);

// Datasets bound to the timelines.
// These are filtered depending on filterSettings,
// and contain only the currently visible data

var engineerTLItems = new vis.DataSet(datasetOptions);
var projectTLItems = new vis.DataSet(datasetOptions);

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
    var html = '<div>' + item.content + '</div>';
    return html;
  },
  groupTemplate: function (item, element) {
    var html = '<div>' + item.content + '</div>';
    return html;
  },
  groupOrder: 'id',
  // individual item events
  // these have to be passed to the options object on construction of the timeline
  onRemove: function (item, callback) {
    engineerTLItems.remove(item);
    projectTLItems.remove(item);
    allAssignments.remove(item);

    delAssignment(item);
    callback(null); // we already removed the assignment ourselves, so block any further action
  },
  onMove: function (item, callback) {
    var aid = item.id;

    var assignment = allAssignments.get(aid);
    var engineerItem = engineerTLItems.get(aid);
    var projectItem = projectTLItems.get(aid);

    assignment.start = item.start.getFullYear() + '-' + (item.start.getMonth() + 1);
    assignment.end = item.end.getFullYear() + '-' + (item.end.getMonth() + 1);
    applyAssignmentUpdate(assignment);
    sendAssignmentToServer(assignment);

    // just to be sure the visjs framework sets the same value
    // as the one we set above (ie. a year-month string, not a Date object)
    item.start = assignment.start;
    item.end = assignment.end;
    callback(item);
  },
  onAdd: function (item, callback) {
    var assignment = {
      start : item.start.getFullYear() + '-' + (item.start.getMonth() + 1),
      end : item.end.getFullYear() + '-' + (item.end.getMonth() + 1),
      fte : 0.5,
      aid : 5000, // FIXME
    }
    assignment.id = assignment.aid;

    if (allEngineers.get(item.group)) {
      // adding on engineers timeline, the group is the engineer
      assignment.eid = item.group;
      assignment.pid = allProjects.get()[0].id;
      applyAssignmentUpdate(assignment);
    } else if (allProjects.get(item.group)) {
      // adding on projects timeline, the group is the project
      assignment.eid = allEngineers.get()[0].id;
      assignment.pid = item.group;
      applyAssignmentUpdate(assignment);
    }

    // high-light the added assignment and zoom to it
    engineersTimeline.setSelection([assignment.id]);
    engineersTimeline.focus([assignment.id]);

    projectsTimeline.setSelection([assignment.id]);
    projectsTimeline.focus([assignment.id]);

    callback(null);
  }
};
timelineOptions.onUpdate = timelineOptions.onMove;

/**
 * apply changes to a full assignment
 *
 * after entering new values for the assignment in the dialogs,
 * and after having updated the assignment,  we now need to
 * update the three DataSet instance (which will also update the timeline plots)
 *
 * arguments:
 *    assignment  full assignment object to sync to the DataSets
 */
function applyAssignmentUpdate (assignment) {
  var projectItem = {};
  projectItem.content = assignment.fte + ' FTE: ' + assignment.eid;
  projectItem.fte = assignment.fte;
  projectItem.group = assignment.pid;
  projectItem.start = assignment.start;
  projectItem.end = assignment.end;
  projectItem.id = assignment.aid;

  var engineerItem = {};
  engineerItem.content = assignment.fte + ' FTE: ' + assignment.pid;
  engineerItem.fte = assignment.fte;
  engineerItem.group = assignment.eid;
  engineerItem.start = assignment.start;
  engineerItem.end = assignment.end;
  engineerItem.id = assignment.aid;

  allAssignments.update(assignment);
  engineerTLItems.update(engineerItem);
  projectTLItems.update(projectItem);
};

// Projects and Engineers Timelines
// --------------------------------
var projectsContainer = document.getElementById('visjs-projects-container');
var projectsTimeline = new vis.Timeline(projectsContainer, projectTLItems, allProjects, timelineOptions);

var engineersContainer = document.getElementById('visjs-engineers-container');
var engineersTimeline = new vis.Timeline(engineersContainer, engineerTLItems, allEngineers, timelineOptions);

// map contextmenu (ie. right mouse button)
// to open a modal window to update assignments
function openAssignmentModal (properties) {
  properties.event.preventDefault(); // prevent default browser pop-up menu

  if (properties.what == 'item') {
    var assignment = allAssignments.get(properties.item);

    $('#inputAid').text(assignment.aid);
    $('#inputEngineer').val(assignment.eid);
    $('#inputProject').val(assignment.pid);
    $('#inputFTE').val(assignment.fte);
    $('#inputStart').val(assignment.start);
    $('#inputEnd').val(assignment.end);

    $('#inputAidDiv').show()
    $('#inputEngineerDiv').hide()
    $('#inputLinemanagerDiv').hide();
    $('#inputCoordinatorDiv').hide();
    $('#inputProjectDiv').show()
    $('#inputFTEDiv').show()
    $('#inputStartDiv').show()
    $('#inputEndDiv').show()
  } else if (properties.what == 'group-label' && allProjects.get(properties.group)) {
    var project = allProjects.get(properties.group);

    $('#inputAid').text(project.pid);
    $('#inputCoordinator').val(project.coordinator);
    $('#inputFTE').val(project.fte);
    $('#inputStart').val(project.start);
    $('#inputEnd').val(project.end);

    $('#inputAidDiv').show()
    $('#inputEngineerDiv').hide()
    $('#inputLinemanagerDiv').hide();
    $('#inputCoordinatorDiv').show();
    $('#inputProjectDiv').hide()
    $('#inputFTEDiv').show()
    $('#inputStartDiv').show()
    $('#inputEndDiv').show()
  } else if (properties.what == 'group-label' && allEngineers.get(properties.group)) {
    var engineer = allEngineers.get(properties.group);

    $('#inputAid').text(engineer.eid);
    $('#inputLinemanager').val(engineer.coordinator);
    $('#inputFTE').val(engineer.fte);
    $('#inputStart').val(engineer.start);
    $('#inputEnd').val(engineer.end);

    $('#inputAidDiv').show()
    $('#inputEngineerDiv').hide()
    $('#inputLinemanagerDiv').show();
    $('#inputCoordinatorDiv').hide();
    $('#inputProjectDiv').hide()
    $('#inputFTEDiv').show()
    $('#inputStartDiv').show()
    $('#inputEndDiv').show()
  } else {
    console.log(properties);
    return;
  }

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

  applyAssignmentUpdate(assignment);
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
  var firstSelectedAssignment = allAssignments.get(properties.items[0]);

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
  var firstSelectedAssignment = allAssignments.get(properties.items[0]);


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
  'state': 'all', // all, active, inactive
  'coordinator': 'all',
  'linemanager': 'all',
  'engineer': 'all'
};

/**
 * Apply the filtering described in the filterSettings on the following:
 *   - engineerTLItems
 *   - projectTLItems
 *   - projects
 * As the timelines are bound to the DataSet, updating the views is automatic
 *
 * uses global args:
 *   filterSettings, allAssignments
 *
 * datasets filtered:
 *   engineerTLItems, projectTLItems
 */
function applyFilterSettings () {
  // projects are groups on the timeline and have a boolean 'visible'
  // This hides the all items: the assignments and the duration (type 'background', in green)
  allProjects.forEach(function (project) {
    project.visible = false;

    if ((
      // if set, only show active/inactive projects
      (filterSettings.state == 'all') ||
      (filterSettings.state == 'active' && project.active == true) ||
      (filterSettings.state == 'inactive' && project.active == false)
    ) && (
      // if set, only show projects with selected coordinator
      (filterSettings.coordinator == 'all') ||
      (filterSettings.coordinator == project.coordinator)
    )) {
      project.visible = true;
    }
    if (filterSettings.engineer != 'all') {
      needle = false;
      // if set, remove projects that dont have the selected engineer assigned:
      // iterate over all projects, and stop and return true as soon as one assignment matches
      project.visible = allAssignments.get().some(function (assignment) {
        return (assignment.pid == project.pid && assignment.eid == filterSettings.engineer);
      });
    }
    allProjects.update(project);
  });

  // engineers are groups on the timeline and have a boolean 'visible'
  allEngineers.forEach(function (engineer) {
    engineer.visible = false;
    if ((
      // if set, only show active/inactive engineers
      (filterSettings.state == 'all') ||
      (filterSettings.state == 'active' && engineer.active == true) ||
      (filterSettings.state == 'inactive' && engineer.active == false)
    ) && (
      // if set, only show selected engineer
      (filterSettings.engineer == 'all') ||
      (filterSettings.engineer == engineer.id)
    )) {
      engineer.visible = true;
    }
    allEngineers.update(engineer);
  });

  // assignments are items on a timeline, that cannot be individually hidden/shown
  // so actually remove or add them where necessary
  var addEAs = [];
  // var addPAs = [];
  var removeAid = [];
  allAssignments.forEach(function (assignment) {
    var show = false;
    var project = allProjects.get(assignment.pid);
    var engineer = allEngineers.get(assignment.eid);

    if ((
      (filterSettings.state == 'all') ||
      (filterSettings.state == 'active' && project.active == true) ||
      (filterSettings.state == 'inactive' && project.active == false)
    ) && (
      (filterSettings.coordinator == 'all') ||
      (filterSettings.coordinator = project.coordinator)
    ) && (
      (filterSettings.engineer == 'all') ||
      (filterSettings.engineer == assignment.eid)
    )) {
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

  engineerTLItems.remove(removeAid);
  engineerTLItems.update(addEAs);

  // projectTLItems.remove(removeAid);
  // projectTLItems.update(addPAs);
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

$('#inputStatusOptions').on('change', function () {
  filterSettings.state = $('#inputStatusOptions').val();
  applyFilterSettings();
});

$('#inputSortOptions').on('change', function () {
  var sort = $('#inputSortOptions').val();

  engineersTimeline.setOptions({groupOrder: 'id'});

  if (sort == 'name') {
    projectsTimeline.setOptions({groupOrder: 'id'});
  } else if (sort == 'start') {
    projectsTimeline.setOptions({groupOrder: 'sortStart'});
  } else if (sort == 'end') {
    projectsTimeline.setOptions({groupOrder: 'sortEnd'});
  }
});

$('#inputCoordinatorOptions').on('change', function () {
  filterSettings.coordinator = $('#inputCoordinatorOptions').val();
  applyFilterSettings();
});

$('#inputLinemanagerOptions').on('change', function () {
  filterSettings.linemanager = $('#inputLinemanagerOptions').val();
  applyFilterSettings();
});

$('#inputEngineerOptions').on('change', function () {
  filterSettings.engineer = $('#inputEngineerOptions').val();
  applyFilterSettings();
});
