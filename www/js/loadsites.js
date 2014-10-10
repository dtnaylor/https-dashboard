/* ========================= COMMON HELPER FUNCTIONS ======================== */
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

function load_manifest(manifest_path) {
	$.getJSON(manifest_path, function(manifest) {
		Storage.set('manifest', manifest);
	});
}


/*
 * MAIN ENTRY POINT
 */
$(function () {
	var profile_dir = './profiles/';
	load_manifest(profile_dir + 'manifest.json');

	if (!Storage.exists('current-user-agent')) {
		Storage.set('current-user-agent', 'default');
	}

	// call page-specific main()
	main(profile_dir);
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
function main(profile_dir) {
	$.getJSON(profile_dir + 'summary.json', function(data) {
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
