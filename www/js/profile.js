/*
 * HELPER FUNCTIONS
 */
function getSearchParameters() {
      var prmstr = window.location.search.substr(1);
      return prmstr != null && prmstr != "" ? transformToAssocArray(prmstr) : {};
}

function transformToAssocArray( prmstr ) {
    var params = {};
    var prmarr = prmstr.split("&");
    for ( var i = 0; i < prmarr.length; i++) {
        var tmparr = prmarr[i].split("=");
        params[tmparr[0]] = tmparr[1];
    }
    return params;
}


function pretty(string)
{
	var map = {
		'xml':'XML',
		'css':'CSS',
		'html':'HTML',
		'json':'JSON',
	};

	if (string in map)
		return map[string];
	else
    	return string.charAt(0).toUpperCase() + string.slice(1);
}

function dict_to_pie_data(dict) {
	pie_data = [];
	for (key in dict) {
		pie_data.push([pretty(key), dict[key]]);
	}
	return pie_data;
}

/* makes two pie data arrays with the same data labels
   (e.g., to make sure the same label gets the same color in 2 charts) */
function dicts_to_pie_data(dict1, dict2) {
	pie_data = [[],[]];  // we give back two arrays

	for (key in dict1) {
		pie_data[0].push([pretty(key), dict1[key]]);
		if (key in dict2)
			pie_data[1].push([pretty(key), dict2[key]]);
		else
			pie_data[1].push([pretty(key), 0]);
	}
	
	// now get any leftover keys in dict 2 but not 1
	for (key in dict2) {
		if (!(key in dict1)) {
			pie_data[1].push([pretty(key), dict2[key]]);
			pie_data[0].push([pretty(key), 0]);
		}
	}
	return pie_data;
}



/*
 * PLOTTING FUNCTIONS
 */
function make_pie_chart(id, title, data, tooltip_postfix, margin, series_name) {
	margin = margin ? margin : [25, 25, 40, 25];

    $(id).highcharts({
        chart: {
            plotBackgroundColor: null,
            plotBorderWidth: null,
            plotShadow: false,
			margin: margin,
        },
        title: {
            text: title
        },
        tooltip: {
    	    pointFormat: '{series.name}: <b>{point.percentage:.1f}% ({point.y} ' + tooltip_postfix + ')</b>'
        },
        plotOptions: {
            pie: {
                allowPointSelect: true,
                cursor: 'pointer',
                dataLabels: {
                    enabled: false,
                    format: '<b>{point.name}</b>: {point.percentage:.1f} %',
                    style: {
                        color: (Highcharts.theme && Highcharts.theme.contrastTextColor) || 'black'
                    }
                },
				showInLegend: true,
            }
        },
        series: [{
            type: 'pie',
			name: series_name,
            data: data,
        }]
    });
}


function dicts_to_stacked_bar_data(dicts) {
	var segments = [];  // color segment names
	var series = [];

	// figure out the complete list of categories
	for (i=0; i < dicts.length; i++) {
		// grab segment names if we don't have them already
		for (var key in dicts[i]) {
			if (segments.indexOf(key) == -1)
				segments.push(key);
		}
	}

	// get values
	for (i=0; i < segments.length; i++) {
		var data = [];
		for (j=0; j < dicts.length; j++) {
			if (segments[i] in dicts[j])
				data.push(dicts[j][segments[i]]);
			else
				data.push(0);
		}
		
		series.push({ "name":pretty(segments[i]), "data":data});
	}

	return series;
}

/*
 * categories are the colored bar segments
 * series is an array of associative arrays w/ name and data entries
 */
function make_stacked_bar(id, title, ylabel, tooltip_postfix, stacking, categories, series) {
	$(function () {
        $(id).highcharts({
            chart: {
                type: 'bar'
            },
            title: {
                text: title
            },
            xAxis: {
                categories: categories
            },
            yAxis: {
                min: 0,
                title: {
                    text: ylabel
                }
            },
			tooltip: {
				followPointer: true,
    	    	pointFormat: '{series.name}: <b>{point.y} ' + tooltip_postfix + ' ({point.percentage:.1f}%)</b>'
			},
            legend: {
                reversed: true
            },
            plotOptions: {
                series: {
                    stacking: stacking
                }
            },
                series: series,
        });
    });
}


