# GitHub-Scraper (alpha)

GitHub-Scraper automatically builds issues and PRs tables in Google Sheets documents, and periodically updates them.
* **Multirepo**: track several repositories within one sheet and several sheets within one spreadsheet
* **Constructable**: tweak table structure, relations "repository-to-sheet" and filling functions
* **Adaptive**: change your preferences and add new repos and\or sheets without restarting the scraper
* **Ongoing**: continue filling on exceptions - scraper will log traceback into file without failing

![image](https://github.com/IlyaFaer/GitHub-Scraper/blob/master/GitHubScraperPreview.png?raw=true)

**Setup**  
To build your first tables and start tracking repositories you need:
* Steps 1 and 2 of [Google Sheets API Setup](https://developers.google.com/sheets/api/quickstart/python)
* Install [PyGitHub package](https://pygithub.readthedocs.io/en/latest/introduction.html)
* Create *loginpas.txt* file in scraper's folder and enter your GitHub login and password into it in format: `login/password`. No whitespaces or newlines needed
* Set your tables configurations in *config.py* file (or use standard)
* Set filling functions in *fill_funcs.py* file (or use standard)
* Run *main.py* - scraper will build tables and start tracking specified repositories. First filling after program start usually takes some time, but subsequent updates will be faster (~50% faster), as Scraper will be processing only recently updated PRs.

**Auto and manual filling**  
You can tweak spreadsheet filling by (re-)defining filling functions in *fill_funcs.py* file, leaving some columns for manual-only use (for example "Comment").

**Configurations**  
Scraper uses *config.py* file as a source of preferences. Before update it reloads *config.py* module, so you can change table's preferences without stoping scraper's main program. Configurations are set with several constants:
* TITLE - spreadsheet name
* UPDATE_PERIODICITY - duration of pause between updates in seconds
* SHEETS - spreadsheet preferences: list of sheets with their names, meaningful labels, lists of corresponding repositories and team lists
* COLUMNS - column names, style, data validation (with corresponding color for some values) and filling functions
* sort_func - function, which is used for sorting issues within sheet  

**Updating**  
At specified intervals scraper makes request to GitHub to get issues/PRs list. If new issues have been created, scraper will add them into the table with *Priority* 'New'. If some issues have been closed, scraper will make their number grey.  

**PR autodetection**  
To make scraper detect PRs, use GitHub keywords "Towards", "Closes", "Fixes" in public PRs and "IPR" in internals to make link from PR's body to original issue. Scrapper will use this links to fill "Public PR" and "Internal PR" fields in related issues.  

**PR color**  
Public PR's number may be colored. Colors has their meaning:  
Gold - PR was created by not team member  
Red - PR had been closed  
Violet - PR had been merged  

**Assignee**  
In *config.py* you can specify team members. If any member assigned issue, his login will be shown in Assignee column. If issue was assigned by someone else, you'll see "Other" in Assignee column.
