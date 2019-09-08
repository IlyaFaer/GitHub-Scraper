# Github-Scraper

Github-Scraper automatically builds issues and PRs tables in Google Sheets documents, and periodically updates their data.

![image](https://cdn1.imggmi.com/uploads/2019/8/31/412b7ab2c12f86916559343125942f7d-full.png)

**Setup**  
To build your first tables and start tracking repositories you need:
* Steps 1 and 2 of [Google Sheets Setup](https://developers.google.com/sheets/api/quickstart/python). On a first run you'll have to authenticate in Google Sheets API.
* Install [PyGitHub package](https://pygithub.readthedocs.io/en/latest/introduction.html).
* Create *loginpas.txt* file in scraper's folder and enter your GitHub login and password into it in format: `login/password`. No whitespaces or newlines needed.
* Set your tables configurations in *config.py* file.
* Run *main.py* - scraper will build tables and start tracking specified repositories.

**Attention!**  
Do not change table architecture manually without updating scraper code! Columns, which intended for manual filing: Priority, Work status, Task, Opened, Comment. Do not redact any other values!  

**Configurations**  
Scraper uses *config.py* file as a source of preferences. Before update it reloads *config.py* module, so you can change table's preferences without stoping scraper's main program. Configurations are set with several constants:
* TITLE - spreadsheet name
* UPDATE_PERIODICITY - duration of pause between updates in seconds.
* SHEETS - spreadsheet preferences: list of sheets with their names, meaningful labels, lists of corresponding repositories and team list
* TRACKED_FIELDS - names of columns, that should be rewriten on every update
* COLUMNS - column preferences. In this structure you can set column name, width, data aligning and data validation (with corresponding color for some values)
* sort_func - function, which is used by scraper for sorting issues in sheet.  

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
In *config.py* you can specify team members. If any member assigned issue, his name will be shown in Assignee column. If issue was assigned by someone else, you'll see "Other" in Assignee column.  

**Future features**  
* Statistics row
* Tracking changes during week (merging, creating PR's, etc.)
* Tracking review approvement
