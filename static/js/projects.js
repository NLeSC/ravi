/**
 * Add projects to the project timeline
 * Add projects to the engineer assignment popup
 *
 * An project is an object with the following properties:
 * Project {
 *   pid          string
 *   active       boolean
 *   comments     string
 *   coordinator  eid
 *   start        YYYY-MM
 *   end          YYYY-MM
 *   exact_code   integer
 *   fte          number
 * }
 *
 * arguments:
 *    projects: Array[project]
 *
 * uses the following global variables:
 *    allProjects
 */

function initializeProjects(projects) {
  projects.forEach(function(project) {
    // sanitize data
    var d;
    var start = project.start || '2015-01';
    var end = project.end || '2050-01';
    var assigned = project.assigned || 0;
    var fte = project.fte || 0;
    var coordinator = project.coordinator || " - ";

    allProjects.update({
      id: project.pid,
      pid: project.pid,
      content: "<b>" + project.pid + "</b>" +
        "<br>Assigned " + assigned.toFixed(2) + " / " + fte.toFixed(2) + " FTE" +
        "<br>" + coordinator,

      active: project.active,
      comments: project.comments,
      coordinator: project.coordinator,
      start: start,
      end: end,
      sortStart: "" + start,
      sortEnd: "" + end,
      exact_code: project.exact_code,
      fte: project.fte,
      assigned: project.assigned,
      balance: project.fte - project.assigned
    });

    if (project.coordinator) {
      allCoordinators.update({
        id: project.coordinator
      });
    }
  });

  // Add projects to the filter box, subdivide by active / inactive
  filterBox = $('#inputProjectOptions');
  filterBox.empty();
  $('<option />', { value: 'all', text: 'All' }).appendTo(filterBox);
  var activeList = $('<optgroup>', { label: 'Active' }).appendTo(filterBox);
  var inactiveList = $('<optgroup>', { label: 'Inactive' }).appendTo(filterBox);

  allProjects.forEach(function(project) {
    if (project.active) {
      $('<option />', { value: project.id, text: project.id }).appendTo(activeList);
    } else {
      $('<option />', { value: project.id, text: project.id }).appendTo(inactiveList);
    }
  });

  // Add projects to the input box
  inputBox = $('#inputProject');
  inputBox.empty();
  allProjects.forEach(function(project) {
    $('<option />', { value: project.id, text: project.id }).appendTo(inputBox);
  });

  // Add coordinators to the drop down menus
  inputBox = $('#inputCoordinator');
  filterBox = $('#inputCoordinatorOptions');
  inputBox.empty();
  filterBox.empty();

  $('<option />', { value: 'all', text: 'All' }).appendTo(filterBox);

  allCoordinators.forEach(function (coordinator) {
    $('<option />', { value: coordinator.id, text: coordinator.id, }).appendTo(inputBox);
    $('<option />', { value: coordinator.id, text: coordinator.id, }).appendTo(filterBox);
  });
}

/**
 * Send a request for projects to the server.
 * The response is parsed, and the global var allProjects is update()-ed via
 * a call to initializeProjects()
 */
function sendRequestForProjectsToServer () {
  return fetch('/get_projects')
  .then(function (response) {
    return response.json();
  })
  .then(function (data) {
    initializeProjects(data);
  })
  .catch(function (error) {
    alert('Cannot get projects from server');
    console.error(error);
  });
}

/**
 * Send a project object to the server
 *
 * arguments:
 *    project
 */
function sendProjectToServer (project) {
  form = new FormData()
  form.append('pid', project.pid || '');
  form.append('fte', project.fte || '');
  form.append('start', project.start || '');
  form.append('end', project.end || '');
  form.append('active', project.active ? 1 : 0);
  form.append('coordinator', project.coordinator || '');

  fetch('/update_project', {
    method: 'POST',
    body: form
  })
  .catch(function (error) {
    alert('Cannot update project at server');
    console.error(error);
  });
}

/**
 * Send a request for the overview to the server.
 */
function sendRequestForOverviewToServer () {
  overviewItems.clear();
  overviewItems.flush();

  return fetch('/get_overview')
  .then(function (response) {
    return response.json();
  })
  .then(function (data) {
    // Add overview data to plot
    data['available'].forEach(function (item) {
      overviewItems.add({
        x: item.start,
        end: item.end,
        y: item.fte,
        group: 'available'
      });
    });
    data['required'].forEach(function (item) {
      overviewItems.add({
        x: item.start,
        end: item.end,
        y: item.fte,
        group: 'required'
      });
    });
    overviewItems.flush();
    overviewPlot.fit({animation: false});
  })
  .catch(function (error) {
    alert('Cannot get projects from server');
    console.error(error);
  });
}

/**
 * Send a request for the hours written on the project
 * assume response is orderd by date
 */
function sendRequestForProjectWrittenHours(project) {
  var myRequest = new Request('/get_project_written_hours', {
    method: 'POST',
    body: JSON.stringify(project)
  });

  detailItems.clear();
  detailGroups.clear();

  detailGroups.flush();
  detailItems.flush();

  return fetch(myRequest)
  .then(function (response) {
    return response.json();
  })
  .then(function (data) {
    var totalByMedewerker = {};
    var totalByDate = {};

    detailGroups.update({
      id: 0,
      content: '| Actual'
    });
    detailGroups.update({
      id: 1,
      content: '| Available ' + project.fte.toFixed(2)
    });

    detailGroups.update({
      id: 2,
      content: '| Planning'
    });

    data.forEach(function (item) {
      if (item.Medewerker == 'Planning') {
        detailItems.add({
          x: item.date,
          y: item.Aantal,
          group: 2
        });
      } else {
        // Accumulate hours per employee
        totalByMedewerker[item.Medewerker] = totalByMedewerker[item.Medewerker] || 0;
        totalByMedewerker[item.Medewerker] = totalByMedewerker[item.Medewerker] + item.Aantal;

        // Accumulate hours per date
        totalByDate[item.date] = totalByDate[item.date] || 0;
        totalByDate[item.date] = totalByDate[item.date] + item.Aantal;

        detailGroups.update({
          id: item.Medewerker,
          content: item.Medewerker
        });
        detailItems.add({
          x: item.date,
          y: totalByMedewerker[item.Medewerker],
          group: item.Medewerker
        });
      }
    });

    // running sum of actual hours
    var previous = 0;
    for (var key in totalByDate) {
      detailItems.add({
        x: key,
        y: totalByDate[key] + previous,
        group: 0
      });
      previous = previous + totalByDate[key];
    }

    // roofline
    detailItems.add({
      x: project.start,
      y: project.fte * 1680,
      group: 1
    });
    detailItems.add({
      x: project.end,
      y: project.fte * 1680,
      group: 1
    });

    // update timedetail plot
    detailGroups.flush();
    detailItems.flush();
    detailPlot.fit();
    detailPlot.redraw();
  })
  .catch(function (error) {
    alert('Cannot get project hours from server');
    console.error(error);
  });
}
