/* ========================= COMMON HELPER FUNCTIONS ======================== */
/*
 * Wrapper for localStorage
 */
var Storage = {
	set: function(key, value) {
		localStorage[key] = JSON.stringify(value);
	},

	get: function(key) {
		return localStorage[key] ? JSON.parse(localStorage[key]) : null;
	},

	exists: function(key) {
		return localStorage[key] != null;
	},
};

/*
 * Load the manifest dictionary and put in local storage
 */
function load_manifest(manifest_path) {
	$.getJSON(manifest_path, function(manifest) {
		Storage.set('manifest', manifest);
	});
}

/*
 * Set the displayed user agent name
 */
function set_user_agent_display(user_agent) {
	manifest = Storage.get('manifest');
	display = document.getElementById("user-agent-display");
	display.innerHTML = manifest["user-agents"][user_agent]["name"];
}

/*
 * Change the user agent and refresh the page.
 * user_agent argument should be a key in the user-agents dict in manifest
 */
function change_user_agent(user_agent) {
	Storage.set('current-user-agent', user_agent);
	set_user_agent_display(user_agent);

	// reload page data
	main(Storage.get('profile-dir'), Storage.get('current-user-agent'));
	console.log('changing user agent to: ' + user_agent);
}


/*
 * MAIN ENTRY POINT
 */
$(function () {
	var profile_dir = './profiles/';
	Storage.set('profile-dir', profile_dir);  // TODO: something better?
	load_manifest(profile_dir + 'manifest.json');

	// load user agent menu
	if (!Storage.exists('current-user-agent')) {
		Storage.set('current-user-agent', 'default');
	}
	set_user_agent_display(Storage.get('current-user-agent'));
	user_agents = Storage.get('manifest')['user-agents'];
	user_agent_menu = document.getElementById("user-agent-menu");
	for (var user_agent in user_agents) {
		user_agent_menu.innerHTML =
			'<li><a href="javascript: change_user_agent(\'' + user_agent + '\');">' 
			+ user_agents[user_agent]['name'] 
			+ '</a></li>'
			+ user_agent_menu.innerHTML;
	}

	// call page-specific main()
	main(profile_dir, Storage.get('current-user-agent'));
});


/* ========================================================================== */













function ulWriter(rowIndex, record, columns, cellWriter) {

	var row = "<tr>";

	// site URL
	row += "<td><a href=\"profile.html?site=" + record.site + "\">" + record.site + "</a></td>";


	//// HTTPS Support
	//if (record.availability == 'http-only')
	//	row += "<td><span class=\"label label-default\">HTTP Only</span></td>";
	//else if (record.availability == 'both')
	//	row += "<td><span class=\"label label-primary\">Both</span></td>";
	//else if (record.availability == 'https-only')
	//	row += "<td><span class=\"label label-success\">HTTPS Only</span></td>";
		
	
	// Availability
	if (record.availability == 'http-only')
		row += '<td><span class=\"label label-default\">HTTP</span>&nbsp;&nbsp;</td><td style="display:none">2</td>';
	else if (record.availability == 'both') {
		if (record.https_partial == 'yes')
			row += '<td><span class=\"label label-default\">HTTP</span>&nbsp;&nbsp;<span class=\"label label-danger\">Partial HTTPS</span></td><td style="display:none">0</td>';
		else
			row += '<td><span class=\"label label-default\">HTTP</span>&nbsp;&nbsp;<span class=\"label label-success\">HTTPS</span></td><td style="display:none">0</td>';
	} else if (record.availability == 'https-only') {
		if (record.https_partial == 'yes')
			row += '<td><span class=\"label label-danger\">Partial HTTPS</span></td><td style="display:none">1</td>';
		else
			row += '<td><span class=\"label label-success\">HTTPS</span></td><td style="display:none">1</td>';
	}

	row += "</tr>";

	return row;
}


function only_both(sites) {
	var new_sites = [];

	for (i=0; i < sites.length; i++) {
		if (sites[i]["availability"] == 'both') {
			new_sites.push(sites[i]);
		}
	}

	return new_sites;
}


/* 
 * MAIN
 */
function main(profile_dir, user_agent) {
	summary_path = profile_dir + user_agent + '/summary.json';
	$.getJSON(summary_path, function(data) {
		/*
		 * Site URL list
		 */
		$('#site-table').dynatable({
		  writers: {
		    _rowWriter: ulWriter
		  },
		  dataset: {
		    records: only_both(data["sites"])   // TODO: temporary
		  }
		});
		
		var dynatable = $('#site-table').data('dynatable');
		dynatable.paginationPerPage.set(100); // Show 100 records per page
		dynatable.process();


		//var tbl_body = "";
		//$.each(data["sites"], function() {
		//    var tbl_row = "";
		//	tbl_row += "<td><a href=\"profile.html?site=" + this["Site"] + "\">" + this["Site"] + "</a></td>";
		//    tbl_body += "<tr>"+tbl_row+"</tr>\n";
		//})
		//$("#site-table tbody").html(tbl_body);
	});
}
