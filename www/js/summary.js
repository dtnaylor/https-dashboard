/*
 * MAIN
 */
function main() {
	load_basic_stats('sort-alpha');
	load_protocol_counts('http', 'sort-alpha');
	load_protocol_counts('https', 'sort-alpha');

	$.getJSON(get_summary_json_path(), function(data) {
		/*
		 *  Protocol availability
		 */
    	$('#availability-pie-chart').highcharts({
    	    chart: {
    	        plotBackgroundColor: null,
    	        plotBorderWidth: null,
    	        plotShadow: false,
				margin: [25, 25, 25, 25],
    	    },
    	    title: {
    	        text: 'HTTPS Support'
    	    },
    	    tooltip: {
    		    pointFormat: '<b>{point.percentage:.1f}% ({point.y} sites)</b>'
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
    	        data: data["availability"]
    	    }],
        	credits: {
        	    enabled: false
        	}
    	});
	});
}

function load_basic_stats(sort) {
	var basic_stats = ["num_objects", "num_mbytes", "num_tcp_handshakes", "num_hosts"];
	var highlightBG = false;
	basic_stats.forEach(function(stat) {
		var bgcolor = highlightBG ? "#F0F8FF" : "#ffffff";
		highlightBG = !highlightBG;

		load_basic_stat(stat, sort, bgcolor);
		load_basic_stat_diff(stat, sort, bgcolor);
	});
}

function load_protocol_counts(site, sort) {
	$.getJSON(get_summary_json_path(), function(data) {
		/*
		 * protocol count stack plots
		 */
		$(function () {
			var id = '#' + site + '-site-counts';
			var key = site + '_site_protocol_counts';
    	    $(id).highcharts({
    	        chart: {
    	            type: 'area'
    	        },
    	        title: {
    	            text: site.toUpperCase() + ' Sites'
    	        },
    	        xAxis: {
					categories: data[key]["url"][sort],
    	            tickmarkPlacement: 'on',
					labels: {
						enabled: false
					},
    	            title: {
    	                enabled: false
    	            }
    	        },
    	        yAxis: {
    	            title: {
    	                text: 'Number of Objects'
    	            },
    	        },
    	        tooltip: {
    	            shared: true,
    	            valueSuffix: ' objects'
    	        },
    	    	plotOptions: {
    	    	    area: {
						stacking: 'normal',
    	    	        marker: {
    	    	            enabled: false,
    	    	            symbol: 'circle',
    	    	            radius: 2,
    	    	            states: {
    	    	                hover: {
    	    	                    enabled: true
    	    	                }
    	    	            }
    	    	        }
    	    	    }
    	    	},
    	        series: [{
    	            name: 'HTTP Objects',
    	            data: data[key]["HTTP"][sort]
    	        }, {
    	            name: 'HTTPS Objects',
    	            data: data[key]["HTTPS"][sort]
    	        }]
    	    });
    	});

	});
}



var ylabels = new Array();
ylabels["num_objects"] = "Number of Objects";
ylabels["num_tcp_handshakes"] = "Number of TCP Connections";
ylabels["num_mbytes"] = "Total Size (MB)";
ylabels["num_hosts"] = "Number of Hosts";

function load_basic_stat(stat, sort, bgcolor) {
	$.getJSON(get_summary_json_path(), function(data) {
    	$('#'+stat).highcharts({
    	    chart: {
    	        type: 'area',
				backgroundColor: bgcolor,
    	    },
    	    title: {
    	        text: ylabels[stat]
    	    },
    	    xAxis: {
				categories: data[stat]["url"][sort],
    	        tickmarkPlacement: 'on',
				labels: {
					enabled: false
				},
    	        title: {
    	            enabled: false
    	        }
    	    },
    	    yAxis: {
    	        title: {
    	            text: ylabels[stat]
    	        },
    	    },
    	    tooltip: {
    	        shared: true,
    	        //valueSuffix: ' objects'
    	    },
    	    plotOptions: {
    	        area: {
    	            marker: {
    	                enabled: false,
    	                symbol: 'circle',
    	                radius: 2,
    	                states: {
    	                    hover: {
    	                        enabled: true
    	                    }
    	                }
    	            }
    	        },
				series: {
            	    point: {
            	        events: {
            	            click: function () {
								window.location.href = 'profile.html?site=' + this.category;
            	            }
            	        }
            	    }
            	}
    	    },
    	    series: [{
    	        name: 'HTTP',
    	        data: data[stat]["HTTP"][sort]
    	    }, {
    	        name: 'HTTPS',
    	        data: data[stat]["HTTPS"][sort]
    	    }]
    	});
	});
}

/* subtract a2 from a1 element-wise */
function subtract_arrays(a1, a2) {
	if (a1.length != a2.length)
		return null;

	var result = new Array(a1.length);
	for (i = 0; i < a1.length; i++) {
		result[i] = a1[i] - a2[i];
	}

	return result;
}

function assign_threshold_colors(data, threshold) {
	var colored_data = new Array(data.length);
	for (i = 0; i < data.length; i++) {
		the_color = 'gray';
		if (data[i] > 0)
			the_color = '#3BA686';
		else if (data[i] < 0)
			the_color = '#E04946';

		colored_data[i] = {y:data[i], color:the_color};
	}

	return colored_data;
}

function load_basic_stat_diff(stat, sort, bgcolor) {
	$.getJSON(get_summary_json_path(), function(data) {
    	$('#'+stat+"-diff").highcharts({
    	    chart: {
    	        type: 'column',
				backgroundColor: bgcolor,
    	    },
    	    title: {
    	        text: 'Increase in HTTPS Page',
    	    },
    	    xAxis: {
				categories: data[stat]["url"][sort],
    	        tickmarkPlacement: 'on',
				labels: {
					enabled: false
				},
    	        title: {
    	            enabled: false
    	        }
    	    },
    	    yAxis: {
    	        title: {
    	            text: ylabels[stat]
    	        },
    	    },
    	    tooltip: {
				shared:'true',
                formatter:function(a,b,c){
					var s = '';
					$.each(this.points, function(i, point) {
                    	s += '<tspan style="font-size: 10px;">' + point.x + '</tspan><br/><b>HTTPS-HTTP:</b> ' + point.y;
					});
                    return s;
                },
    	    },
			legend: {
				enabled: false,
			},
    	    plotOptions: {
    	        area: {
    	            marker: {
    	                enabled: false,
    	                symbol: 'circle',
    	                radius: 2,
    	                states: {
    	                    hover: {
    	                        enabled: true
    	                    }
    	                }
    	            }
    	        },
				series: {
            	    point: {
            	        events: {
            	            click: function () {
								window.location.href = 'profile.html?site=' + this.category;
            	            }
            	        }
            	    }
            	}
    	    },
    	    series: [{
    	        name: 'HTTPS-HTTP',
    	        data: assign_threshold_colors(subtract_arrays(data[stat]["HTTPS"][sort], data[stat]["HTTP"][sort]), 0),
    	    }],
        	credits: {
        	    enabled: false
        	}
    	});
	});
}
