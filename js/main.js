var datasetOptions = {};

// The full datasets, containing all information necessary to
// sync with the server
var allAssignments = new vis.DataSet(datasetOptions);
var allEngineers = new vis.DataSet(datasetOptions);
var allProjects = new vis.DataSet(datasetOptions);
var allLinemanagers = new vis.DataSet(datasetOptions);
var allCoordinators = new vis.DataSet(datasetOptions);
var allLoads = new vis.DataSet(datasetOptions);

// Datasets bound to the timelines.
// These are filtered depending on filterSettings,
// and contain only the currently visible data

var engineerTLItems = new vis.DataSet(datasetOptions);
var projectTLItems = new vis.DataSet(datasetOptions);
var overviewItems = new vis.DataSet(datasetOptions);

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
    overrideItems: true  // allow these options to override item.editable
  },
  orientation: {
    axis: 'top'
  },
  groupEditable: true,
  type: 'range',
  template: function (item, element, data) {
    var html = '<div>' + item.content + '</div>';
    return html;
  },
  groupTemplate: function (item, element) {
    var html;

    if (allEngineers.get(item.id)) {
      var engineer = allEngineers.get(item.id);
      html = '<div> <img width=150px src="assets/' + engineer.eid + '.png")> ' + item.content + '</div>';
    } else {
      html = '<div>' + item.content + '</div>';
    }
    return html;
  },
  groupOrder: 'id',
  // individual item events
  // these have to be passed to the options object on construction of the timeline
  onRemove: function (item, callback) {
    engineerTLItems.remove(item);
    projectTLItems.remove(item);
    allAssignments.remove(item);

    sendDeleteAssignmentToServer(item.id);
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
    }

    // when adding on engineers timeline, the group is the engineer
    // when adding on projects timeline, the group is the project
    if (allEngineers.get(item.group)) {
      assignment.eid = item.group;
    } else if (allProjects.get(item.group)) {
      assignment.pid = item.group;
    }

    // have the database create the assignment and have it find
    // an assignment index (aid)
    sendCreateAssignmentToServer(assignment);

    // get the new assignment from the server
    sendRequestForAssignmentsToServer(assignment.eid, assignment.pid);

    // the assignment will be added when the server responds, so we're done here
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

var overviewGroups = new vis.DataSet();
overviewGroups.add([
  {
    content: 'available',
    id: 'available',
    className: 'overview-available-line'
  }, {
    content: 'required',
    id: 'required',
    className: 'overview-required-line'
  }]
);

