import pandas as pd
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
from bs4 import BeautifulSoup
import time
import os
import random
from datetime import datetime

# --- REQUÊTES ÉLARGIES POUR PLUS D'OFFRES ---
DEFAULT_QUERIES = [
     

    # Data & AI
    {"keywords": "data", "location": "Morocco"},
    {"keywords": "data analyst", "location": "Morocco"},
    {"keywords": "data scientist", "location": "Morocco"},
    {"keywords": "data engineer", "location": "Morocco"},
    {"keywords": "machine learning", "location": "Morocco"},
    {"keywords": "AI internship", "location": "Morocco"},
    {"keywords": "deep learning", "location": "Morocco"},
    {"keywords": "NLP", "location": "Morocco"},
    {"keywords": "computer vision", "location": "Morocco"},
    {"keywords": "business intelligence", "location": "Morocco"},
    {"keywords": "analytics", "location": "Morocco"},
    
     
]

def get_driver():
    """Créer un driver Chrome optimisé anti-détection."""
    options = Options()
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-blink-features=AutomationControlled")
    options.add_experimental_option("excludeSwitches", ["enable-automation"])
    options.add_experimental_option('useAutomationExtension', False)
    options.add_argument("--window-size=1920,1080")
    options.add_argument("--disable-gpu")
    options.add_argument("--lang=en-US")
    
    user_agents = [
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36",
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
        "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
    ]
    options.add_argument(f"user-agent={random.choice(user_agents)}")
    
    driver = webdriver.Chrome(options=options)
    driver.execute_script("Object.defineProperty(navigator, 'webdriver', {get: () => undefined})")
    return driver

def scroll_page(driver, scroll_pause=1.5):
    """Scroll progressif optimisé."""
    last_height = driver.execute_script("return document.body.scrollHeight")
    attempts = 0
    
    while attempts < 6:
        # Scroll en 3 étapes
        for i in range(3):
            driver.execute_script(f"window.scrollTo(0, document.body.scrollHeight * {(i+1)/3});")
            time.sleep(random.uniform(0.3, 0.7))
        
        time.sleep(scroll_pause)
        new_height = driver.execute_script("return document.body.scrollHeight")
        
        if new_height == last_height:
            break
        last_height = new_height
        attempts += 1

def wait_for_jobs(driver, timeout=8):
    """Attendre le chargement des jobs."""
    try:
        WebDriverWait(driver, timeout).until(
            EC.presence_of_element_located((By.CSS_SELECTOR, "ul.jobs-search__results-list, div.base-card"))
        )
        return True
    except:
        return False