/*
 * metric is either 'count' or 'size'
 */
function load_object_type_breakdown(metric, stacking) {
	// Get the path to the site's JSON profile
	var params = getSearchParameters();
	if (!params.hasOwnProperty("site")) return -1;

	$.getJSON(get_profile_path(params["site"]), function(data) {
		/*
		 * Object Type Bars
		 */

		// if the site doesn't support HTTP or HTTPS, make an empty dict for that protocol
		var http_num_objects_by_type = data["http-profile"] ? data["http-profile"]["num-objects-by-type"] : {};
		var https_num_objects_by_type = data["https-profile"] ? data["https-profile"]["num-objects-by-type"] : {};
		var http_num_bytes_by_type = data["http-profile"] ? data["http-profile"]["num-bytes-by-type"] : {};
		var https_num_bytes_by_type = data["https-profile"] ? data["https-profile"]["num-bytes-by-type"] : {};

		if (metric == 'count') {
			var series = dicts_to_stacked_bar_data([http_num_objects_by_type,
													https_num_objects_by_type]);
			var ylabel = stacking == 'normal' ? 'Number of Objects' : 'Percent of Objects';
			make_stacked_bar('#object-types', null, ylabel, 'objects', stacking, ['HTTP', 'HTTPS'], series);
		} else if (metric == 'size') {
			var series = dicts_to_stacked_bar_data([http_num_bytes_by_type,
													https_num_bytes_by_type]);
			var ylabel = stacking == 'normal' ? 'Number of Bytes' : 'Percent of Bytes';
			make_stacked_bar('#object-types', null, ylabel, 'bytes', stacking, ['HTTP', 'HTTPS'], series);

		}
		
	});
}



/*
 * Attempt to load an image. If successful, set the image as the src of the
 * supplied image element. If not successful, hide the element_to_hide
 * (which is typically the image element or a container of the image element).
 */
// TODO: this doesn't fetch the image twice, does it?
function load_image_or_hide(image_url, image_element, element_to_hide) {
	var img = new Image();
	img.onload = function() {
		image_element.src = this.src;
		element_to_hide.style.visibility = 'visible';
		//element_to_hide.style.display = 'inline';
	};

	img.onerror = function() {
		element_to_hide.style.visibility = 'hidden';
		//element_to_hide.style.display = 'none';
	};

	img.src = image_url;
}





/* 
 * MAIN
 */
