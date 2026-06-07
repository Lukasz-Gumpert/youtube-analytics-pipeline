<p>
  <img src="youtube-analytics-pipeline\assets\image-1.png" width="150" alt='python'/>
  <img src="youtube-analytics-pipeline\assets\image-2.png" width="150" alt='powerbi'/>
  <img src="youtube-analytics-pipeline\assets\image-3.png" width="150" alt='google cloud'/>
  <img src="youtube-analytics-pipeline\assets\image-4.png" width="150" alt='github actions'/>
</p>

# youtube-analytics-pipeline
An end-to-end Data Engineering and Business Intelligence pipeline that automates daily extraction of performance metrics from a YouTube channel via **YouTube APIs**, orchestrates data transformation with **Python (Pandas)**, updates a cloud data store (**Google Sheets**), and delivers advanced audience insights through a custom **Power BI** dashboard.

The entire workflow runs automatically on a daily schedule using **GitHub Actions**.

>**Portfolio Publication Terms:** This dashboard was developed as a pro-bono/barter solution for an active content creator. In exchange for implementing the automated ETL engine for free, the client granted full permission to publish the architecture publicly without an NDA (Non-Disclosure Agreement).


## 1. Core ETL Engine (Python & YouTube APIs) [tarot_youtube_data.py](youtube-analytics-pipeline\tarot_youtube_data.py)
![Python](https://img.shields.io/badge/python-3670A0?style=for-the-badge&logo=python&logoColor=ffdd54)
![Pandas](https://img.shields.io/badge/pandas-%23150458.svg?style=for-the-badge&logo=pandas&logoColor=white)
![Google Cloud](https://img.shields.io/badge/GoogleCloud-%234285F4.svg?style=for-the-badge&logo=google-cloud&logoColor=white)

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

Every time the pipeline runs, it reads the date column in Google Sheet. If it finds that data for the current date has already been uploaded, it skips that day entirely. This ensures that even if the script runs multiple times on the same day, it will never create duplicate rows or mess up historical metrics.

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
## 2. Cloud Automation & CI/CD (GitHub Actions) [daily.yml](youtube-analytics-pipeline\daily.yml)
![GitHub Actions](https://img.shields.io/badge/github%20actions-%232671E5.svg?style=for-the-badge&logo=github-actions&logoColor=white)

The entire ETL pipeline is fully automated using a GitHub Actions CI/CD workflow.

Instead of running the script manually, a configured cron job wakes up an isolated Ubuntu container every day at 22:55 UTC (23:55 Polish Time). The virtual environment automatically checks out the repository, sets up Python 3.11, installs the required dependencies, and builds secure authentication files on the fly before executing the data extraction.

### Zero-Trust Security Configuration

To keep the channel completely safe and production-ready, no private credentials, API keys, or Google OAuth tokens are saved in clear text files inside the repository.

Instead, the workflow leverages GitHub Encrypted Secrets. Sensitive data blocks (like API_KEY, CHANNEL_ID, and the entire JSON content for Google Service Accounts) are safely injected directly into the cloud container environment dynamically at runtime. This allows the repository to remain completely Public for portfolio presentation without exposing any private business data.

## 3. Business Intelligence & Data Modeling (Power BI) [tarot_dashboard](youtube-analytics-pipeline\tarot_dashboard.pbix)
![Power BI](https://img.shields.io/badge/Power_BI-F2C811?style=for-the-badge&logo=power-bi&logoColor=black)
![DAX](https://img.shields.io/badge/DAX-%232196F3.svg?style=for-the-badge&logo=microsoft&logoColor=white)

### Client Constraints & Visual Identity ("Stellar Analytics")
To meet the client's strict branding requirements, the entire user interface was custom-engineered to seamlessly match the visual identity and atmosphere of their active YouTube channel:

<img src="youtube-analytics-pipeline\assets\dash-01.jpg" alt='dashboard main page'>

* **Brand Consistency:** Moved away from standard corporate business templates to match the specific artistic niche of the client's brand.
* **Background Theme:** Deep space midnight blue (`#0C0F26`) mixed with soft dark tones to enhance screen readability and replicate the channel's banner graphics.
* **Accent Palette:** Metallic Gold (`#D4AF37`) for critical Key Performance Indicators (KPIs) and primary highlights, paired with warm Cream (`#F5F5DC`) for secondary text metrics to maintain an elegant, high-contrast feel.
* **User-Centric Layout:** Navigation slicers are grouped on the left-hand side, keeping historical trend charts and structural performance matrices clean and central for the client's daily operational reviews.

### Phase 1: Advanced Power Query ETL & Schema Preparation
Before mapping out relationships, the raw, multidimensional streams imported from Google Sheets underwent an intensive data-cleansing and reshaping process within **Power Query (M Language)**. This step was critical to ensure absolute type safety, optimize data compression, and prepare the tables for relational modeling.

<img src="youtube-analytics-pipeline\assets\power-query-01.jpg" alt='dashboard transform data'>

* **Strict Type Enforcement & Standardization:** 
  * Converted mixed timestamp and text strings into standardized, native `Date` formats across all historical tables (`daily_summary`, `geo_history`, etc.).
  * Explicitly cast all numerical performance metrics (views, likes, comments, watch time) into strict integers (`Int64.Type`).

* **Text Cleansing & ID Extraction:** 
  * Cleaned messy categorical dimensions by removing string anomalies, spaces, and formatting artifacts. 
  * Extracted clean, raw tracking identifiers to prepare columns for precise cross-table relationships.

* **Missing Data & Null Value Handling:** 
  * Applied conditional replacements to substitute empty text fields or `null` values with unified fallback descriptions (e.g., transforming blank traffic sources or missing regions into `OTHER_UNKNOWN`).
  * Replaced missing numerical payloads with `0` to prevent calculation gaps during DAX time-intelligence evaluations.

* **Granularity Alignment:** 
  * Separated high-level channel snapshots from deeply nested video-level metrics, creating a clean logical split between overall operational performance and specific content engagement statistics.

### Phase 2: Relational Data Modeling & Galaxy Schema Architecture
With multiple independent fact tables capturing channel performance metrics at different levels of granularity, a standard single-fact Star Schema was insufficient. Instead, the analytical engine was engineered using a **Galaxy Schema (Fact Constellation Architecture)**, where a centralized dimension filters multiple co-existing fact tables.

<img src="youtube-analytics-pipeline\assets\power-query-02.jpg" alt='dashboard transform data'>

#### The Relational Topology
The architecture strictly segregates metrics from context to avoid data redundancy, circular dependencies, and cross-filtering ambiguity:

* **Analytical Fact Tables (Data Ingestion Layers):**

  * `daily_summary` – High-level core channel tracking (views, watch time, subscribers balance).
   * `v_performance` – Granular daily log tracking metrics (likes, comments, views) per individual video. This table features a dual-date architectural design to support multi-perspective time analysis:
  * `geo_history`, `traffic_history`, `devices_history`, `audience_history` – Daily snapshot aggregates for structural categorical slicing.
* **Shared Dimension Tables (The Analytical Context):**
  * `Date` – The master calendar table serving as the structural backbone of the model.
* **Isolated Calculation Layer:**
  * `_key_measures` – A dedicated, decoupled container deployed exclusively for organizing DAX business logic, keeping fact schemas clean and lightweight.

#### Centralized Time-Intelligence & Date Table Logic

Since the pipeline fetches data daily via automated API scripts, any temporary connection drop or lag could cause gaps in the timeline. A centralized, continuous `Date` table was built to act as the single source of truth for time, ensuring all charts and trends display correctly.

* **Unidirectional Relationships (One-Way Filters):** 
Filters flow strictly from the `1` side (the `Date` table) to the `*` side (all Fact tables). This keeps data filtering predictable and allows Power BI's internal database engine (**VertiPaq**) to process queries instantly, preventing slow report loading times.

* **Active vs. Inactive Relationships (Role-Playing Dimension):** The `v_performance` table contains two different dates, which required two separate connections to the central `Date` table:
  * *Active Relationship (Solid Line):* Links the calendar to `snapshot_date` to track daily channel changes and historical metrics.
  * *Inactive Relationship (Dotted Line):* Links the calendar to `published_at` (the video release date). This setup allows for custom lifecycle analysis (e.g., tracking a video's growth from the exact day it was published) by dynamically activating this second path using the DAX `USERELATIONSHIP` function – all without duplicating tables or cluttering the model.

### Phase 3: Advanced DAX Engineering & Report Sheet Architecture

To transform raw, transactional API logs into an automated, high-performance executive cockpit, a robust semantic calculation layer was developed within the `_key_measures` container. The DAX (Data Analysis Expressions) architecture completely decouples visual elements from the ingestion tables using strict context transition overrides, custom time-intelligence logic, and explicit relationship activations.

Rather than relying on basic aggregates, this layer engineers specialized KPI matrices and statistical benchmarks completely unavailable within native YouTube Studio, mapped across six dedicated core sheets.


#### Sheet 1: Home Dashboard (Macro Community Footprint)

<img src="youtube-analytics-pipeline\assets\dash-01.gif" alt="Home Dashboard" style="margin-bottom: 15px; margin-top: 5px">

The **Home** interface serves as the primary executive command center, providing immediate cross-metric validation across core platform signals: Subscribers, Total Watch Time, Engagement, and Retention (APV).

* **Algorithmic Trend & Floor Benchmarking:** The dashboard features two crucial visual baselines. A calculated Linear Regression Trendline (red dashed line) highlights structural momentum, while a static Performance Baseline (yellow dashed line) tracks the historical minimum operational floor. This lets you immediately check if daily acquisition loops are tracking above or below historical channel standards.

* **The Total Engagement Index:** To quantify active community loyalty, this measure runs row-by-row iteration over the performance records, heavily weighting high-effort user interactions (comments) over low-effort clicks (likes):

```dax
Engagement Score = 
SUMX(
    'v_performance',
    'v_performance'[likes] * 1.0 + 'v_performance'[comments] * 2.0
)
```

<br clear="left"/>

---

#### Sheet 2: Reach Analysis (Granular Video Volume Rankings)

<img src="youtube-analytics-pipeline\assets\dash-02.gif" alt="Reach Dashboard" style="margin-bottom: 15px; margin-top: 5px">

The **Reach** sheet moves away from timeseries to focus entirely on publication scale, using sorted horizontal bar matrix layouts to rank performance across individual video titles.

* **Non-Native Cross-Granularity KPIs:** This layout isolates dynamic metrics like *Avg Views per Video*, *% Views Share*, and *Total Watch Time (EMW)*. 

* **Dynamic Statistical Mean Evaluation:** Features a dynamic **Average View Line** (white dashed vertical benchmark) that recalculates automatically based on the selected date slicer and format filters (Long-form vs. Short). This instantly flags exactly which topics or video formats drove impression volume significantly above the channel's running average.

<br clear="left"/>

---

#### Sheet 3: Engagement Profile (Interaction Ratio Analysis)

<img src="youtube-analytics-pipeline\assets\dash-03.gif" alt="Engagement Dashboard" style="margin-bottom: 15px; margin-top: 5px">

The **Engagement** interface isolates structural interaction intensity, sorting content by its raw capacity to trigger viewer feedback and relationship building.

* **Interactive Target Benchmarking:** Maps out specific video titles against a custom **Engagement Target Floor** (set at 5.00%, represented by the white vertical dashed benchmark). 
* **Algorithmic Feedback Loop:** By filtering content via the format parameters, this layout isolates content strategies that successfully drive audience investment. This provides an immediate data-driven feedback loop for thumbnail, title, and topic validation.

```dax
Engagement Rate (ER) = 
VAR LatestSnapshot = CALCULATE(MAX('v_performance'[snapshot_date]), ALL('Date'))

-- 1. Total interactions (Likes + Comments) while preserving strict filter context rules
VAR TotalInteractions = 
    CALCULATE(
        [Total Likes Gained] + [Total Comments],
        KEEPFILTERS('v_performance'[snapshot_date] = LatestSnapshot),
        USERELATIONSHIP('Date'[Date], 'v_performance'[published_at])
    )

-- 2. Total views volume while preserving strict filter context rules
VAR TotalViewsSnapshot = 
    CALCULATE(
        SUM('v_performance'[views]),
        KEEPFILTERS('v_performance'[snapshot_date] = LatestSnapshot),
        USERELATIONSHIP('Date'[Date], 'v_performance'[published_at])
    )

RETURN
DIVIDE(TotalInteractions, TotalViewsSnapshot, 0)
```

<br clear="left"/>

---

#### Sheet 4: Retention Dynamics (APV Performance Modeling)

<img src="youtube-analytics-pipeline\assets\dash-04.gif" alt="Retention Dashboard" style="margin-bottom: 15px; margin-top: 5px">

Audience retention is the single most critical factor for algorithmic distribution. The **Retention** sheet ranks videos by **APV (Average Percentage Viewed)** to isolate exact quality thresholds and content drop-off points.

* **Skew-Resistant Weighted Retention:** Standard platform averages can be heavily skewed by short-form formats (Shorts) with massive completion rates. To prevent this from masking long-form retention issues, the calculation layer deploys a true **Weighted View Percentage** calculated directly inside the current filter context:
```dax
Weighted View % = 
DIVIDE(
    SUMX('v_performance', 'v_performance'[views] * 'v_performance'[average_view_percentage]),
    SUM('v_performance'[views]),
    0
)
```

<br clear="right"/>

---

#### Sheet 5: Performance Analysis (Temporal Upload Optimization)

<img src="youtube-analytics-pipeline\assets\dash-05.jpg" alt="Performance Dashboard" style="margin-bottom: 15px; margin-top: 5px">

The **Performance** tab maps publication habits against actual consumption spikes across a standard weekly matrix (**Day of Week**).

* **Multi-Granular Time Cross-Analysis:** Top bar visual tracks the raw *Number of Publications* segmented by format (Long-form vs. Short), while the bottom matrix charts raw *Views accumulated* on those specific days.

* **Scheduling Efficiency Matrix:** This dual-chart logic helps creators spot scheduling gaps. For example, it exposes mismatches where high-volume upload days (like Tuesdays) might be underperforming compared to high-velocity audience windows on days with lower upload volume (like Fridays).

<br clear="left"/>

---

#### Sheet 6: GEO Analytics (International Market Penetration)

<img src="youtube-analytics-pipeline\assets\dash-06.jpg" alt="GEO Dashboard" style="margin-bottom: 15px; margin-top: 5px">

The **GEO** sheet provides necessary market isolation, filtering out domestic baseline data to expose international expansion opportunities.

* **Domestic Signal Cleansing:** Formatted explicitly as **Top 5 Countries (excl. Poland) by Views**, this interface strips away domestic traffic to isolate the channel's secondary growth layers (currently: DE, GB, IT, NL, US).

* **Context-Preserved Tracking with Trendlines:** The timeseries line chart uses advanced context handling to layer a **Linear Regression Trendline** (red dashed line) and a **Running Median Floor** (white dashed line) over international traffic. This allows creators to verify if localized search optimization or foreign-language dubbing is successfully building a stable, long-term audience base abroad.

```dax
Average Percentage Viewed (APV) = 
VAR LatestSnapshot = CALCULATE(MAX('v_performance'[snapshot_date]), ALL('Date'))
RETURN
CALCULATE(
    DIVIDE(
        SUMX('v_performance', 'v_performance'[views] * 'v_performance'[average_view_percentage]),
        SUM('v_performance'[views]),
        BLANK()
    ) / 100,
    KEEPFILTERS('v_performance'[snapshot_date] = LatestSnapshot),
    USERELATIONSHIP('Date'[Date], 'v_performance'[published_at])
)
```

## 4. Automation, Infrastructure & Repository Topology

###  CI/CD Orchestration via GitHub Actions

To completely eliminate manual intervention, the data harvesting lifecycle is fully automated using an isolated orchestration container. A configured GitHub Actions runner instantiates a headless virtual server on a rigid daily cadence.

```yaml
name: Daily YouTube Data

on:
  schedule:
    - cron: "55 22 * * *"   # 23:55 czasu PL (UTC+1)
  workflow_dispatch:

jobs:
  run-script:
    runs-on: ubuntu-latest

    steps:
      - name: Checkout repository
        uses: actions/checkout@v4

      - name: Set up Python
        uses: actions/setup-python@v5
        with:
          python-version: "3.11"

      - name: Install dependencies
        run: |
          python -m pip install --upgrade pip
          pip install -r requirements.txt

      - name: Create credentials files from secrets
        # Dodajemy zabezpieczenie ' ', aby uniknąć problemów z formatowaniem JSON
        run: |
          echo '${{ secrets.GSHEETS_CREDENTIALS }}' > credentials.json
          echo '${{ secrets.CLIENT_SECRET_JSON }}' > client_secret.json
          echo '${{ secrets.TOKEN_JSON }}' > token.json

      - name: Run script
        env:
          # Przekazujemy wszystkie potrzebne zmienne środowiskowe
          API_KEY: ${{ secrets.API_KEY }}
          CHANNEL_ID: ${{ secrets.CHANNEL_ID }}
        run: python tarot_youtube_data.py
```

* **Container Initialization:** Provisions an ubuntu-latest runtime environment.

* **Environment Stabilization:** Checks out the production branch and builds a static Python 3.11 virtualization wrapper via actions/setup-python@v5.

* **Dependency Saturation:** Upgrades pip and installs all required production packages using the repository's native requirements.txt manifest.

* **Dynamic Token Synthesis:** Safely decrypts and injects GitHub Encrypted Secrets directly into the runner filesystem to build three core authorization assets (credentials.json, client_secret.json, and token.json) on the fly, avoiding structural JSON formatting breaks.

* **Execution Loop:** Dispatches the primary execution engine (tarot_youtube_data.py) while passing critical authorization keys (API_KEY, CHANNEL_ID) securely via system environment variables.

### Production Project Topology
The directory layout enforces a strict decoupling of project assets, core execution scripts, and orchestration workflows, mapped exactly to the repository environment:

```
youtube-analytics-pipeline/
├── assets/                          # Embedded visual documentation layer
│   ├── dash-01.gif                  # Home dashboard visual capture
│   ├── dash-01.jpg                  # Home dashboard static presentation screen
│   ├── dash-02.gif                  # Reach analysis layout
│   ├── dash-03.gif                  # Engagement profiling sheet
│   ├── dash-04.gif                  # Retention dynamics visualization
│   ├── dash-05.jpg                  # Temporal publication matrix
│   ├── dash-06.jpg                  # International market GEO map
│   ├── image-1.png                  # Python official technology brand asset
│   ├── image-2.png                  # Microsoft Power BI product logo
│   ├── image-3.png                  # Google Cloud Platform enterprise identity
│   ├── image-4.png                  # GitHub Actions workflow automation icon
│   ├── power-query-01.jpg           # Raw data schema extraction checkpoint
│   └── power-query-02.jpg           # Power Query M-Engine ETL data transformation sequence
├── daily.yml                        # CI/CD workflow template (for reference)
├── .gitignore                       # Strict production security configuration mask
├── README.md                        # Master project documentation
├── tarot_dashboard.pbix             # Production Power BI dashboard
└── tarot_youtube_data.py            # Primary Python ETL engine (Extraction, Pandas Transformation)

```
### Zero-Trust Directory Protection (.gitignore)

To maintain absolute production security and allow public exposure of the source code for engineering review, a multi-tier exclusionary .gitignore file was integrated. This block guarantees that private authorization parameters, operational session files, and operating system junk records can never be accidentally staged or committed to public version control.

```
*credentials*.json
*secret*.json
*.env
client_secrets.json
.token_storage/

# Python Compilation & Dependency Caches
__pycache__/
*.py[cod]
*$py.class
.venv/
venv/
ENV/
pip-log.txt
pip-delete-this-directory.txt

# Local Machine Operational Metadata & OS Artefacts
.DS_Store
Thumbs.db
ehthumbs.db
.desktop
.idea/
.vscode/
*.pbix.user
```


## 5. Challenges, Lessons Learned & Future Roadmap

### The Ultimate Challenge: Delivering an End-to-End Production System
This project was a major milestone for me. It was the first time I built a complete data solution completely from scratch—handling everything from raw API integration, through cloud automation, to final business intelligence dashboard design. 

Operating under real-world client constraints meant that the pipeline couldn't just work "locally" on my machine; it had to be 100% stable, fully automated, and production-ready for daily business use. Working with the YouTube API was a completely new environment for me, and turning unstructured video platforms logs into a structured business data store brought several unexpected, critical challenges that I had to troubleshoot and solve step-by-step:

* **Challenge 1: Breaking Through API Payload Limitations**
  * *The Problem:* As the client's video library grew, passing hundreds of video identifiers simultaneously into the YouTube Analytics API triggered strict URL size limitations and broke the pipeline with `400 Bad Request` errors.
  * *The Solution:* Instead of letting the script crash, I engineered a dynamic indexing window in Python. I designed a batching mechanism that automatically slices the global collection of video IDs into manageable chunks of 200 items, processes them in parallel, and safely merges them back using Pandas.
* **Challenge 2: The Multi-Perspective Date Trap (DAX Logic)**
  * *The Problem:* During the Power BI dashboard implementation, I realized that analyzing standard daily channel performance (`snapshot_date`) alongside individual video lifecycles based on their upload day (`published_at`) created data filtering conflicts and slowed down report performance. 
  * *The Solution:* I restructured the relational model into a **Galaxy Schema** and established an inactive relationship between the Fact table and the Master Calendar. I then forced the evaluation engine to dynamically wake up the correct filtering path exactly when needed by leveraging advanced DAX context modifiers via `USERELATIONSHIP` and `KEEPFILTERS`.

### Current Developments (Active Optimization)
The project is actively maintained, and I am currently using it to push my data engineering skills further:
* **Dynamic Spreadsheet Sharding:** To prevent the Google Sheets storage from hitting maximum cell capacity limits as historical logs accumulate, I am currently developing a script routine that will automatically split and partition target tables based on the **Current Year and Month**.

### Future Infrastructure Roadmap
* **Migration to PostgreSQL:** While Google Sheets works perfectly as a lightweight cloud layer for the client's current scale, the ultimate goal is full infrastructure maturity. I plan to refactor the Python ETL engine to bypass spreadsheets entirely and stream normalized transactional records directly into a hosted **PostgreSQL** relational database for superior query performance, strict schema enforcement, and advanced SQL modeling options.

