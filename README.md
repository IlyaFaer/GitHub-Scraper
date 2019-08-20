# Github-Scraper

The scraper automatically builds and updates issues and PRs tables. It reads issues from given list of repositories, groups them into sheets (each repo linked with specific sheet), and builds Google Sheet Document.

![image](http://i68.tinypic.com/1jb5ec.png)

**Attention!**  
Do not change table architecture manually without updating scraper code! Columns, which intended for manual filing: Priority, Work status, Task, Opened, Comment. Do not redact any other values!  

**Columns and order**  
Column preferences (possible values, width, name, aligning) can be set while creating *title row*. You can add colors to columns with data validation. Issues in table are ordered by repository name, project name and issue number  

**Updating**  
Every hour scraper makes request to GitHub to get issues/PRs list. If new issues have been created, scraper will add them into the table with *Priority* 'New'. If some issues have been closed, scraper will make their number grey.  

**Repositories names and labels**  
You can specify short name for specific repo and meaningful labels in source code. Both will be shown in specific columns.  

**PR autodetection**  
To make scrapper autodetect PRs, use GitHub keywords "Towards", "Closes", "Fixes" in public PRs and "IPR" in internals to make link from PR's body to original issue. Scrapper will use this links to fill "Public PR" and "Internal PR" fields in related issues.  

**PR color**  
Public PR's number can be colored. Every color has it's meaning:  
Gold - PR was created by not team member (team members specified in configurations)  
Red - PR had been closed  
Violet - PR had been merged  

**Assignee**  
In configuration file you can specify team members. If any member assigned issue, his name will be shown in Assignee column. If issue was assigned by someone else, you'll see "Other" in Assignee column.  

**Future features**  
* Statistics row
* Tracking changes during week (merging, creating PR's, etc.)
* Tracking review approvement
