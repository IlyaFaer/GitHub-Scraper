# GitHub-Scraper (beta)

GitHub-Scraper automatically builds issues and PRs tables in Google Sheets documents, and periodically updates them.
* **Multirepo**: track several repositories within one sheet and several sheets within one spreadsheet
* **Constructible**: tweak table structure, relations "repository-to-sheet" and filling functions
* **Adaptive**: change your preferences and add new repos/sheets without restarting Scraper
* **Ready to go**: avoid tweaking Scraper and just use completely workable examples

![image](https://github.com/IlyaFaer/GitHub-Scraper/blob/master/GitHubScraperPreview.png?raw=true)

**Setup**  
To build your first tables and start tracking repositories you need:
* Steps 1 and 2 of [Google Sheets API Setup](https://developers.google.com/sheets/api/quickstart/python)
* Install [PyGitHub package](https://pygithub.readthedocs.io/en/latest/introduction.html)  
In *scraper* folder:
* Create *loginpas.txt* and enter your GitHub credentials into it in format: `login/password`
* Create *config.py* and set your tables configurations with it (see [config_example.py](https://github.com/IlyaFaer/GitHub-Scraper/blob/master/scraper/examples/config_example.py))
* Create *fill_funcs.py* and set your filling functions with it (see [fill_funcs_example.py](https://github.com/IlyaFaer/GitHub-Scraper/blob/master/scraper/examples/fill_funcs_example.py))
* Create and run *main.py* (see [main_example.py](https://github.com/IlyaFaer/GitHub-Scraper/blob/master/scraper/examples/main_example.py)) - Scraper will build tables and start tracking specified repositories. First filling after program start usually takes some time, but subsequent updates are faster (~80% faster), as Scraper is processing only recently updated PRs and issues.

If you're getting problems while filling, check *logs.txt* file for traceback, and feel free to create an issue.

**Auto and manual filling**  
You can tweak table filling in *fill_funcs.py*, leaving some columns for manual-only use (for example "Comment").

**Configurations**  
Scraper uses *config.py* as a source of preferences. Before update it reloads *config.py* module, so you can change preferences without stoping Scraper. Configurations are set with several constants:
* TITLE - spreadsheet name
* UPDATE_PERIODICITY - duration of a pause between updates in seconds
* SHEETS - spreadsheet preferences: list of sheets, meaningful labels, lists of corresponding repositories and teams
* COLUMNS - column names, style and data validation
* fill_funcs.sort_func - function for sorting issues within sheet  

**PR autodetection**  
To make Scraper detect PRs, use GitHub keywords "Towards", "Closes", "Fixes" to make link from PRs body to the original issue. Scrapper will use these links to fill "Public PR" field in the related issues.  
