/*
 * MAIN
 */
function main() {
	user_agents = Storage.get('crawl-manifest')['user-agents'];
	table = document.getElementById('user-agent-table');

	for (var user_agent in user_agents) {
		table.innerHTML +=
		'<tr>' +
			'<td>' + user_agents[user_agent]['name'] + '</td>' +
			'<td>' + user_agents[user_agent]['string'] + '</td>' +
		'</tr>';
	}

}
