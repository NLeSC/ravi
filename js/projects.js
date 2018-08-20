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

    allProjects.update({
      id: project.pid,
      pid: project.pid,
      content: project.pid,

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

  // add to the modal pop up on the engineer timeline
  inputBox = $('#inputProject');
  filterBox = $('#inputProjectOptions');

  inputBox.empty();
  filterBox.empty();

  $('<option />', { value: 'all', text: 'All' }).appendTo(filterBox);

  allProjects.forEach(function(project) {
    $('<option />', { value: project.id, text: project.content }).appendTo(inputBox);
    $('<option />', { value: project.id, text: project.content }).appendTo(filterBox);
  });

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
  return fetch('http://localhost:5000/get_projects')
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
 * Send a request for the overview to the server.
 */
function sendRequestForOverviewToServer () {
  return fetch('http://localhost:5000/get_overview')
  .then(function (response) {
    return response.json();
  })
  .then(function (data) {
    // Add overview data to plot
    overviewItems.clear();

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
  var myRequest = new Request('http://localhost:5000/get_project_written_hours', {
    method: 'POST',
    body: '{"Projectcode":"' + project.exact_code + '"}'
  });

  return fetch(myRequest)
  .then(function (response) {
    return response.json();
  })
  .then(function (data) {
    detailItems.clear();
    detailGroups.clear();

    detailGroups.update({
      id: 0,
      content: 'Ideal'
    });
    detailGroups.update({
      id: 1,
      content: 'Actual'
    });

    var totalByMedewerker = {};
    var totalByDate = {};

    data.forEach(function (item) {
      detailGroups.update({
        id: item.Medewerker,
        content: item.Medewerker
      });

      totalByMedewerker[item.Medewerker] = totalByMedewerker[item.Medewerker] || 0;
      totalByMedewerker[item.Medewerker] = totalByMedewerker[item.Medewerker] + item.Aantal;

      totalByDate[item.date] = totalByDate[item.date] || 0;
      totalByDate[item.date] = totalByDate[item.date] + item.Aantal;

      detailItems.add({
        x: item.date,
        y: totalByMedewerker[item.Medewerker],
        group: item.Medewerker
      });

    });

    var previous = 0;
    for (var key in totalByDate) {
      detailItems.add({
        x: key,
        y: totalByDate[key] + previous,
        group: 1
      });
      previous = previous + totalByDate[key];
    }

    detailItems.add({
      x: project.start,
      y: 0,
      group: 0
    });
    detailItems.add({
      x: project.end,
      y: project.fte * 1680,
      group: 0
    });



    // update timedetail plot
    detailPlot.fit();
  })
  .catch(function (error) {
    alert('Cannot get project hours from server');
    console.error(error);
  });
}
