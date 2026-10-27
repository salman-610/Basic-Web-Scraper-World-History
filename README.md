Basic Web Scraper – World History

A Python web scraping project featuring historical event extraction, date validation, event categorization, and duplicate detection using Requests and Beautiful Soup.

Project Overview

This project scrapes historical events from Wikipedia's annual event pages for the years 1865–1890. It extracts relevant event information, classifies events into categories, and performs data-quality checks before displaying the results in the terminal.

Features

- Scrapes historical events from Wikipedia.
- Extracts event titles, dates, years, and categories.
- Uses Requests to retrieve webpages.
- Uses Beautiful Soup to parse HTML content.
- Categorizes events into predefined categories.
- Validates dates and required fields.
- Flags potential duplicate and similar event titles.
- Generates data-quality reports and identifies entries requiring manual review.
- Displays results in a readable terminal format.

Technologies Used

- Python
- Requests
- Beautiful Soup
- Regular Expressions
- MySQL connector module (supporting project database code)

Project Structure

```text
Basic-Web-Scraper-World-History/
├── main.py
├── database.py
├── README.md
├── requirements.txt
├── .gitignore
└── .env.example
```

Installation and Usage

1. Clone the repository:

   
   git clone https://github.com/salman-610/Basic-Web-Scraper-World-History.git
   

2. Navigate to the project directory:

   
   cd Basic-Web-Scraper-World-History
   

3. Install the dependencies:

   
   pip install -r requirements.txt
   

4. Run the scraper:

   
   python main.py
   

Current Configuration

- Year range: 1865–1890
- Data source: Wikipedia annual event pages
- Execution mode: Preview only
- Database writes: Disabled

The scraper displays extracted events and data-quality reports without modifying database records.

Learning Objectives

- Understand web scraping with Requests and Beautiful Soup.
- Learn the basics of HTML parsing and data extraction.
- Practice regular expressions and date validation.
- Implement basic event categorization and duplicate detection.
- Present extracted information in a readable format.

Disclaimer

This project is intended for educational purposes. Extracted data and automated classifications may require manual verification. Please follow Wikipedia's applicable terms and access guidelines when scraping.

Author

Salman A