World History Event Explorer

Project Overview

World History Event Explorer is a Python-based web scraping project that collects historical event information from Wikipedia's yearly event pages.

The application allows users to select a year, review the collected events, and explore them through different categories. It also checks the extracted information and highlights entries that may need manual verification.

Main Features

- Year Selection: Choose a year between 2020 and 2026 to explore its historical events.
- Automated Data Collection: Retrieve event information from the corresponding Wikipedia page.
- Event Date Detection: Identify dates mentioned alongside historical events.
- Category Classification: Organize collected events into categories such as wars, natural disasters, human-caused disasters, and terrorism or attacks.
- Data Quality Checks: Identify incomplete, unclear, or potentially duplicated entries.
- Review Notes: Highlight records that may require additional verification.
- Interactive Navigation: Browse category-wise results or return to the year selection menu.

Technologies Used

| Technology | Purpose |
|---|---|
| Python | Application development and data processing |
| Requests | Retrieving webpage content |
| BeautifulSoup | Extracting information from HTML |
| Regular Expressions | Detecting and processing date patterns |
| MySQL | Planned database storage |

Project Structure


world_history_web_scraper/
│
├── main.py
├── database.py
├── requirements.txt
├── README.md
└── .gitignore


Installation and Setup

1. Clone the Repository


git clone https://github.com/salman-610/Basic-Web-Scraper-World-History.git


2. Open the Project Folder


cd Basic-Web-Scraper-World-History


3. Create a Virtual Environment


py -m venv venv


4. Activate the Virtual Environment

For Windows PowerShell:


.\venv\Scripts\Activate.ps1


5. Install Dependencies


py -m pip install -r requirements.txt


If the dependency file is empty, install the required packages:


py -m pip install requests beautifulsoup4 mysql-connector-python


Running the Application

Start the program using:


py main.py


Enter a year between 2020 and 2026 when prompted.

How the Application Works

1. The user enters a year.
2. The application constructs the corresponding Wikipedia yearly events page URL.
3. Python Requests retrieves the webpage.
4. BeautifulSoup processes the HTML and extracts event entries.
5. The application attempts to identify event dates and assign categories.
6. Validation checks identify incomplete or similar records that may need review.
7. A summary displays the collection results.
8. The user selects a category to view its associated events.
9. The user can return to the year selection menu or exit the application.

Event Categories

Events are grouped according to the information extracted from the source page. Categories currently include:

- War
- Natural Disaster
- Human-Caused Disaster
- Terrorism / Attack
- Needs Review

The category counts depend on the selected year's webpage and the extraction results.

Database Information

The project includes a `database.py` module prepared for connecting to a local MySQL database named `world_history_db`.

The current application runs in preview mode. Database storage is not yet integrated into the active scraping workflow.

For database authentication, the project reads the MySQL password from the `MYSQL_PASSWORD` environment variable rather than storing credentials directly in the source code.

Limitations

- The collected information depends on the content and structure of Wikipedia pages.
- Some event dates may not be detected automatically.
- Category assignment is based on text-processing rules and may require manual correction.
- Similarity checks may identify entries that need further inspection.
- The current version displays extracted information without saving the results to MySQL.

Future Improvements

- Integrate MySQL storage into the year-wise scraping workflow.
- Add more historical years.
- Improve event date extraction and category classification.
- Provide better duplicate detection.
- Develop a graphical interface for easier browsing.
- Add search and filtering options.

Project Purpose

This project demonstrates the practical use of Python for webpage retrieval, HTML parsing, text processing, information classification, and data validation through a historical-event collection application.