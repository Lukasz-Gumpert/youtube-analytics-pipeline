import os
import re  # Niezbędne do wyciągania czasu trwania
import gspread
import pandas as pd
from datetime import datetime, date, timedelta
from googleapiclient.discovery import build
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request

# 1. CONFIG & AUTH
API_KEY = os.getenv("API_KEY")
CHANNEL_ID = os.getenv("CHANNEL_ID")
SERVICE_ACCOUNT_FILE = "credentials.json"
CLIENT_SECRET_FILE = "client_secret.json"
TOKEN_FILE = "token.json"
SHEET_NAME = "tarot_data"
SCOPES = [
    "https://www.googleapis.com/auth/yt-analytics.readonly", 
    "https://www.googleapis.com/auth/spreadsheets", 
    "https://www.googleapis.com/auth/youtube.readonly"
]

def get_services():
    creds = None
    if os.path.exists(TOKEN_FILE):
        creds = Credentials.from_authorized_user_file(TOKEN_FILE, SCOPES)
    if not creds or not creds.valid:
        if creds and creds.expired and creds.refresh_token:
            creds.refresh(Request())
        else:
            flow = InstalledAppFlow.from_client_secrets_file(CLIENT_SECRET_FILE, SCOPES)
            creds = flow.run_local_server(port=0, access_type='offline', prompt='select_account consent')
        with open(TOKEN_FILE, "w") as token:
            token.write(creds.to_json())
    return build("youtubeAnalytics", "v2", credentials=creds), build("youtube", "v3", developerKey=API_KEY)

analytics, youtube = get_services()

# 2. DEFINICJE FUNKCJI

def parse_duration(duration_str):
    """Zamienia format ISO 8601 (PT1M30S) na sekundy (int)."""
    hours = re.search(r'(\d+)H', duration_str)
    minutes = re.search(r'(\d+)M', duration_str)
    seconds = re.search(r'(\d+)S', duration_str)
    
    h = int(hours.group(1)) if hours else 0
    m = int(minutes.group(1)) if minutes else 0
    s = int(seconds.group(1)) if seconds else 0
    
    return h * 3600 + m * 60 + s

def get_channel_and_videos():
    ch_res = youtube.channels().list(part="statistics,contentDetails", id=CHANNEL_ID).execute()
    ch = ch_res["items"][0]
    yesterday_str = (date.today() - timedelta(days=1)).isoformat()
    
    df_channel = pd.DataFrame([{
        "date": yesterday_str, 
        "subscribers": int(ch["statistics"]["subscriberCount"]), 
        "total_views": int(ch["statistics"]["viewCount"]), 
        "total_videos": int(ch["statistics"]["videoCount"])
    }])
    
    uploads_id = ch["contentDetails"]["relatedPlaylists"]["uploads"]
    video_ids = []
    req = youtube.playlistItems().list(part="snippet", playlistId=uploads_id, maxResults=50)
    while req:
        res = req.execute()
        video_ids += [i["snippet"]["resourceId"]["videoId"] for i in res["items"]]
        if len(video_ids) >= 500: break
        req = youtube.playlistItems().list_next(req, res)

    videos = []
    for i in range(0, len(video_ids), 50):
        res = youtube.videos().list(part="snippet,statistics,contentDetails", id=",".join(video_ids[i:i+50])).execute()
        for v in res["items"]:
            dur_raw = v["contentDetails"].get("duration", "PT0S")
            dur_sec = parse_duration(dur_raw)
            v_type = "Short" if dur_sec <= 60 else "Long-form"
            
            videos.append({
                "video_id": v["id"], 
                "title": v["snippet"]["title"], 
                "published_at": v["snippet"]["publishedAt"][:10],
                "video_duration_sec": dur_sec,
                "video_type": v_type,
                "views_total": int(v["statistics"].get("viewCount", 0)), 
                "likes_total": int(v["statistics"].get("likeCount", 0)), 
                "comments_total": int(v["statistics"].get("commentCount", 0))
            })
    return df_channel, pd.DataFrame(videos)

def run_analytics_query(start_date, end_date, metrics, dimensions=None, sort=None, filters=None):
    try:
        res = analytics.reports().query(
            ids=f"channel=={CHANNEL_ID}", 
            startDate=start_date.isoformat(), 
            endDate=end_date.isoformat(), 
            metrics=metrics, 
            dimensions=dimensions, 
            sort=sort, 
            filters=filters,
            maxResults=1000
        ).execute()
        cols = [c["name"] for c in res["columnHeaders"]]
        rows = res.get("rows", [])
        return pd.DataFrame(rows, columns=cols)
    except Exception as e:
        print(f"Błąd raportu ({metrics}): {e}")
        return pd.DataFrame()

def pivot_data(df, dimension_col, metrics_col):
    if df is None or df.empty: return pd.DataFrame()
    df[dimension_col] = df[dimension_col].replace(['', None], 'OTHER_UNKNOWN')
    df = df.drop_duplicates(subset=['day', dimension_col])
    pivoted = df.pivot(index='day', columns=dimension_col, values=metrics_col).reset_index()
    pivoted.columns.name = None 
    cols_to_fix = [c for c in pivoted.columns if c != 'day']
    pivoted[cols_to_fix] = pivoted[cols_to_fix].fillna(0).astype(int)
    return pivoted