function main() {
	var params = getSearchParameters();
	if (!params.hasOwnProperty("site")) return -1;

	$.getJSON(get_profile_path(params["site"]), function(data) {

		/*
		 * Site URL
		 */
		document.getElementById("site-url").innerHTML = data["base-url"];

		/*
		 * Site thumbnails
		 */
		load_image_or_hide(get_thumbnail_path(params["site"], 'http'),
						   document.getElementById("http-site-thumbnail"),
						   document.getElementById("http-site-thumbnail-container"));

		load_image_or_hide(get_thumbnail_path(params["site"], 'https'),
						   document.getElementById("https-site-thumbnail"),
						   document.getElementById("https-site-thumbnail-container"));

		document.getElementById("http-screenshot-link").href = get_screenshot_path(params["site"], 'http');
		document.getElementById("https-screenshot-link").href = get_screenshot_path(params["site"], 'https');


		/*
		 * Bar charts
		 */
		// if the site doesn't support HTTP or HTTPS, make an empty array for that protocol
		var http_num_objects = data["http-profile"] ? data["http-profile"]["num-objects"] : [];
		var https_num_objects = data["https-profile"] ? data["https-profile"]["num-objects"] : [];
		var http_num_mbytes = data["http-profile"] ? data["http-profile"]["num-bytes"]/1000000.0 : [];
		var https_num_mbytes = data["https-profile"] ? data["https-profile"]["num-bytes"]/1000000.0 : [];
		var http_num_hosts = data["http-profile"] ? data["http-profile"]["num-hosts"] : [];
		var https_num_hosts = data["https-profile"] ? data["https-profile"]["num-hosts"] : [];
		var http_num_tcp_handshakes = data["http-profile"] ? data["http-profile"]["num-tcp-handshakes"] : [];
		var https_num_tcp_handshakes = data["https-profile"] ? data["https-profile"]["num-tcp-handshakes"] : [];

		$('#basic-stats').highcharts({
            chart: {
                type: 'bar'
            },
            title: {
                text: 'Basic Statistics'
            },
            xAxis: {
                categories: ['Number of Objects', 'Total Size (MB)', 'Number of Hosts', 'Number of Connections'],
                title: {
                    text: null
                }
            },
            yAxis: {
                min: 0,
                title: {
                    text: null
                }
            },
            plotOptions: {
                bar: {
                    dataLabels: {
                        enabled: true
                    }
                }
            },
            credits: {
                enabled: false
            },
            series: [{
                name: 'HTTP',
                data: [http_num_objects, http_num_mbytes, http_num_hosts, http_num_tcp_handshakes],
            }, {
                name: 'HTTPS',
                data: [https_num_objects, https_num_mbytes, https_num_hosts, https_num_tcp_handshakes],
            }]
        });





		/*
		 * HTTP Protocol Counts Pie
		 */
		if (data["http-protocol-counts"]) {
			make_pie_chart('#http-protocol-counts',  // element id
						   'HTTP Site',  // title
						   data["http-protocol-counts"],  // data
						   'objects',  // tooltip postfix
						   [25, 25, 25, 25],  // margin
						   'HTTP Site'  // series name
			);
		}


		/*
		 * HTTPS Protocol Counts Pie
		 */
		if (data["https-protocol-counts"]) {
			make_pie_chart('#https-protocol-counts',  // element id
						   'HTTPS Site',  // title
						   data["https-protocol-counts"],  // data
						   'objects',  // tooltip postfix
						   [25, 25, 25, 25],  // margin
						   'HTTPS Site'  // series name
			);
		}

		/*
		 * Object origin details
		 */
		console.log(data["object-details"]);
		var tbl_body = "";
		$.each(data["object-details"], function() {
		    var tbl_row = "";
			tbl_row += "<td style=\"overflow:hidden; white-space:nowrap; \" title=\""+ this["filename"] + "\">" + this["filename"] + "</td>";

			if (this.hasOwnProperty("http-origin") && this["http-origin"] != "") {
				// Display a colored 'HTTP' or 'HTTPS' badge
				var label = "";
				if (this["http-protocol"] == "http")
					label = "<span class=\"label label-default\">HTTP</span>";
				else
					label = "<span class=\"label label-success\">HTTPS</span>";
				label += "&nbsp;&nbsp;&nbsp;";

				tbl_row += "<td style=\"overflow:hidden; white-space:nowrap; padding-left: 20px;\" title=\""+ this["http-origin"] + "\">" + label + this["http-origin"] + "</td>";
			} else {
				tbl_row += "<td></td>";
			}

			if (this.hasOwnProperty("https-origin") && this["https-origin"] != "") {
				// Display a colored 'HTTP' or 'HTTPS' badge
				var label = "";
				if (this["https-protocol"] == "http")
					label = "<span class=\"label label-danger\">HTTP</span>";
				else
					label = "<span class=\"label label-success\">HTTPS</span>";
				label += "&nbsp;&nbsp;&nbsp;";

				tbl_row += "<td style=\"overflow:hidden; white-space:nowrap; padding-left: 20px;\" title=\""+ this["https-origin"] + "\">" + label + this["https-origin"] + "</td>";
			} else {
				tbl_row += "<td></td>";
			}

		    tbl_body += "<tr>"+tbl_row+"</tr>\n";
		})
		$("#object-details-table tbody").html(tbl_body);

	})
	.fail(function() {  // getting JSON failed
		error_alert = document.getElementById("error-alert");
		error_alert.innerHTML = '<strong>Oops!</strong> We don\'t have data for <i>' + params["site"] + '</i> for the selected crawl date and user agent.';
		error_alert.style.display = "inherit";
	});

	load_object_type_breakdown('count', 'normal');
}
