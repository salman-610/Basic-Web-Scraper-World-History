World History Web Scraper

Project Overview

World History Event Explorer is a Python-based web scraping application that collects historical event information from Wikipedia's yearly event pages.

The application allows users to select a year, retrieve historical events, explore categorized results, and identify records requiring further verification.

It demonstrates the practical application of Python web scraping, HTML parsing, text processing, data validation, duplicate detection, and MySQL database integration.

Key Features

- Year-Based Scraping: Retrieve historical event information for selected years between 2020 and 2026.
- Event Extraction: Parse yearly Wikipedia pages and extract historical event descriptions.
- Date Identification: Detect event dates using text-processing techniques.
- Category Classification: Organize events into predefined historical categories.
- Data Validation: Identify incomplete entries and records requiring manual verification.
- Duplicate Detection: Identify repeated and potentially similar event descriptions.
- Review Notes: Maintain validation notes for records requiring further inspection.
- Database Integration: Store processed event records in MySQL.
- Interactive Navigation: Browse extracted events through year-based and category-based menus.

Technologies Used

| Component | Technology |
|---|---|
| Programming Language | Python |
| Web Scraping | Requests |
| HTML Parsing | BeautifulSoup |
| Text Processing | Regular Expressions |
| Similarity Detection | difflib |
| Database | MySQL |
| Database Client | MySQL Workbench |
| Database Connector | MySQL Connector/Python |
| Development Environment | Visual Studio Code |

Project Structure

world_history_web_scraper/
│
├── main.py
├── database.py
├── database.sql
├── requirements.txt
├── README.md
└── .gitignore


Database Design

The application uses the 'world_history_db' database with the 'historical_events' table.

The table maintains the following information:

- 'id': Unique identifier for each record.
- 'event_title': Extracted historical event title or description.
- 'event_date': Identified event date, stored as text.
- 'event_year': Year associated with the historical event.
- 'category': Assigned historical event category.
- 'description': Optional additional event description.
- 'source_url': URL of the original source page.
- 'source_name': Name of the information source.
- 'scraped_at': Timestamp indicating when the record was stored.
- 'review_reason': Notes explaining why a record requires further verification.

The database structure is provided in 'database.sql' so that reviewers can initialize the required database independently of the developer's local environment.

A unique index on the event title prefix and event year helps prevent duplicate records. Additional indexes support year, category, and date-based queries.

When a new non-empty collection is saved for a selected year, the application replaces the existing records for that year. Records belonging to other years remain unchanged.

Setup and Execution

Prerequisites

- Python 3.8 or later.
- MySQL Server installed and running.
- MySQL Workbench or another MySQL client.
- Internet connectivity.
- A MySQL account with permission to create databases and tables.

1. Obtain the Project

Clone the repository and navigate to the project directory.

GitHub Repository:  
https://github.com/salman-610/Basic-Web-Scraper-World-History


git clone https://github.com/salman-610/Basic-Web-Scraper-World-History.git

cd Basic-Web-Scraper-World-History


2. Create a Virtual Environment

Create an isolated Python environment for the project.


py -m venv .venv


Activate the virtual environment:

.\.venv\Scripts\Activate.ps1

3. Install Dependencies

Install the required Python packages listed in 'requirements.txt'.

py -m pip install -r requirements.txt

4. Prepare the Database

1. Start MySQL Server.
2. Open MySQL Workbench and connect to your local MySQL instance.
3. Open the 'database.sql' file.
4. Execute the SQL statements.

This creates the 'world_history_db' database and the 'historical_events' table required by the application.

5. Configure Database Credentials

The application retrieves the MySQL password from the 'MYSQL_PASSWORD' environment variable.

Before executing the application, configure the password in Windows PowerShell:

$env:MYSQL_PASSWORD = "your_mysql_password"

Replace the placeholder with the password associated with your local MySQL account.

This configuration applies to the current PowerShell session. If you open a new terminal, configure the environment variable again before running the application.

Security Note: Database credentials should not be hardcoded in Python source files or committed to the GitHub repository.

6. Launch the Application

From the project root directory, execute:

py main.py

Enter a supported year when prompted to initiate the scraping process.

Application Workflow

The application retrieves the selected year's Wikipedia event page and processes the available event entries.

The extracted event descriptions undergo date identification, category classification, duplicate checks, and data validation. Records requiring further inspection are assigned review notes.

The processed collection is displayed through category-based navigation and stored in MySQL.

When the same year is scraped again, its existing records are replaced with the newly collected non-empty dataset. Records from other years are preserved.

Important Notes

- MySQL Server must be running before launching the application.
- The database must be initialized using 'database.sql'.
- A valid 'MYSQL_PASSWORD' environment variable is required.
- Internet connectivity is required to retrieve source webpage content.
- Date identification and category classification use rule-based processing and may require manual verification.
- The application depends on the availability and HTML structure of the source webpage.
- Similarity-based duplicate detection does not guarantee the identification of every possible duplicate.
- The project does not include the developer's local MySQL database or credentials.
- The '.venv' directory and sensitive configuration files should not be committed to the repository.
- The '.gitignore' file is provided to exclude local environment and other unnecessary files from version control.

Future Enhancements

- Extend historical coverage to additional years and information sources.
- Improve date extraction and event classification accuracy.
- Introduce advanced event search and filtering.
- Develop a graphical interface for historical event exploration.
- Expand database reporting and analytical capabilities.

Purpose of the Project

This project was developed to demonstrate how Python web scraping techniques can be integrated with text processing, data validation, and relational database operations to build a structured historical information collection system.

It provides practical experience with webpage retrieval, HTML parsing, regular expressions, similarity detection, Python database connectivity, and SQL operations.

Author
Salman