import json
import urllib.request
import datetime
import os
import sys

def fetch_data(username="TMT3"):
    headers = {
        "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    }
    
    total_solved = 1007
    easy = 333
    medium = 539
    hard = 135
    streak = 61
    total_active_days = 354
    submissions = {}
    
    # 1. Fetch Solved counts
    try:
        url_solved = f"https://alfa-leetcode-api.onrender.com/{username}/solved"
        req = urllib.request.Request(url_solved, headers=headers)
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            ac_stats = data.get("matchedUserStats", {}).get("acSubmissionNum", [])
            solved_map = {item["difficulty"]: item["count"] for item in ac_stats}
            if "All" in solved_map:
                total_solved = solved_map["All"]
                easy = solved_map.get("Easy", easy)
                medium = solved_map.get("Medium", medium)
                hard = solved_map.get("Hard", hard)
    except Exception as e:
        print(f"Warning fetching solved stats: {e}", file=sys.stderr)

    # 2. Fetch Calendar / Submissions
    try:
        url_cal = f"https://alfa-leetcode-api.onrender.com/{username}/calendar"
        req = urllib.request.Request(url_cal, headers=headers)
        with urllib.request.urlopen(req, timeout=12) as resp:
            data = json.loads(resp.read().decode('utf-8'))
            streak = data.get("streak", streak)
            total_active_days = data.get("totalActiveDays", total_active_days)
            raw_cal = data.get("submissionCalendar", "{}")
            if isinstance(raw_cal, str):
                submissions = json.loads(raw_cal)
            elif isinstance(raw_cal, dict):
                submissions = raw_cal
    except Exception as e:
        print(f"Warning fetching calendar data: {e}", file=sys.stderr)

    return {
        "total_solved": total_solved,
        "easy": easy,
        "medium": medium,
        "hard": hard,
        "streak": streak,
        "total_active_days": total_active_days,
        "submissions": submissions
    }

def get_color(count):
    if count == 0:
        return "#161b22"
    elif count <= 2:
        return "#0e4429"
    elif count <= 5:
        return "#006d32"
    elif count <= 9:
        return "#26a641"
    else:
        return "#39d353"

def generate_svg(data, output_path):
    today = datetime.date.today()
    # End on the current week's Saturday
    days_to_saturday = (5 - today.weekday()) % 7
    end_date = today + datetime.timedelta(days=days_to_saturday)
    start_date = end_date - datetime.timedelta(weeks=52, days=6)
    
    # Map timestamps to date -> count
    sub_by_date = {}
    total_year_submissions = 0
    for ts_str, count in data["submissions"].items():
        try:
            ts = int(ts_str)
            d = datetime.datetime.fromtimestamp(ts, tz=datetime.timezone.utc).date()
            sub_by_date[d] = sub_by_date.get(d, 0) + count
            total_year_submissions += count
        except Exception:
            pass
            
    if total_year_submissions == 0:
        total_year_submissions = 1355

    CELL_SIZE = 10
    CELL_GAP = 3.5
    STEP = CELL_SIZE + CELL_GAP  # 13.5
    GRID_X = 20
    GRID_Y = 52
    
    cols = 53
    rects = []
    month_labels = []
    last_month = None
    
    curr = start_date
    col_idx = 0
    while col_idx < cols:
        for row_idx in range(7):
            d = curr
            count = sub_by_date.get(d, 0)
            color = get_color(count)
            x = GRID_X + col_idx * STEP
            y = GRID_Y + row_idx * STEP
            
            # Label month on top-row day change
            if row_idx == 0 and d.month != last_month and col_idx < 50:
                month_name = d.strftime("%b")
                month_labels.append(f'<text x="{x:.1f}" y="{GRID_Y + 7 * STEP + 14:.1f}" fill="#8b949e" font-family="JetBrains Mono, -apple-system, sans-serif" font-size="9">{month_name}</text>')
                last_month = d.month
                
            rects.append(f'<rect x="{x:.1f}" y="{y:.1f}" width="{CELL_SIZE}" height="{CELL_SIZE}" rx="2.5" fill="{color}"><title>{d.strftime("%Y-%m-%d")}: {count} submissions</title></rect>')
            curr += datetime.timedelta(days=1)
        col_idx += 1

    svg_width = int(GRID_X * 2 + cols * STEP)
    svg_height = int(GRID_Y + 7 * STEP + 24)
    
    svg = f'''<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {svg_width} {svg_height}" width="100%" height="100%">
  <style>
    .mono {{ font-family: "JetBrains Mono", -apple-system, BlinkMacSystemFont, "Segoe UI", monospace; }}
    .bold {{ font-weight: 700; }}
    .dim {{ fill: #8b949e; }}
    .light {{ fill: #e6edf3; }}
    .easy {{ fill: #5cb85c; }}
    .med {{ fill: #f0ad4e; }}
    .hard {{ fill: #d9534f; }}
    .accent {{ fill: #10B981; }}
  </style>

  <!-- Header Info (Borderless layout with curved pills) -->
  <g class="mono">
    <!-- Solved Counter -->
    <text x="{GRID_X}" y="24" class="light bold" font-size="16">{data["total_solved"]:,}<tspan class="dim" font-size="12" font-weight="400"> / 4055 Solved</tspan></text>
    
    <!-- Curved Difficulty Badges -->
    <rect x="{GRID_X + 160}" y="10" width="70" height="20" rx="10" fill="#161b22" stroke="#30363d" stroke-width="1" />
    <text x="{GRID_X + 168}" y="24" class="easy bold" font-size="10">Easy <tspan class="light">{data["easy"]}</tspan></text>

    <rect x="{GRID_X + 238}" y="10" width="70" height="20" rx="10" fill="#161b22" stroke="#30363d" stroke-width="1" />
    <text x="{GRID_X + 246}" y="24" class="med bold" font-size="10">Med. <tspan class="light">{data["medium"]}</tspan></text>

    <rect x="{GRID_X + 316}" y="10" width="70" height="20" rx="10" fill="#161b22" stroke="#30363d" stroke-width="1" />
    <text x="{GRID_X + 324}" y="24" class="hard bold" font-size="10">Hard <tspan class="light">{data["hard"]}</tspan></text>

    <!-- Submissions & Streak -->
    <text x="{svg_width - GRID_X}" y="24" text-anchor="end" class="dim" font-size="11">
      <tspan class="light bold">{total_year_submissions:,}</tspan> Submissions <tspan fill="#30363d">•</tspan> 
      <tspan class="light bold">{data["total_active_days"]}</tspan> Active Days <tspan fill="#30363d">•</tspan> 
      <tspan class="accent bold">{data["streak"]} Days</tspan> Streak
    </text>
  </g>

  <!-- Green Dotted Submission Matrix (Rounded squircle cells) -->
  <g>
    {"".join(rects)}
  </g>

  <!-- Month Labels -->
  <g>
    {"".join(month_labels)}
  </g>
</svg>'''

    os.makedirs(os.path.dirname(os.path.abspath(output_path)), exist_ok=True)
    with open(output_path, "w", encoding="utf-8") as f:
        f.write(svg)
    print(f"Generated SVG at {output_path}")

if __name__ == "__main__":
    username = sys.argv[1] if len(sys.argv) > 1 else "TMT3"
    data = fetch_data(username)
    generate_svg(data, "dist/leetcode-activity.svg")
    generate_svg(data, "leetcode-activity.svg")
