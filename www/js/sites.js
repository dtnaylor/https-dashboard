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


function filter_all(sites) {
	return sites;
}

function filter_both(sites) {
	var new_sites = [];

	for (i=0; i < sites.length; i++) {
		if (sites[i]["availability"] == 'both') {
			new_sites.push(sites[i]);
		}
	}

	return new_sites;
}


function set_site_list_filter(filter) {
	Storage.set('site-list-filter', filter);
	location.reload();
}

function load_table(filter) {

	// highlight the correct filter button and pick filter function
	var filter_func = null;
	$("#btn-filter-all").removeClass('active');
	$("#btn-filter-both").removeClass('active');
	if (filter == "filter-all") {
		$("#btn-filter-all").addClass('active');
		filter_func = filter_all;
	} else if (filter == "filter-both") {
		$("#btn-filter-both").addClass('active');
		filter_func = filter_both;
	}


	// reload site list with new filter
	$.getJSON(get_summary_json_path(), function(data) {
		/*
		 * Site URL list
		 */

		$('#site-table').dynatable({
		  writers: {
		    _rowWriter: ulWriter
		  },
		  dataset: {
		    records: filter_func(data["sites"])
		  }
		});
		var dynatable = $('#site-table').data('dynatable');
		
		dynatable.paginationPerPage.set(100); // Show 100 records per page
		dynatable.process(true);  // true means don't change URL so back changes table
		


		//var tbl_body = "";
		//$.each(data["sites"], function() {
		//    var tbl_row = "";
		//	tbl_row += "<td><a href=\"profile.html?site=" + this["Site"] + "\">" + this["Site"] + "</a></td>";
		//    tbl_body += "<tr>"+tbl_row+"</tr>\n";
		//})
		//$("#site-table tbody").html(tbl_body);
	});
}


/* 
 * MAIN
 */
function main() {
	var filter = "filter-all";
	if (Storage.exists('site-list-filter')) {
		filter = Storage.get('site-list-filter');
	}
	load_table(filter);
}
