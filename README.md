World History Web Scraper

A Python-based web scraping project that gathers historical event information from Wikipedia's yearly events pages and organizes it for analysis and review.

Features

- Collect historical event entries from 2020 to 2026.
- Extract event titles and identify dates when possible.
- Classify events into categories such as wars, terrorism and attacks, natural disasters, and human-caused disasters.
- Detect potential duplicate entries and similar event titles.
- Identify records with missing dates or uncertain classifications.
- Perform data quality checks to support accurate historical data collection.
- Prepare structured event records for future database integration.

Technologies Used

-  Python  — scraping logic, text processing, and data validation
-  Requests  — retrieving webpage content
-  Beautiful Soup  — parsing HTML and extracting event information
-  MySQL  — database integration
-  Regular Expressions  — date extraction and text matching
-  Git and GitHub  — version control and project hosting

Project Structure


world_history_web_scraper/
├── main.py
├── database.py
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md


How It Works

1. Retrieves historical event pages from Wikipedia.
2. Extracts event entries from the relevant sections.
3. Cleans and processes the collected text.
4. Identifies dates and assigns categories using predefined rules.
5. Checks for possible duplicates, missing information, and ambiguous records.
6. Produces a summary of the collected data and entries requiring further review.

Data Quality and Validation

Historical event titles do not always contain enough information to determine an exact date or category automatically. The scraper flags uncertain records for manual review rather than assuming that every extracted value is correct.

Duplicate detection and event classification are rule-based, so their results should be checked before the data is used for further analysis.

Data Source

The project uses Wikipedia's yearly historical events pages as its primary scraping source.

Historical information collected by the scraper should be verified against reliable references before being treated as authoritative.

Future Enhancements

- Expand historical coverage beyond the current year range.
- Improve date extraction and event classification.
- Store validated historical records in MySQL.
- Develop a web interface for searching and exploring events.
- Add filters for event year and category.
- Provide interactive visualizations of historical events.

Author

Salman A
