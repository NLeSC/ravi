// The full datasets, containing all information necessary to
// sync with the server
var allAssignments = new vis.DataSet();
var allEngineers = new vis.DataSet();
var allProjects = new vis.DataSet();
var allLinemanagers = new vis.DataSet();
var allCoordinators = new vis.DataSet();
var allLoads = new vis.DataSet();

var modalType; // if we are editing an assignment, an engineer, or a project

// Datasets bound to the timelines.
// These are filtered depending on filterSettings,
// and contain only the currently visible data

var engineerTLItems = new vis.DataSet({queue: true});
var projectTLItems = new vis.DataSet({queue: true});
var overviewItems = new vis.DataSet({queue: true});

// Configuration for the Timeline
var d = new Date();
var year = d.getFullYear();
var month = d.getMonth();
var day = d.getDate();

var itemEditableOptions = {
  add: true,           // add new items by double tapping
  updateTime: true,    // drag items horizontally
  updateGroup: false,  // drag items from one group to another
  remove: true,        // delete an item by tapping the delete button top right
  overrideItems: true  // allow these options to override item.editable
}
var timelineOptions = {
  height: '120%',
  verticalScroll: true,
  horizontalScroll: true,
  start: new Date(year - 1, month, day),
  end: new Date(year + 1, month, day),
  zoomKey: 'altKey',
  zoomable: false,
  moveable: true,
  zoomMin: 15768000000,  // Half a year
  zoomMax: 315360000000, // 10 years
  editable: itemEditableOptions,
  orientation: {
    axis: 'top',
    item: 'top'
  },
  groupEditable: true,
  type: 'range',
  template: function (item, element, data) {
    // Heigth classes 0.0 - 0.2
    //                0.2 - 0.4
    //                0.4 - 0.6
    //                0.6 - 0.8
    //                0.8 - 1.0
    var fte = parseFloat(item.fte);

    var className;
    if (fte < 0.2) {
      className = 'item-fte-01';
    } else if (fte < 0.2) {
      className = 'item-fte-12';
    } else if (fte < 0.4) {
      className = 'item-fte-24';
    } else if (fte < 0.6) {
      className = 'item-fte-46';
    } else if (fte < 0.8) {
      className = 'item-fte-68';
    } else {
      className = 'item-fte-80';
    }
    var html = '<div class="' + className + '" >' + item.content + '</div>';
    return html;
  },
  groupTemplate: function (item, element) {
    var html;

    if (allEngineers.get(item.id)) {
      var engineer = allEngineers.get(item.id);
      html = '<div"> <img width=150px src="assets/' + engineer.eid + '.png")></div><div>' + item.content + '</div>';
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
    engineerTLItems.flush();

    projectTLItems.remove(item);
    projectTLItems.flush();

    allAssignments.remove(item);

    sendDeleteAssignmentToServer(item.id);
    callback(null); // we already removed the assignment ourselves, so block any further action

    // give a visual hint to the user that the background plots need refreshing
    $('#refresh-background').addClass('refresh-background');
  },
  onMove: function (item, callback) {
    var aid = item.id;

    var assignment = allAssignments.get(aid);
    var engineerItem = engineerTLItems.get(aid);
    var projectItem = projectTLItems.get(aid);

    // make sure the assignment has proper dates
    item.start = new Date(item.start)
    item.end = new Date(item.end)

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
      assignment.pid = '' // by default, no project
    } else if (allProjects.get(item.group)) {
      assignment.eid = '' // by default, no engineer
      assignment.pid = item.group;
    }

    // have the database create the assignment and have it find
    // an assignment index (aid)
    sendCreateAssignmentToServer(assignment);

    // the assignment will be added when the server responds, so we're done here
    callback(null);

    // give a visual hint to the user that the background plots need refreshing
    $('#refresh-background').addClass('refresh-background');
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
  engineerTLItems.flush();

  projectTLItems.update(projectItem);
  projectTLItems.flush();

  // give a visual hint to the user that the background plots need refreshing
  $('#refresh-background').addClass('refresh-background');
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

var detailGroups = new vis.DataSet([], {queue: true});
var detailItems = new vis.DataSet([], {queue: true});

var detailPlotContainer = document.getElementById('visjs-detail-plot');
var detailPlot = new vis.Graph2d(detailPlotContainer, detailItems, detailGroups, {
  interpolation: false,
  legend: true
});
detailPlot.on('rangechanged', function () {detailPlot.redraw()});

function openAssignmentModal (properties) {
  if (properties.item) {
    modalType = 'assignment';
    var assignment = allAssignments.get(properties.item);

    $('#modal-title-detail').text(assignment.aid);
    $('#inputEngineer').val(assignment.eid);
    $('#inputProject').val(assignment.pid);
    $('#inputFTE').val(assignment.fte);
    $('#inputStart').val(assignment.start);
    $('#inputEnd').val(assignment.end);

    $('#visjs-detail-plot').hide();
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
    modalType = 'project';
    var project = allProjects.get(properties.group);
    sendRequestForProjectWrittenHours(project);
    $('#visjs-detail-plot').show();

    $('#modal-title-detail').text(project.pid + " [exact code: " + project.exact_code + "]");
    $('#inputProject').val(project.pid);
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
    modalType = 'engineer';
    var engineer = allEngineers.get(properties.group);
    $('#visjs-detail-plot').hide();

    $('#modal-title-detail').text(engineer.eid);
    $('#inputEngineer').val(engineer.eid);
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
    return;
  }

  // start the model dialog continue processing on #assignmentUpdateApply.on('click')
  $('#assignmentModal').modal();
}

// update the assignment when the user clicks on the 'Apply changes' button
$('#assignmentUpdateApply').on('click', function () {
  if (modalType == 'assignment') {
    var assignment = {
      aid : $('#modal-title-detail').text(), // a span, not an input
      eid : $('#inputEngineer').val(),
      pid : $('#inputProject').val(),
      fte : $('#inputFTE').val(),
      start : $('#inputStart').val(),
      end : $('#inputEnd').val()
    };
    assignment.id = assignment.aid; // re-use the aid as DataSet id

    applyAssignmentUpdate(assignment);
    sendAssignmentToServer(assignment);

    // high-light the updated assignment and zoom to it
    engineersTimeline.setSelection([assignment.id]);
    engineersTimeline.focus([assignment.id]);

    projectsTimeline.setSelection([assignment.id]);
    projectsTimeline.focus([assignment.id]);
  } else if (modalType == 'engineer') {
    var eid =  $('#inputEngineer').val();
    var engineer = allEngineers.get(eid);

    engineer.fte = $('#inputFTE').val();
    engineer.start = $('#inputStart').val();
    engineer.end = $('#inputEnd').val();
    engineer.coordinator = $('#inputLinemanager').val();
    engineer.active = $('#inputStatus').val();
    allEngineers.update(engineer);

    sendEngineerToServer(engineer);
  } else if (modalType == 'project' ) {
    var pid =  $('#inputProject').val();
    var project = allProjects.get(pid);

    project.fte = $('#inputFTE').val();
    project.start = $('#inputStart').val();
    project.end = $('#inputEnd').val();
    project.coordinator = $('#inputCoordinator').val();
    project.active = $('#inputStatus').val();
    allProjects.update(project);

    sendProjectToServer(project);
  }

  $('#assignmentModal').modal('hide');
  $('#refresh-background').addClass('refresh-background');
});

engineersTimeline.on('doubleClick', openAssignmentModal);
projectsTimeline.on('doubleClick', openAssignmentModal);

// Link the Engineers and Project timelines
// ----------------------------------------

// automatically select the assignments on the other timeline
engineersTimeline.on('select', function (properties) {
  if (! properties || ! properties.items) {
    projectsTimeline.setSelection([]);
    return;
  }
  var focusAssignment = allAssignments.get(properties.items[0]);

  // if the assignment has a project, focus the projects timeline on that
  if (focusAssignment.pid) {
    projectsTimeline.setSelection(focusAssignment.id);
    projectsTimeline.focus(focusAssignment.id);
  } else {
    projectsTimeline.setSelection([]);
  }
});

projectsTimeline.on('select', function (properties) {
  if (! properties || ! properties.items) {
    engineersTimeline.setSelection([]);
    return;
  }
  var focusAssignment = allAssignments.get(properties.items[0]);

  // if the assignment has an engineer, focus the engineers timeline on that
  if (focusAssignment.eid) {
    engineersTimeline.setSelection(focusAssignment.id);
    engineersTimeline.focus(focusAssignment.id);
  } else {
    engineersTimeline.setSelection([]);
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
function draw_project_background () {
  // NOTE: we dont control the ID for the load, as it is the result of
  // some complex SQL query. Therefore we cannot update the items, but
  // we have to remove and add everything
  remove_backgrounds(projectTLItems);

  allProjects.forEach(function (project) {
    var color;
    var style;
    var content;

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

    projectTLItems.update({
      id: project.pid,
      group: project.pid,
      start: project.start,
      end: project.end,
      content: '',
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
function draw_engineer_background () {
  // NOTE: we dont control the ID for the load, as it is the result of
  // some complex SQL query. Therefore we cannot update the items, but
  // we have to remove and add everything
  remove_backgrounds(engineerTLItems);

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
      content: '', // "" + load.fte.toFixed(2) + " FTE",
      style: "background-color: " + color
    });
  });
  engineerTLItems.flush();
}

$('#refresh-background').on('click', function () {
  $('#refresh-background').removeClass('refresh-background');
  $('#refresh-background').addClass('refreshing-background');
  Promise.all([
    sendRequestForEngineersToServer(),
    sendRequestForEngineerLoadsToServer(),
    sendRequestForProjectsToServer(),
    sendRequestForAssignmentsToServer()
  ]).then(function () {
    $('#refresh-background').removeClass('refreshing-background');
    resetViews();
  });
});

$('#inputExtraOptions').on('change', function () {
  var val = $('#inputExtraOptions').val();

  if (val == 'clear') {
    filterSettings = {
      'show': 'eng_and_proj', // eng_and_proj, eng, proj, overview
      'state': 'active', // all, active, inactive
      'coordinator': 'all',
      'linemanager': 'all',
      'engineer': 'all',
      'project': 'all'
    };

    // TODO: select something else than the just clicked-on item for the inputExtraOptions
    $('#inputExtraOptions').val('...');
    $('#inputStatusOptions').val(filterSettings['state']);
    $('#inputCoordinatorOptions').val(filterSettings['coordinator']);
    $('#inputLinemanagerOptions').val(filterSettings['linemanager']);
    $('#inputEngineerOptions').val(filterSettings['engineer']);
    $('#inputProjectOptions').val(filterSettings['project']);
    resetViews();
  }
});

// Hash containing all filterable properties
// Apply filtering using the 'applyFilterSettings' function below
var filterSettings = {
  'show': 'eng_and_proj', // eng_and_proj, eng, proj, overview
  'state': 'active', // all, active, inactive
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
      needle = project.visible;
      // if set, remove projects that dont have the selected engineer assigned:
      project.visible = needle && allAssignments.get().some(function (assignment) {
        return (assignment.pid == project.pid && assignment.eid == filterSettings.engineer);
      });
    }
    if (filterSettings.linemanager != 'all') {
      needle = project.visible;
      // if set, remove projects that are not assigned to a engineer with the select linemanager
      project.visible = needle && allAssignments.get().some(function (assignment) {
        var engineer = allEngineers.get(assignment.eid) || {linemananer: false};
        return (assignment.pid == project.pid && filterSettings.linemanager == engineer.coordinator);
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
    ) && (
      // if set, only show projects with selected coordinator
      (filterSettings.linemanager == 'all') ||
      (filterSettings.linemanager == engineer.coordinator)
    )) {
      engineer.visible = true;
    }
    if (filterSettings.project != 'all') {
      needle = engineer.visible;
      // if set, remove engineers that are not assigned to the selected project
      engineer.visible = needle && allAssignments.get().some(function (assignment) {
        return (assignment.eid == engineer.eid && assignment.pid == filterSettings.project);
      });
    }
    if (filterSettings.coordinator != 'all') {
      needle = engineer.visible;
      // if set, remove engineers that are not assigned to the selected project
      engineer.visible = needle && allAssignments.get().some(function (assignment) {
        var project = allProjects.get(assignment.pid) || {coordinator: false};
        return (assignment.eid == engineer.eid && filterSettings.coordinator == project.coordinator);
      });
    }
    allEngineers.update(engineer);
  });

  // assignments are items on a timeline, that cannot be individually hidden/shown
  // so actually remove or add them where necessary
  allAssignments.forEach(function (assignment) {
    var show = false;
    var project = allProjects.get(assignment.pid) || {active: 'show-always', coordinator: false};

    if ((
      (filterSettings.state == 'all') ||
      (project.active == 'show-always') ||
      (filterSettings.state == 'active' && project.active == true) ||
      (filterSettings.state == 'inactive' && project.active == false)
    ) && (
      (filterSettings.coordinator == 'all') ||
      (filterSettings.coordinator == project.coordinator)
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
      (filterSettings.show == 'eng')
    )) {
      engineerTLItems.update({
        id: assignment.aid,
        group: assignment.eid,
        start: assignment.start,
        end: assignment.end,
        content: assignment.fte + ' FTE: ' + assignment.pid,
        fte: assignment.fte,
        editable: itemEditableOptions
      });
    } else {
      engineerTLItems.remove(assignment.id);
    }

    // update assignment on project timeline
    if (show && (
      (filterSettings.show == 'eng_and_proj') ||
      (filterSettings.show == 'proj')
    )) {
      projectTLItems.update({
        id: assignment.aid,
        group: assignment.pid,
        start: assignment.start,
        end: assignment.end,
        content: assignment.fte + ' FTE: ' + assignment.eid,
        fte: assignment.fte,
        editable: itemEditableOptions
      });
    } else {
      projectTLItems.remove(assignment.id);
    }
  });

  engineerTLItems.flush();
  projectTLItems.flush();
}

function sendRequestForLogToServer() {
  var myRequest = new Request('/get_log', {
    method: 'POST',
    body: JSON.stringify(filterSettings)
  });

  return fetch(myRequest)
  .then(function (response) {
    return response.json();
  })
  .then(function (data) {
    $('#log-body').empty();
    var table = $('#log-table');

    var addColumn = function (a,b) {
      if ((a==b) || (! a || !b)) {
        return "<td>" + (a || "") + "</td>" + "<td>" + (b || "") + "</td>";
      } else {
        return '<td class="log-old">' + (a || "") + "</td>" + '<td class="log-new">' + (b || "") + "</td>";
      }
    };

    data.forEach(function(row)  {
      var tr = "<tr>";

      tr += '<th scope="col">' + row.date + "</td>";
      tr += "<td>" + row.comment + "</td>";
      tr += addColumn(row.oldfte, row.newfte);
      tr += addColumn(row.oldeid, row.neweid);
      tr += addColumn(row.oldpid, row.newpid);
      tr += addColumn(row.oldstart, row.newstart);
      tr += addColumn(row.oldend, row.newend);
      tr += "</tr>";

      table.append(tr);
    });
  })
  .catch(function (error) {
    alert('Cannot get log from server');
    console.error(error);
  });
};

function resetViews () {
  var option = $('#inputWindowOptions').val();
  filterSettings.show = option;

  var projTL = $('#visjs-projects-container');
  var engTL = $('#visjs-engineers-container');
  var ovPlt = $('#visjs-overview-container');
  var logTable = $('#log-container');

  $('#inputStatusOptions').prop("disabled", false);
  $('#inputCoordinatorOptions').prop("disabled", false);
  $('#inputLinemanagerOptions').prop("disabled", false);
  $('#inputEngineerOptions').prop("disabled", false);
  $('#inputProjectOptions').prop("disabled", false);

  if (option == 'eng_and_proj') {
    projTL.removeClass('w-100');
    projTL.addClass('w-50');
    projTL.show();
    engTL.removeClass('w-100');
    engTL.addClass('w-50');
    engTL.show();

    ovPlt.hide();
    logTable.hide();

    draw_project_background();
    draw_engineer_background();
  } else if (option == 'eng') {
    engTL.removeClass('w-50');
    engTL.addClass('w-100');
    engTL.show();
    projTL.hide();
    ovPlt.hide();
    logTable.hide();

    draw_engineer_background();
  } else if (option == 'proj') {
    projTL.removeClass('w-50');
    projTL.addClass('w-100');
    projTL.show();
    engTL.hide();
    ovPlt.hide();
    logTable.hide();

    draw_project_background();
  } else if (option == 'overview') {
    sendRequestForOverviewToServer();
    engTL.hide();
    projTL.hide();
    logTable.hide();
    ovPlt.show();

    $('#inputStatusOptions').prop("disabled", true);
    $('#inputCoordinatorOptions').prop("disabled", true);
    $('#inputLinemanagerOptions').prop("disabled", true);
    $('#inputEngineerOptions').prop("disabled", true);
    $('#inputProjectOptions').prop("disabled", true);
  } else if (option == 'log') {
    sendRequestForLogToServer();
    engTL.hide();
    projTL.hide();
    ovPlt.hide();
    logTable.show();
    $('#inputStatusOptions').prop("disabled", true);
    $('#inputCoordinatorOptions').prop("disabled", true);
    $('#inputLinemanagerOptions').prop("disabled", true);
  }

  applyFilterSettings();
}

$('#inputWindowOptions').on('change', resetViews);

$('#inputStatusOptions').on('change', function () {
  filterSettings.state = $('#inputStatusOptions').val();
  applyFilterSettings();
});

$('#inputProjectSortOptions').on('change', function () {
  var sort = $('#inputProjectSortOptions').val();

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

// TODO: on zoom, move to selection.. focus does not do what we want
$('#projectZoomIn').click(function () {
  projectsTimeline.zoomIn(0.4);
  // projectsTimeline.focus(projectsTimeline.getSelection());
});
$('#projectZoomOut').click(function () {
  projectsTimeline.zoomOut(0.4);
  // projectsTimeline.focus(projectsTimeline.getSelection());
});

$('#inputEngineerSortOptions').on('change', function () {
  var sort = $('#inputEngineerSortOptions').val();


  if (sort == 'name') {
    engineersTimeline.setOptions({groupOrder: 'id'});
  } else if (sort == 'start') {
    engineersTimeline.setOptions({groupOrder: 'sortStart'});
  } else if (sort == 'end') {
    engineersTimeline.setOptions({groupOrder: 'sortEnd'});
  } else if (sort == 'balance') {
    engineersTimeline.setOptions({groupOrder: 'balance'});
  }
});

// TODO: on zoom, move to selection.. focus does not do what we want
$('#engineerZoomIn').click(function () {
  engineersTimeline.zoomIn(0.4);
  // engineersTimeline.focus(engineersTimeline.getSelection());
});
$('#engineerZoomOut').click(function () {
  engineersTimeline.zoomOut(0.4);
  // engineersTimeline.focus(engineersTimeline.getSelection());
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
  if (filterSettings.show == 'log') {
    sendRequestForLogToServer();
  } else {
    applyFilterSettings();
  }
});

$('#inputProjectOptions').on('change', function () {
  filterSettings.project = $('#inputProjectOptions').val();
  if (filterSettings.show == 'log') {
    sendRequestForLogToServer();
  } else {
    applyFilterSettings();
  }
});

Promise.all([
  sendRequestForEngineersToServer(),
  sendRequestForEngineerLoadsToServer(),
  sendRequestForProjectsToServer(),
  sendRequestForAssignmentsToServer()
]).then(resetViews);
