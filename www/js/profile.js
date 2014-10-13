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
function make_pie_chart(id, title, data, tooltip_postfix) {
    $(id).highcharts({
        chart: {
            plotBackgroundColor: null,
            plotBorderWidth: null,
            plotShadow: false,
			margin: [25, 25, 40, 25],
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
function load_object_type_breakdown(profile_dir, user_agent, metric, stacking) {
	// Get the path to the site's JSON profile
	var params = getSearchParameters();
	if (!params.hasOwnProperty("site")) return -1;

	$.getJSON(get_profile(profile_dir, user_agent, params["site"]), function(data) {
		/*
		 * Object Type Bars
		 */
		if (metric == 'count') {
			var series = dicts_to_stacked_bar_data([data["http-profile"]["num-objects-by-type"],
													data["https-profile"]["num-objects-by-type"]]);
			var ylabel = stacking == 'normal' ? 'Number of Objects' : 'Percent of Objects';
			make_stacked_bar('#object-types', null, ylabel, 'objects', stacking, ['HTTP', 'HTTPS'], series);
		} else if (metric == 'size') {
			var series = dicts_to_stacked_bar_data([data["http-profile"]["num-bytes-by-type"],
													data["https-profile"]["num-bytes-by-type"]]);
			var ylabel = stacking == 'normal' ? 'Number of Bytes' : 'Percent of Bytes';
			make_stacked_bar('#object-types', null, ylabel, 'bytes', stacking, ['HTTP', 'HTTPS'], series);

		}
		
		/*
		 * Object Type Pie
		 */
		//obj_type_data = dicts_to_pie_data(data["http-profile"]["num-objects-by-type"],
		//									data["https-profile"]["num-objects-by-type"]);
		//make_pie_chart('#http-object-types', 'HTTP Site', obj_type_data[0], 'objects');
		//make_pie_chart('#https-object-types', 'HTTPS Site', obj_type_data[1], 'objects');

	});
}






/* 
 * MAIN
 */
function main(profile_dir, user_agent) {
	var params = getSearchParameters();
	if (!params.hasOwnProperty("site")) return -1;

	$.getJSON(get_profile(profile_dir, user_agent, params["site"]), function(data) {

		/*
		 * Site URL
		 */
		document.getElementById("site-url").innerHTML = data["base-url"];

		/*
		 * Site thumbnail
		 */
		document.getElementById("site-thumbnail").src = get_thumbnail(profile_dir, user_agent, params["site"]);


		/*
		 * Bar charts
		 */
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
                data: [data["http-profile"]["num-objects"], data["http-profile"]["num-bytes"]/1000000.0, data["http-profile"]["num-hosts"], data["http-profile"]["num-tcp-handshakes"]],
            }, {
                name: 'HTTPS',
                data: [data["https-profile"]["num-objects"], data["https-profile"]["num-bytes"]/1000000.0, data["https-profile"]["num-hosts"], data["https-profile"]["num-tcp-handshakes"]],
            }]
        });





		/*
		 * HTTP Protocol Counts Pie
		 */
    	$('#http-protocol-counts').highcharts({
    	    chart: {
    	        plotBackgroundColor: null,
    	        plotBorderWidth: null,
    	        plotShadow: false,
				margin: [25, 25, 25, 25],
    	    },
    	    title: {
    	        text: 'HTTP Site'
    	    },
    	    tooltip: {
    		    pointFormat: '{series.name}: <b>{point.percentage:.1f}% ({point.y} objects)</b>'
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
    	        name: 'HTTP Site',
    	        data: data["http-protocol-counts"]
    	    }]
    	});


		/*
		 * HTTPS Protocol Counts Pie
		 */
    	$('#https-protocol-counts').highcharts({
    	    chart: {
    	        plotBackgroundColor: null,
    	        plotBorderWidth: null,
    	        plotShadow: false,
				margin: [25, 25, 25, 25],
    	    },
    	    title: {
    	        text: 'HTTPS Site'
    	    },
    	    tooltip: {
    		    pointFormat: '{series.name}: <b>{point.percentage:.1f}% ({point.y} objects)</b>'
    	    },
    	    plotOptions: {
    	        pie: {
    	            allowPointSelect: true,
    	            cursor: 'pointer',
    	            dataLabels: {
    	                enabled: false,
    	            },
					showInLegend: true,
    	        }
    	    },
    	    series: [{
    	        type: 'pie',
    	        name: 'HTTPS Site',
    	        data: data["https-protocol-counts"]
    	    }]
    	});

		/*
		 * Object origin details
		 */
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

	});

	load_object_type_breakdown(profile_dir, user_agent, 'count', 'normal');
}
