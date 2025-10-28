from flask import Flask, render_template, request, jsonify
import os
import pandas as pd
from scraper import run_scraper, DEFAULT_QUERIES
from apscheduler.schedulers.background import BackgroundScheduler

app = Flask(__name__)

CSV_PATH = "public/linkedin_jobs_all_pages.csv"

# --- Fonction de mise à jour automatique ---
def update_jobs():
    print("🔄 Scraping automatique des offres LinkedIn...")
    df = run_scraper(DEFAULT_QUERIES, max_pages=3, fast_mode=True)
    df.to_csv(CSV_PATH, index=False)
    print(f"✅ Mise à jour terminée: {len(df)} offres sauvegardées.")

# --- Scheduler pour exécuter toutes les 5 minutes ---
scheduler = BackgroundScheduler()
scheduler.add_job(update_jobs, 'interval', minutes=5)  # <- toutes les 5 min
scheduler.start()

# --- Route principale ---
@app.route("/", methods=["GET"])
def index():
    page = int(request.args.get("page", 1))
    keyword = request.args.get("keyword", "").lower()
    location = request.args.get("location", "").lower()

    # Charger le CSV
    if os.path.exists(CSV_PATH):
        df = pd.read_csv(CSV_PATH)
    else:
        df = run_scraper(DEFAULT_QUERIES, max_pages=3, fast_mode=True)

    # Filtrer selon la recherche
    filtered_df = df[
        df["title"].str.lower().str.contains(keyword) &
        df["location"].str.lower().str.contains(location)
    ] if not df.empty else pd.DataFrame()

    # Pagination
    per_page = 10
    total_jobs = len(filtered_df)
    total_pages = max((total_jobs + per_page - 1) // per_page, 1)
    start_idx = (page - 1) * per_page
    end_idx = start_idx + per_page
    jobs = filtered_df.iloc[start_idx:end_idx].to_dict(orient="records")

    stats = {
        "total": total_jobs,
        "companies": df['company'].nunique() if not df.empty else 0,
        "locations": df['location'].nunique() if not df.empty else 0
    }

    return render_template("index.html", jobs=jobs, stats=stats,
                           keyword=keyword, location=location,
                           page=page, total_pages=total_pages)

# --- Route pour mise à jour manuelle ---
@app.route("/refresh")
def refresh():
    update_jobs()
    return jsonify({
        "success": True,
        "message": "✅ Offres mises à jour automatiquement !"
    })

if __name__ == "__main__":
    os.makedirs("public", exist_ok=True)
    app.run(debug=True, host="127.0.0.1", port=5050)
