
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
 * Load the manifest dictionary and put in local storage
 */
function load_manifest(manifest_path) {
	// using .ajax so call is synchronous
	$.ajax({
	  url: manifest_path,
	  dataType: 'json',
	  async: false,
	  success: function(data) {
		Storage.set('manifest', data);
	  }
	});
}

/*
 * Return the path to the profile for a given site
 */
function get_profile(profile_dir, user_agent, site) {
	return profile_dir + user_agent + '/site_profiles/' + site + ".json";
}

/*
 * Return the path to the thumbnail for a given site
 */
function get_thumbnail(profile_dir, user_agent, site, protocol) {
	return profile_dir + user_agent + '/site_screenshots/' + site + '-' 
		+ protocol + '_thumb.png';
}

/*
 * Return the path to the screenshot for a given site
 */
function get_screenshot(profile_dir, user_agent, site, protocol) {
	return profile_dir + user_agent + '/site_screenshots/' + site + '-' 
		+ protocol + '.png';
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
	console.log('changing user agent to: ' + user_agent);
	Storage.set('current-user-agent', user_agent);
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
	var profile_dir = './profiles/';
	Storage.set('profile-dir', profile_dir);  // TODO: something better?
	load_manifest(profile_dir + 'manifest.json');

	// load user agent menu
	user_agents = Storage.get('manifest')['user-agents'];
	user_agent_menu = document.getElementById("user-agent-menu");
	for (var user_agent in user_agents) {
		user_agent_menu.innerHTML =
			'<li><a href="javascript: change_user_agent(\'' + user_agent + '\');">' 
			+ user_agents[user_agent]['name'] 
			+ '</a></li>'
			+ user_agent_menu.innerHTML;
	}
	if (!Storage.exists('current-user-agent')) {
		// if there's no stored user agent, pick a random one
		// TODO: manifest should tell default user agent?
		for (var user_agent in user_agents) {
			Storage.set('current-user-agent', user_agent);
			break;
		}
	}
	set_user_agent_display(Storage.get('current-user-agent'));

	// call page-specific main()
	main(profile_dir, Storage.get('current-user-agent'));
});


/* ========================================================================== */
