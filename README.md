# GitHub Scraper (beta, active development paused)

GitHub Scraper automatically builds issues and PRs tables in Google Sheets documents, and periodically updates them.
* **Multirepo**: track several repositories within one sheet and several sheets within one spreadsheet
* **Constructible**: tweak table structure, coloring and filling functions
* **Adaptive**: change your preferences and add new repos/sheets without restarting Scraper
* **Ready to go**: avoid tweaking Scraper and just use completely workable [examples](https://github.com/IlyaFaer/GitHub-Scraper/tree/master/scraper/examples)

![image](https://github.com/IlyaFaer/GitHub-Scraper/blob/master/GitHubScraperPreview.png?raw=true)

**Setup**  
To build your tables and start tracking repositories you need:
* [Enable Google Sheets API](https://developers.google.com/sheets/api/quickstart/python#step_1_turn_on_the)  
* Install required packages with *requirements.txt*  
In *scraper* folder:
* Create *config.py* and set your tables configurations with it (see [config_example.py](https://github.com/IlyaFaer/GitHub-Scraper/blob/master/scraper/examples/config_example.py))
* Create *fill_funcs.py* and set your filling functions with it (see [fill_funcs_example.py](https://github.com/IlyaFaer/GitHub-Scraper/blob/master/scraper/examples/fill_funcs_example.py))
* Create and run *main.py* (see [main_example.py](https://github.com/IlyaFaer/GitHub-Scraper/blob/master/scraper/examples/main_example.py))

Scraper will build tables and start tracking specified repositories. First filling can take time, but subsequent updates are faster (~80% faster), as Scraper is processing only recently updated PRs and issues. You can check filling progress in *logs.txt*. If any error occur, its traceback will be shown in *logs.txt* as well.

**Structure, auto and manual filling**  
You can tweak table filling in *fill_funcs.py*, leaving some columns for manual-only use (for example "Comment"), setting ignoring and  cleanup rules, sorting, coloring, etc., in any way you like.  

Scraper uses *config.py* as a source of preferences. Before update it reloads *config.py* module, so you can change preferences without stoping Scraper - add new sheets, repositories, rules, etc.  

**PR autodetection**  
To make Scraper detect PRs, use GitHub keywords "Towards", "Closes", "Fixes" to make link from PRs body to the original issue. Scraper will use these links to fill "Public PR" field in the related issues.  

**Archive**  
By default, Scraper moves issues with `Done` status into Archive sheet and stops tracking them. This feature allows to avoid overwhelming sheets with non-active data. The behavior can be changed by setting `ARCHIVE_SHEET` configurations and `to_be_archived` filling function.  

**Credentials**  
On a first Scraper launch you'll have to authenticate on Google Sheets API (you'll see appropriate popup-window) and on GitHub (with a console). On subsequent launches Scraper will use previous credentials without asking to enter them once again.

**Beta version disclaimer**  
Scraper is in a state of active development yet. Please, use Releases as the most stable versions, and feel free to open an issue in case of any problems.