def send_to_sheets(to_overwrite, to_append):
    gc = gspread.service_account(filename=SERVICE_ACCOUNT_FILE)
    sh = gc.open(SHEET_NAME)
    
    for name, df in to_overwrite.items():
        if df is None or df.empty: continue
        try:
            ws = sh.worksheet(name)
            ws.clear()
            ws.update(range_name='A1', values=[df.columns.tolist()] + df.values.tolist())
            print(f"Nadpisano: {name}")
        except Exception as e:
            print(f"Błąd nadpisywania {name}: {e}")

    for name, df in to_append.items():
        if df is None or df.empty: continue
        try:
            try: 
                ws = sh.worksheet(name)
            except gspread.WorksheetNotFound:
                ws = sh.add_worksheet(title=name, rows="5000", cols="50")
                ws.update(range_name='A1', values=[df.columns.tolist()])
                ws = sh.worksheet(name)

            headers = ws.row_values(1)
            df_clean = df.fillna(0)
            new_columns = [col for col in df_clean.columns if col not in headers]
            if new_columns:
                for col in new_columns:
                    headers.append(col)
                ws.update(range_name='A1', values=[headers])

            existing_dates = ws.col_values(1)
            new_rows = []
            for _, row in df_clean.iterrows():
                new_date = str(row.iloc[0]).strip()
                if new_date not in existing_dates:
                    formatted_row = [str(row.get(h, 0)) for h in headers]
                    new_rows.append(formatted_row)
            
            if new_rows:
                ws.append_rows(new_rows, value_input_option='USER_ENTERED')
                print(f"Zsynchronizowano: {name}")
        except Exception as e: 
            print(f"Błąd w {name}: {e}")

# 3. WYKONANIE
if __name__ == "__main__":
    df_channel, df_videos = get_channel_and_videos()
    yesterday = date.today() - timedelta(days=1)
    # ZMIANA: Użyjemy wczorajszej daty jako daty snapshotu dla v_performance
    snapshot_date = yesterday.isoformat() 
    
    start_of_channel = date(2025, 12, 19)
    analysis_start = date.today() - timedelta(days=5) 
    analysis_end = date.today() - timedelta(days=2)

    vids_list = df_videos['video_id'].tolist()
    batch_size = 200 
    all_perf_data = []

    for i in range(0, len(vids_list), batch_size):
        batch = vids_list[i : i + batch_size]
        ids_filter = f"video=={','.join(batch)}"
        df_b = run_analytics_query(start_of_channel, yesterday, "views,likes,comments,subscribersGained", "video", filters=ids_filter)
        df_r = run_analytics_query(start_of_channel, yesterday, "estimatedMinutesWatched,averageViewDuration,averageViewPercentage", "video", filters=ids_filter)
        if not df_b.empty:
            merged_batch = pd.merge(df_b, df_r, on="video", how="left")
            all_perf_data.append(merged_batch)

    if all_perf_data:
        df_perf_combined = pd.concat(all_perf_data, ignore_index=True)
        df_v_perf = pd.merge(
            df_perf_combined, 
            df_videos[['video_id', 'title', 'published_at', 'video_duration_sec', 'video_type']], 
            left_on="video", right_on="video_id", how="left"
        )
        
        df_v_perf['snapshot_date'] = snapshot_date
        cols_order = ['snapshot_date', 'video', 'title', 'published_at', 'video_duration_sec', 'video_type', 
                      'views', 'estimatedMinutesWatched', 'averageViewDuration', 
                      'averageViewPercentage', 'likes', 'comments', 'subscribersGained']
        
        df_v_perf = df_v_perf[cols_order].sort_values(by="views", ascending=False)
    else:
        df_v_perf = pd.DataFrame()
    
    df_daily = run_analytics_query(analysis_start, analysis_end, "views,estimatedMinutesWatched,subscribersGained,subscribersLost", "day")
    
    if not df_daily.empty:
        df_daily['current_total_subs'] = int(df_channel['subscribers'].iloc[0])
        df_daily['current_total_views'] = int(df_channel['total_views'].iloc[0])
        df_daily['subs_net'] = df_daily['subscribersGained'].astype(int) - df_daily['subscribersLost'].astype(int)

    raw_geo_snapshot = run_analytics_query(start_of_channel, yesterday, "views", "country")
    if not raw_geo_snapshot.empty:
        raw_geo_snapshot['day'] = yesterday.isoformat()

    df_geo_pivoted = pivot_data(raw_geo_snapshot, 'country', 'views')
    df_devices_pivoted = pivot_data(run_analytics_query(analysis_start, analysis_end, "views", "day,deviceType"), 'deviceType', 'views')
    df_subs_pivoted = pivot_data(run_analytics_query(analysis_start, analysis_end, "views", "day,subscribedStatus"), 'subscribedStatus', 'views')
    df_traffic_pivoted = pivot_data(run_analytics_query(analysis_start, analysis_end, "views", "day,insightTrafficSourceType"), 'insightTrafficSourceType', 'views')

    send_to_sheets(
        to_overwrite={}, 
        to_append={
            "v_performance": df_v_perf,
            "daily_summary": df_daily,
            "geo_history": df_geo_pivoted,
            "traffic_history": df_traffic_pivoted,
            "devices_history": df_devices_pivoted,
            "audience_history": df_subs_pivoted
        }
    )
