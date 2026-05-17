# youtube-analytics-pipeline
Automated ETL pipeline using Python and GitHub Actions to fetch, transform, and sync YouTube Analytics data with Google Sheets for custom Power BI dashboards.

<p>
  <img src="youtube-analytics-pipeline\assets\image-1.png" width="150" alt='python'/>
  <img src="youtube-analytics-pipeline\assets\image-2.png" width="150" alt='powerbi'/>
  <img src="youtube-analytics-pipeline\assets\image-3.png" width="150" alt='google cloud'/>
  <img src="youtube-analytics-pipeline\assets\image-4.png" width="150" alt='github actions'/>
</p>

# youtube-analytics-pipeline
Automated ETL pipeline using Python and GitHub Actions to fetch, transform, and sync YouTube Analytics data with Google Sheets for custom Power BI dashboards.

### Project is divided into two conceptual parts:

- **Scenario 1: Sales Data Generator:**
A Make.com scenario responsible for populating the Google Sheet, simulating a dynamic CRM/ERP system with fresh, realistic sales transactional data (including calculated profit and cost metrics).

- **Scenario 2: AI Sales Intelligence & Notification:** The core workflow that consumes the generated sales data, uses Google Gemini AI for in-depth analysis and report generation, and automatically formats and distributes the final summary via Gmail.
