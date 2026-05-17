<p>
  <img src="youtube-analytics-pipeline\assets\image-1.png" width="150" alt='python'/>
  <img src="youtube-analytics-pipeline\assets\image-2.png" width="150" alt='powerbi'/>
  <img src="youtube-analytics-pipeline\assets\image-3.png" width="150" alt='google cloud'/>
  <img src="youtube-analytics-pipeline\assets\image-4.png" width="150" alt='github actions'/>
</p>

# youtube-analytics-pipeline
An end-to-end Data Engineering and Business Intelligence pipeline that automates daily extraction of performance metrics from a YouTube channel via **YouTube APIs**, orchestrates data transformation with **Python (Pandas)**, updates a cloud data store (**Google Sheets**), and delivers advanced audience insights through a custom **Power BI** dashboard.

The entire workflow runs automatically on a daily schedule using **GitHub Actions**.


## 1. Core ETL Engine (Python & YouTube APIs)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Pandas](https://img.shields.io/badge/pandas-%23150458.svg?style=for-the-badge&logo=pandas&logoColor=white)



This core component orchestrates secure authentication, processes massive multi-dimensional data requests from YouTube APIs, transforms unstructured nested payloads using **Pandas**, and maintains strict data synchronization with cloud storage.

### Pagination & Batching API Queries
When fetching detailed performance charts for growing video libraries, passing hundreds of tracking identifiers simultaneously can trigger massive `400 Bad Request` or URL payload size limitations from the YouTube API. 

To solve this, the pipeline segments the global video collection into chunks of 200 items using an iterative indexing window, dynamically making parallel requests and combining the snapshots back into a unified data structure.

```python
# Video collection chunking routine from data_extractor.py
vids_list = df_videos['video_id'].tolist()
batch_size = 200 
all_perf_data = []

for i in range(0, len(vids_list), batch_size):
    batch = vids_list[i : i + batch_size]
    ids_filter = f"video=={','.join(batch)}"
    
    # Executing modular queries over the active chunk boundaries
    df_b = run_analytics_query(start_of_channel, yesterday, "views,likes,comments,subscribersGained", "video", filters=ids_filter)
    df_r = run_analytics_query(start_of_channel, yesterday, "estimatedMinutesWatched,averageViewDuration,averageViewPercentage", "video", filters=ids_filter)
    
    if not df_b.empty:
        merged_batch = pd.merge(df_b, df_r, on="video", how="left")
        all_perf_data.append(merged_batch)
```

### Data Transformation & Pivoting
A dedicated transformation step was built using Pandas. The engine automatically replaces missing or empty information with clear labels, removes duplicate rows, and reshapes (pivots) the data from a long list into a clean, wide table structure where each category gets its own column.

```python
def pivot_data(df, dimension_col, metrics_col):
    if df is None or df.empty: return pd.DataFrame()
    
    # Fill in blank or missing labels to keep data clean and consistent
    df[dimension_col] = df[dimension_col].replace(['', None], 'OTHER_UNKNOWN')
    df = df.drop_duplicates(subset=['day', dimension_col])
    
    # Flip rows into columns (Pivot) to make the data easy for Power BI to read
    pivoted = df.pivot(index='day', columns=dimension_col, values=metrics_col).reset_index()
    pivoted.columns.name = None 
    
    # Fill any empty cells with 0 and convert metrics to clean integers
    cols_to_fix = [c for c in pivoted.columns if c != 'day']
    pivoted[cols_to_fix] = pivoted[cols_to_fix].fillna(0).astype(int)
    return pivoted
```
### Smart Data Synchronization & Deduplication

The pipeline connects directly to Google Sheets using the gspread library and a secure Google Service Account. To keep the cloud database clean and accurate, the script performs an automatic safety check before uploading any new data.

Every time the pipeline runs, it reads the date column in your Google Sheet. If it finds that data for the current date has already been uploaded, it skips that day entirely. This ensures that even if the script runs multiple times on the same day, it will never create duplicate rows or mess up your historical metrics.

```python
# Cloud commitment and snapshot date validation block
existing_dates = ws.col_values(1)
new_rows = []

for _, row in df_clean.iterrows():
    new_date = str(row.iloc[0]).strip()
    
    # Deduplication boundary check: prevents multiple daily executions from inflating data
    if new_date not in existing_dates:
        formatted_row = [str(row.get(h, 0)) for h in headers]
        new_rows.append(formatted_row)
        
if new_rows:
    ws.append_rows(new_rows, value_input_option='USER_ENTERED')

```
## 2. Cloud Automation & CI/CD (GitHub Actions)
![Google Cloud](https://img.shields.io/badge/GoogleCloud-%234285F4.svg?style=for-the-badge&logo=google-cloud&logoColor=white)
![GitHub Actions](https://img.shields.io/badge/github%20actions-%232671E5.svg?style=for-the-badge&logo=github-actions&logoColor=white)

The entire ETL pipeline is fully automated using a GitHub Actions CI/CD workflow.

Instead of running the script manually, a configured cron job wakes up an isolated Ubuntu container every day at 22:55 UTC (23:55 Polish Time). The virtual environment automatically checks out the repository, sets up Python 3.11, installs the required dependencies, and builds secure authentication files on the fly before executing the data extraction.

### Zero-Trust Security Configuration

To keep the channel completely safe and production-ready, no private credentials, API keys, or Google OAuth tokens are saved in clear text files inside the repository.

Instead, the workflow leverages GitHub Encrypted Secrets. Sensitive data blocks (like API_KEY, CHANNEL_ID, and the entire JSON content for Google Service Accounts) are safely injected directly into the cloud container environment dynamically at runtime. This allows the repository to remain completely Public for portfolio presentation without exposing any private business data.

## 2. Business Intelligence & Data Modeling
![Power Bi](https://img.shields.io/badge/Power_BI-F2C811?style=for-the-badge&logo=power-bi&logoColor=black)