def scrape_page(keywords, location, page_num, driver):
    """Scraper une page avec extraction optimisée."""
    start = page_num * 25
    url = (
        f"https://www.linkedin.com/jobs/search/?keywords={keywords.replace(' ', '%20')}"
        f"&location={location.replace(' ', '%20')}&f_E=1&start={start}"
    )
    
    try:
        driver.get(url)
        time.sleep(random.uniform(2, 4))
        
        if not wait_for_jobs(driver):
            return []
        
        scroll_page(driver)
        time.sleep(1)
        
    except Exception as e:
        return []

    soup = BeautifulSoup(driver.page_source, "html.parser")
    
    # Trouver les job cards avec plusieurs méthodes
    job_cards = []
    container = soup.find("ul", class_="jobs-search__results-list")
    if container:
        job_cards = container.find_all("li")
    
    if not job_cards:
        job_cards = soup.find_all("div", class_="base-card")
    
    if not job_cards:
        job_cards = soup.find_all("li", class_="jobs-search-results__list-item")
    
    if not job_cards:
        return []
    
    page_jobs = []
    for card in job_cards:
        try:
            # Extraction avec fallbacks multiples
            title_tag = (card.find("h3", class_="base-search-card__title") or 
                        card.find("a", class_="base-card__full-link") or
                        card.find("h3") or
                        card.find("span", class_="sr-only"))
            
            company_tag = (card.find("h4", class_="base-search-card__subtitle") or
                          card.find("a", class_="hidden-nested-link") or
                          card.find("h4") or
                          card.find("span", class_="job-search-card__subtitle"))
            
            loc_tag = (card.find("span", class_="job-search-card__location") or
                      card.find("span", class_="base-search-card__metadata"))
            
            link_tag = card.find("a", href=True)
            
            # Logo avec plusieurs sources
            logo_tag = card.find("img")
            logo_url = "N/A"
            if logo_tag:
                logo_url = (logo_tag.get("src") or 
                           logo_tag.get("data-delayed-url") or 
                           logo_tag.get("data-ghost-url") or "N/A")
            
            # Extraction texte
            title = title_tag.get_text(strip=True) if title_tag else "N/A"
            company = company_tag.get_text(strip=True) if company_tag else "N/A"
            location_text = loc_tag.get_text(strip=True) if loc_tag else location
            link = link_tag["href"].split("?")[0] if link_tag else "N/A"
            
            # Validation
            if title != "N/A" and link != "N/A" and "linkedin.com/jobs/view" in link:
                page_jobs.append({
                    "title": title,
                    "company": company,
                    "location": location_text,
                    "link": link,
                    "logo": logo_url,
                    "search_keywords": keywords,
                    "search_location": location,
                    "scraped_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                })
        except:
            continue
    
    return page_jobs

def scrape_query(query, max_pages=8):
    """Scraper plusieurs pages d'une requête."""
    driver = get_driver()
    all_jobs = []
    consecutive_empty = 0
    
    try:
        for page in range(max_pages):
            jobs = scrape_page(query["keywords"], query["location"], page, driver)
            
            if not jobs:
                consecutive_empty += 1
                if consecutive_empty >= 2:
                    break
            else:
                consecutive_empty = 0
                all_jobs.extend(jobs)
            
            # Pause courte entre pages
            if page < max_pages - 1 and jobs:
                time.sleep(random.uniform(2, 4))
                
    except Exception as e:
        print(f"  ⚠️ Error: {e}")
    finally:
        driver.quit()
    
    return all_jobs

def run_scraper(queries=None, max_pages=8, max_workers=1, fast_mode=False):
    """
    Fonction principale de scraping optimisée.
    
    Args:
        queries: Liste de requêtes (None = utiliser DEFAULT_QUERIES)
        max_pages: Pages max par requête (8 = ~200 jobs par requête)
        max_workers: Non utilisé (séquentiel)
        fast_mode: Si True, réduit les délais (risque de blocage)
    
    Returns:
        DataFrame pandas avec les résultats
    """
    if queries is None:
        queries = DEFAULT_QUERIES
    
    print(f"\n{'='*70}")
    print(f" LINKEDIN SCRAPER - MODE OPTIMISÉ")
    print(f"{'='*70}")
    print(f"Requêtes: {len(queries)}")
    print(f" Pages max/requête: {max_pages}")
    print(f" Objectif: ~{len(queries) * max_pages * 20} offres potentielles")
    print(f"⏰ Démarré: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"{'='*70}\n")
    
    all_results = []
    start_time = time.time()
    
    for i, query in enumerate(queries, 1):
        print(f" [{i}/{len(queries)}] '{query['keywords'][:40]}' in {query['location']}", end=" ")
        
        jobs = scrape_query(query, max_pages=max_pages)
        all_results.extend(jobs)
        
        print(f"→ {len(jobs)} jobs | Total: {len(all_results)}")
        
        # Pause entre requêtes (ajustable)
        if i < len(queries):
            wait = random.uniform(3, 6) if fast_mode else random.uniform(6, 10)
            time.sleep(wait)
    
    # Traitement final
    elapsed = time.time() - start_time
    
    if all_results:
        df = pd.DataFrame(all_results)
        
        # Nettoyage
        initial = len(df)
        df.drop_duplicates(subset="link", keep="first", inplace=True)
        
        # Filtrer les offres invalides
        df = df[df['title'] != "N/A"]
        df = df[df['link'].str.contains("linkedin.com/jobs/view", na=False)]
        
        removed = initial - len(df)
        
        # Sauvegarder
        os.makedirs("public", exist_ok=True)
        output_file = "public/linkedin_jobs_all_pages.csv"
        df.to_csv(output_file, index=False, encoding="utf-8-sig")
        
        print(f"\n{'='*70}")
        print(f"SCRAPING TERMINÉ EN {elapsed/60:.1f} MINUTES !")
        print(f"{'='*70}")
        print(f" Offres collectées: {initial}")
        print(f" Doublons/invalides supprimés: {removed}")
        print(f" Offres uniques finales: {len(df)}")
        print(f" Entreprises uniques: {df['company'].nunique()}")
        print(f" Villes: {df['location'].nunique()}")
        print(f" Fichier: {output_file}")
        print(f"{'='*70}\n")
        
        # Top 10 mots-clés les plus productifs
        print("🏆 TOP 10 RECHERCHES LES PLUS PRODUCTIVES:")
        top_keywords = df['search_keywords'].value_counts().head(10)
        for kw, count in top_keywords.items():
            print(f"  • {kw[:45]:<45} → {count:>3} offres")
        
        print(f"\n{'='*70}\n")
        
        return df
    else:
        print("\n Aucune offre trouvée!")
        return pd.DataFrame()

# Pour test direct
if __name__ == "__main__":
    print(" Choisissez un mode:")
    print("1. Mode COMPLET (toutes les requêtes, ~1h, 500+ offres)")
    print("2. Mode RAPIDE (requêtes principales, ~20min, 200+ offres)")
    print("3. Mode TEST (3 requêtes, ~2min, 50+ offres)")
    
    choice = input("\nVotre choix (1/2/3): ").strip()
    
    if choice == "1":
        df = run_scraper(DEFAULT_QUERIES, max_pages=8, fast_mode=False)
    elif choice == "2":
        quick_queries = DEFAULT_QUERIES[:20]  # 20 premières requêtes
        df = run_scraper(quick_queries, max_pages=6, fast_mode=True)
    else:
        test_queries = [
            {"keywords": "internship", "location": "Morocco"},
            {"keywords": "stage", "location": "Morocco"},
            {"keywords": "developer", "location": "Morocco"},
        ]
        df = run_scraper(test_queries, max_pages=5, fast_mode=True)
    
    if not df.empty:
        print("\n APERÇU DES RÉSULTATS:")
        print(df[['title', 'company', 'location']].head(15).to_string(index=False))