var overviewContainer = document.getElementById('visjs-overview-container');
var overviewPlot = new vis.Graph2d(overviewContainer, overviewItems, overviewGroups, {legend: true});
overviewPlot.on('rangechanged', function () {overviewPlot.redraw()});

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
    $('#inputEngineerDiv').show()
    $('#inputLinemanagerDiv').hide();
    $('#inputCoordinatorDiv').hide();
    $('#inputProjectDiv').show()
    $('#inputFTEDiv').show()
    $('#inputStartDiv').show()
    $('#inputEndDiv').show()
    $('#inputStatusDiv').hide();
  } else if (properties.what == 'group-label' && allProjects.get(properties.group)) {
    var project = allProjects.get(properties.group);

    $('#inputAid').text(project.pid);
    $('#inputCoordinator').val(project.coordinator);
    $('#inputFTE').val(project.fte);
    $('#inputStart').val(project.start);
    $('#inputEnd').val(project.end);
    $('#inputStatus').val(project.active ? 'active' : 'inactive');

    $('#inputAidDiv').show();
    $('#inputEngineerDiv').hide();
    $('#inputLinemanagerDiv').hide();
    $('#inputCoordinatorDiv').show();
    $('#inputProjectDiv').hide();
    $('#inputFTEDiv').show();
    $('#inputStartDiv').show();
    $('#inputEndDiv').show();
    $('#inputStatusDiv').show();
  } else if (properties.what == 'group-label' && allEngineers.get(properties.group)) {
    var engineer = allEngineers.get(properties.group);

    $('#inputAid').text(engineer.eid);
    $('#inputLinemanager').val(engineer.coordinator);
    $('#inputFTE').val(engineer.fte);
    $('#inputStart').val(engineer.start);
    $('#inputEnd').val(engineer.end);
    $('#inputStatus').val(engineer.active ? 'active' : 'inactive');

    $('#inputAidDiv').show();
    $('#inputEngineerDiv').hide();
    $('#inputLinemanagerDiv').show();
    $('#inputCoordinatorDiv').hide();
    $('#inputProjectDiv').hide();
    $('#inputFTEDiv').show();
    $('#inputStartDiv').show();
    $('#inputEndDiv').show();
    $('#inputStatusDiv').show();
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

/**
 * Remove all items with property 'background'
 * from the dataset.
 * NOTE: this will automatically remove them from the timeline plot
 *
 * arguments:
 *   dataset  : the DataSet to prune
 */
function remove_backgrounds (dataset) {
  var backgrounds = [];
  dataset.forEach(function (item) {
    if (item.type == 'background') {
      backgrounds.push(item.id);
    }
  })
  dataset.remove(backgrounds);
}

/**
 * Draw project load as items on the project timeline
 * remove any other background present.
 * arguments:
 *   background : string, must be 'full' or 'summary'
 */
function draw_project_background (background) {
  remove_backgrounds(projectTLItems);

  // add project duration to the project timeline
  allProjects.forEach(function (project) {
    var color;
    var style;
    var content;

    if (background == 'summary') {
      if (project.balance < -0.5) {
        color = 'rgba(5, 5, 55, 0.20)';     // Dark grey
      } else if (project.balance < -0.1) {
        color = 'rgba(75, 75, 75, 0.20)';   // Grey
      } else if (project.balance < 0.1) {
        color = 'rgba(10, 255, 10, 0.20)';  // Green
      } else if (project.balance < 0.5) {
        color = 'rgba(200, 200, 10, 0.20)'; // Orange
      } else {
        color = 'rgba(255, 10, 10, 0.20)';  // Red
      }
      content = 'Assigned: ' + project.assigned.toFixed(2) + ' of ' + project.fte.toFixed(2) + ' FTE';
    } else if (background == 'full') {
      color = 'rgba(105, 255, 98, 0.20)';
      content = '';
    } else {
      console.error('Project background not implemented: ', background);
    }

    projectTLItems.update({
      id: project.pid,
      group: project.pid,
      start: project.start,
      end: project.end,
      content: content,
      type: 'background',
      style: 'background-color: ' + color,
      editable: false
    });
  });
}

/**
 * Draw engineer load as items on the project timeline
 * remove any other background present.
 *
 * arguments:
 *   background : string, must be 'full' or 'summary'
 */
function draw_engineer_background (background) {
  // NOTE: we dont control the ID for the load, as it is the result of
  // some complex SQL query. Therefore we cannot update the items, but
  // we have to remove and add everything
  remove_backgrounds(engineerTLItems);

  if (background == 'full') {
    return;
  }

  if (background != 'summary') {
    console.error('Background for engineer not implemented: ', background);
  }

  allLoads.forEach(function (load) {
    if (load.fte < -0.5) {
      color = 'rgba(5, 5, 55, 0.20)';     // Dark grey
    } else if (load.fte < -0.1) {
      color = 'rgba(75, 75, 75, 0.20)';   // Grey
    } else if (load.fte < 0.1) {
      color = 'rgba(10, 255, 10, 0.20)';  // Green
    } else if (load.fte < 0.5) {
      color = 'rgba(200, 200, 10, 0.20)'; // Orange
    } else {
      color = 'rgba(255, 10, 10, 0.20)';  // Red
    }

    engineerTLItems.add({
      group: load.eid,
      type: 'background',
      start: load.start,
      end: load.end,
      editable: false,
      content: "" + load.fte.toFixed(2) + " FTE",
      style: "background-color: " + color
    });
  });
}

// Hash containing all filterable properties
// Apply filtering using the 'applyFilterSettings' function below
var filterSettings = {
  'show': 'eng_and_proj', // eng_and_proj, eng, proj, eng_sum, proj_sum
  'state': 'all', // all, active, inactive
  'coordinator': 'all',
  'linemanager': 'all',
  'engineer': 'all',
  'project': 'all'
};

/**
 * Apply the filtering described in the filterSettings on the following:
 *   - engineerTLItems
 *   - projectTLItems
 *   - projects
 * As the timelines are bound to the DataSet, updating the views is automatic
 *
 * uses global args:
 *   filterSettings, allAssignments, allProjects, allEngineers
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
    ) && (
      // if set, only show the selected project
      (filterSettings.project == 'all') ||
      (filterSettings.project == project.pid)
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
    if (filterSettings.project != 'all') {
      needle = false;
      // if set, remove engineers that are not assigned to the selected project
      // iterate over all engineers, and stop and return true as soon as one assignment matches
      engineer.visible = allAssignments.get().some(function (assignment) {
        return (assignment.eid == engineer.eid && assignment.pid == filterSettings.project);
      });
    }
    allEngineers.update(engineer);
  });

  // assignments are items on a timeline, that cannot be individually hidden/shown
  // so actually remove or add them where necessary
  var addEA = [];
  var addPA = [];
  var removeEA = [];
  var removePA = [];
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
    ) && (
      (filterSettings.project == 'all') ||
      (filterSettings.project == assignment.pid)
    )) {
      show = true;
    }

    // update assignment on engineer timeline
    if (show && (
      (filterSettings.show == 'eng_and_proj') ||
      (filterSettings.show == 'eng') ||
      (filterSettings.show == 'eng_sum')
    )) {
      addEA.push({
        id: assignment.aid,
        group: assignment.eid,
        start: assignment.start,
        end: assignment.end,
        content: assignment.fte + ' FTE: ' + assignment.pid,
        editable: true
      });
    } else {
      removeEA.push(assignment.id);
    }

    // update assignment on project timeline
    if (show && (
      (filterSettings.show == 'eng_and_proj') ||
      (filterSettings.show == 'proj') ||
      (filterSettings.show == 'proj_sum')
    )) {
      addPA.push({
        id: assignment.aid,
        group: assignment.pid,
        start: assignment.start,
        end: assignment.end,
        content: assignment.fte + ' FTE: ' + assignment.eid,
        editable: true
      });
    } else {
      removePA.push(assignment.id);
    }
  });

  engineerTLItems.remove(removeEA);
  engineerTLItems.update(addEA);

  projectTLItems.remove(removePA);
  projectTLItems.update(addPA);
}

$('#inputWindowOptions').on('change', function () {
  var option = $('#inputWindowOptions').val();
  filterSettings.show = option;

  var projTL = $('#visjs-projects-container');
  var engTL = $('#visjs-engineers-container');
  var ovPlt = $('#visjs-overview-container');

  if (option == 'eng_and_proj') {
    draw_project_background('full');
    projTL.removeClass('w-100');
    projTL.addClass('w-50');
    projTL.show();

    draw_engineer_background ('full');
    engTL.removeClass('w-100');
    engTL.addClass('w-50');
    engTL.show();

    ovPlt.hide();
  } else if (option == 'eng') {
    draw_engineer_background ('full');
    engTL.removeClass('w-50');
    engTL.addClass('w-100');
    engTL.show();

    projTL.hide();
    ovPlt.hide();
  } else if (option == 'proj') {
    draw_project_background('full');
    projTL.removeClass('w-50');
    projTL.addClass('w-100');
    projTL.show();

    engTL.hide();
    ovPlt.hide();
  } else if (option == 'eng_sum') {
    draw_project_background('summary');
    projTL.removeClass('w-100');
    projTL.addClass('w-50');
    projTL.show();

    draw_engineer_background ('full');
    engTL.removeClass('w-100');
    engTL.addClass('w-50');
    engTL.show();
    ovPlt.hide();
  } else if (option == 'proj_sum') {
    draw_project_background('full');
    projTL.removeClass('w-100');
    projTL.addClass('w-50');
    projTL.show();

    draw_engineer_background ('summary');
    engTL.removeClass('w-100');
    engTL.addClass('w-50');
    engTL.show();
    ovPlt.hide();
  } else if (option == 'overview') {
    engTL.hide();
    projTL.hide();

    ovPlt.show();
    overviewPlot.fit();
    sendRequestForOverviewToServer();
  }

  applyFilterSettings();
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
  } else if (sort == 'balance') {
    projectsTimeline.setOptions({groupOrder: 'balance'});
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

$('#inputProjectOptions').on('change', function () {
  filterSettings.project = $('#inputProjectOptions').val();
  applyFilterSettings();
});


sendRequestForEngineersToServer();
sendRequestForProjectsToServer();
sendRequestForAssignmentsToServer();
sendRequestForEngineerLoadsToServer();
sendRequestForOverviewToServer();
