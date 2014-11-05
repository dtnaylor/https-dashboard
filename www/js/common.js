
/* ========================= COMMON HELPER FUNCTIONS ======================== */
/*
 * Wrapper for localStorage
 */
var Storage = {
	set: function(key, value) {
		key = 'edu.cmu.cs.httpsdashboard.' + key;
		localStorage[key] = JSON.stringify(value);
	},

	get: function(key) {
		key = 'edu.cmu.cs.httpsdashboard.' + key;
		return localStorage[key] ? JSON.parse(localStorage[key]) : null;
	},

	exists: function(key) {
		key = 'edu.cmu.cs.httpsdashboard.' + key;
		return localStorage[key] != null;
	},
};

/*
 * Load a JSON file and store in local storage
 */
function load_json(json_path, key) {
	// using .ajax so call is synchronous
	$.ajax({
	  url: json_path,
	  dataType: 'json',
	  async: false,
	  success: function(data) {
		Storage.set(key, data);
	  }
	});
}

/***** BEGIN FILE PATH FUNCTIONS *****/

/*
 * Return the path to the current profile directory
 */
function get_selected_dir() {
	profile_dir = Storage.get('profile-dir');
	crawl_date = Storage.get('selected-crawl-date');
	user_agent = Storage.get('selected-user-agent');

	return profile_dir + '/' 
		 + crawl_date + '/'
		 + user_agent;
}

/*
 * Return the path to the main manifest
 */
function get_main_manifest_path() {
	profile_dir = Storage.get('profile-dir');
	return profile_dir + '/main-manifest.json';
}

/*
 * Return the path to the crawl manifest for the selected date
 */
function get_crawl_manifest_path() {
	profile_dir = Storage.get('profile-dir');
	crawl_date = Storage.get('selected-crawl-date');
	return profile_dir + crawl_date + '/crawl-manifest.json';
}

/*
 * Return the path to the profile for a given site
 */
function get_profile_path(site) {
	return get_selected_dir() + '/site_profiles/' + site + ".json";
}

/*
 * Return the path to the summary JSON for a crawl
 */
function get_summary_json_path() {
	return get_selected_dir() + '/summary.json';
}

/*
 * Return the path to the thumbnail for a given site
 */
function get_thumbnail_path(site, protocol) {
	return get_selected_dir() + '/site_screenshots/' + site + '-' 
		+ protocol + '_thumb.png';
}

/*
 * Return the path to the screenshot for a given site
 */
function get_screenshot_path(profile_dir, user_agent, site, protocol) {
	return get_selected_dir() + '/site_screenshots/' + site + '-' 
		+ protocol + '.png';
}

/***** END FILE PATH FUNCTIONS *****/

/*
 * Set the displayed user agent name
 */
function set_crawl_date_display(crawl_date) {
	crawl_manifest = Storage.get('crawl-manifest');
	display = document.getElementById("crawl-date-display");
	display.innerHTML = crawl_date; // TODO: pretty format?
}

/*
 * Set the displayed user agent name
 */
function set_user_agent_display(user_agent) {
	crawl_manifest = Storage.get('crawl-manifest');
	display = document.getElementById("user-agent-display");
	display.innerHTML = crawl_manifest["user-agents"][user_agent]["name"];
}

/*
 * Change the selected crawl date and refresh the page.
 */
function change_crawl_date(crawl_date) {
	console.log('changing crawl_date to: ' + crawl_date);
	Storage.set('selected-crawl-date', crawl_date);
	set_crawl_date_display(crawl_date);

	// reload page data
	//$('#site-table-body').innerHTML = '';
	//var dynatable = $('#site-table').data('dynatable');
	//console.log(dynatable);
	//dynatable.records.resetOriginal();
	//document.getElementById("site-table-body").innerHTML = '';
	//main(Storage.get('profile-dir'), user_agent);

	// FIXME: something better
	location.reload();
	
}

/*
 * Change the user agent and refresh the page.
 * user_agent argument should be a key in the user-agents dict in crawl manifest
 */
function change_user_agent(user_agent) {
	console.log('changing user agent to: ' + user_agent);
	Storage.set('selected-user-agent', user_agent);
	set_user_agent_display(user_agent);

	// reload page data
	//$('#site-table-body').innerHTML = '';
	//var dynatable = $('#site-table').data('dynatable');
	//console.log(dynatable);
	//dynatable.records.resetOriginal();
	//document.getElementById("site-table-body").innerHTML = '';
	//main(Storage.get('profile-dir'), user_agent);

	// FIXME: something better
	location.reload();
	
}


/*
 * MAIN ENTRY POINT
 */
$(function () {
	//
	// DATA DIRECTORY
	//
	var profile_dir = './profiles/';
	Storage.set('profile-dir', profile_dir);



	//
	// LOAD MAIN MANIFEST
	//
	load_json(get_main_manifest_path(), 'main-manifest');

	// get last crawl date
	main_manifest = Storage.get('main-manifest');
	crawl_dates = main_manifest['dates']
	if (!Storage.exists('selected-crawl-date')) {
		// if there's no stored crawl date, pick most recent
		first_date = crawl_dates[0]
		Storage.set('selected-crawl-date', first_date);
	}
	set_crawl_date_display(Storage.get('selected-crawl-date'));

	// load crawl date menu
	crawl_date_menu = document.getElementById("crawl-date-menu");
	for (var i=0; i < crawl_dates.length; i++) {
		crawl_date = crawl_dates[i];
		crawl_date_menu.innerHTML =
			crawl_date_menu.innerHTML
			+ '<li><a href="javascript: change_crawl_date(\'' + crawl_date + '\');">' 
			+ crawl_date  // TODO: prettier format?
			+ '</a></li>';
	}



	//
	// LOAD CRAWL MANIFEST
	//
	load_json(get_crawl_manifest_path(), 'crawl-manifest');

	// load last user agent
	user_agents = Storage.get('crawl-manifest')['user-agents'];
	if (!Storage.exists('selected-user-agent')) {
		// if there's no stored user agent, pick a random one
		// TODO: crawl manifest should tell default user agent?
		for (var user_agent in user_agents) {
			Storage.set('selected-user-agent', user_agent);
			break;
		}
	}
	set_user_agent_display(Storage.get('selected-user-agent'));
	
	// load user agent menu
	user_agent_menu = document.getElementById("user-agent-menu");
	for (var user_agent in user_agents) {
		user_agent_menu.innerHTML =
			'<li><a href="javascript: change_user_agent(\'' + user_agent + '\');">' 
			+ user_agents[user_agent]['name'] 
			+ '</a></li>'
			+ user_agent_menu.innerHTML;
	}



	// call page-specific main()
	main();
});


/* ========================================================================== */
