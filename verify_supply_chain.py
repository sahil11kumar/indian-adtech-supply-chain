import os
import re
import time
import json
import pandas as pd
import requests

# 1. Target Publishers for the Indian Market (20 per category, total 120)
PUBLISHERS_IN = {
    # News & Media
    "timesofindia.indiatimes.com": "News & Media",
    "ndtv.com": "News & Media",
    "indianexpress.com": "News & Media",
    "hindustantimes.com": "News & Media",
    "thehindu.com": "News & Media",
    "news18.com": "News & Media",
    "republicworld.com": "News & Media",
    "indiatvnews.com": "News & Media",
    "scroll.in": "News & Media",
    "dainikbhaskar.com": "News & Media",
    "jagran.com": "News & Media",
    "amarujala.com": "News & Media",
    "oneindia.com": "News & Media",
    "anandabazar.com": "News & Media",
    "malayalam.samayam.com": "News & Media",
    "asianetnews.com": "News & Media",
    "mathrubhumi.com": "News & Media",
    "dailythanthi.com": "News & Media",
    "deccanherald.com": "News & Media",
    "telegraphindia.com": "News & Media",
    
    # Finance & Business
    "moneycontrol.com": "Finance & Business",
    "livemint.com": "Finance & Business",
    "economictimes.indiatimes.com": "Finance & Business",
    "financialexpress.com": "Finance & Business",
    "business-standard.com": "Finance & Business",
    "cnbctv18.com": "Finance & Business",
    "businessinsider.in": "Finance & Business",
    "fortuneindia.com": "Finance & Business",
    "businesstoday.in": "Finance & Business",
    "outlookbusiness.com": "Finance & Business",
    "equitymaster.com": "Finance & Business",
    "tickertape.in": "Finance & Business",
    "groww.in": "Finance & Business",
    "moneyworks4me.com": "Finance & Business",
    "valueresearchonline.com": "Finance & Business",
    "bseindia.com": "Finance & Business",
    "nseindia.com": "Finance & Business",
    "livechennai.com": "Finance & Business",
    "dynamiclevels.com": "Finance & Business",
    "in.investing.com": "Finance & Business",
    
    # Tech & Gaming
    "gadgets360.com": "Tech & Gaming",
    "digit.in": "Tech & Gaming",
    "bgr.in": "Tech & Gaming",
    "gizbot.com": "Tech & Gaming",
    "mysmartprice.com": "Tech & Gaming",
    "smartprix.com": "Tech & Gaming",
    "cashify.in": "Tech & Gaming",
    "91mobiles.com": "Tech & Gaming",
    "mobile57.com": "Tech & Gaming",
    "beebom.com": "Tech & Gaming",
    "techlusive.in": "Tech & Gaming",
    "techpp.com": "Tech & Gaming",
    "gadgetsnow.com": "Tech & Gaming",
    "geeksforgeeks.org": "Tech & Gaming",
    "javatpoint.com": "Tech & Gaming",
    "tutorialspoint.com": "Tech & Gaming",
    "analyticsvidhya.com": "Tech & Gaming",
    "dataquest.nasscom.in": "Tech & Gaming",
    "spidell.in": "Tech & Gaming",
    "in.pcmag.com": "Tech & Gaming",
    
    # Entertainment
    "filmibeat.com": "Entertainment",
    "pinkvilla.com": "Entertainment",
    "koimoi.com": "Entertainment",
    "bollywoodhungama.com": "Entertainment",
    "boxofficeindia.com": "Entertainment",
    "teluguone.com": "Entertainment",
    "123telugu.com": "Entertainment",
    "greatandhra.com": "Entertainment",
    "tupaki.com": "Entertainment",
    "gulte.com": "Entertainment",
    "behindwoods.com": "Entertainment",
    "galatta.com": "Entertainment",
    "nettv4u.com": "Entertainment",
    "desimartini.com": "Entertainment",
    "missmalini.com": "Entertainment",
    "iwmbuzz.com": "Entertainment",
    "cinestaan.com": "Entertainment",
    "mirchiplay.com": "Entertainment",
    "zoomtventertainment.com": "Entertainment",
    "bollywoodlife.com": "Entertainment",
    
    # Sports
    "sportskeeda.com": "Sports",
    "cricbuzz.com": "Sports",
    "espncricinfo.com": "Sports",
    "sports.ndtv.com": "Sports",
    "khelnow.com": "Sports",
    "circularjourney.com": "Sports",
    "insidesport.in": "Sports",
    "mykhel.com": "Sports",
    "cricketaddictor.com": "Sports",
    "circleofcricket.com": "Sports",
    "cricheroes.in": "Sports",
    "cricketcountry.com": "Sports",
    "fancode.com": "Sports",
    "dynamiccricket.com": "Sports",
    "ultimatekho-kho.com": "Sports",
    "prokabaddi.com": "Sports",
    "isllive.in": "Sports",
    "aiff.com": "Sports",
    "bcci.tv": "Sports",
    "in.goal.com": "Sports",
    
    # Retail Media & E-Commerce (Marketplaces, Travel, Aggregators, Quick Commerce)
    "nykaa.com": "Retail Media & E-Commerce",
    "jiomart.com": "Retail Media & E-Commerce",
    "swiggy.com": "Retail Media & E-Commerce",
    "zepto.com": "Retail Media & E-Commerce",
    "makemytrip.com": "Retail Media & E-Commerce",
    "ixigo.com": "Retail Media & E-Commerce",
    "cleartrip.com": "Retail Media & E-Commerce",
    "cardekho.com": "Retail Media & E-Commerce",
    "zomato.com": "Retail Media & E-Commerce",
    "carwale.com": "Retail Media & E-Commerce",
    "zigwheels.com": "Retail Media & E-Commerce",
    "redbus.in": "Retail Media & E-Commerce",
    "bookmyshow.com": "Retail Media & E-Commerce",
    "magicbricks.com": "Retail Media & E-Commerce",
    "99acres.com": "Retail Media & E-Commerce",
    "housing.com": "Retail Media & E-Commerce",
    "nobroker.in": "Retail Media & E-Commerce",
    "justdial.com": "Retail Media & E-Commerce",
    "indiamart.com": "Retail Media & E-Commerce",
    "tradeindia.com": "Retail Media & E-Commerce"
}

# 2. Target Publishers for the US Market (20 per category, total 120)
PUBLISHERS_US = {
    # News & Media
    "nytimes.com": "News & Media",
    "cnn.com": "News & Media",
    "washingtonpost.com": "News & Media",
    "usatoday.com": "News & Media",
    "nypost.com": "News & Media",
    "huffpost.com": "News & Media",
    "foxnews.com": "News & Media",
    "nbcnews.com": "News & Media",
    "cbsnews.com": "News & Media",
    "abcnews.go.com": "News & Media",
    "theatlantic.com": "News & Media",
    "newyorker.com": "News & Media",
    "slate.com": "News & Media",
    "dailybeast.com": "News & Media",
    "politico.com": "News & Media",
    "time.com": "News & Media",
    "newsweek.com": "News & Media",
    "foreignpolicy.com": "News & Media",
    "vox.com": "News & Media",
    "nationalreview.com": "News & Media",
    
    # Finance & Business
    "forbes.com": "Finance & Business",
    "bloomberg.com": "Finance & Business",
    "cnbc.com": "Finance & Business",
    "businessinsider.com": "Finance & Business",
    "wsj.com": "Finance & Business",
    "marketwatch.com": "Finance & Business",
    "barrons.com": "Finance & Business",
    "fool.com": "Finance & Business",
    "investopedia.com": "Finance & Business",
    "seekingalpha.com": "Finance & Business",
    "finance.yahoo.com": "Finance & Business",
    "kiplinger.com": "Finance & Business",
    "standardandpoors.com": "Finance & Business",
    "morningstar.com": "Finance & Business",
    "reuters.com": "Finance & Business",
    "ft.com": "Finance & Business",
    "entrepreneur.com": "Finance & Business",
    "inc.com": "Finance & Business",
    "fastcompany.com": "Finance & Business",
    "economictimes.com": "Finance & Business",
    
    # Tech & Gaming
    "cnet.com": "Tech & Gaming",
    "theverge.com": "Tech & Gaming",
    "ign.com": "Tech & Gaming",
    "wired.com": "Tech & Gaming",
    "techcrunch.com": "Tech & Gaming",
    "engadget.com": "Tech & Gaming",
    "mashable.com": "Tech & Gaming",
    "gizmodo.com": "Tech & Gaming",
    "tomshardware.com": "Tech & Gaming",
    "digitaltrends.com": "Tech & Gaming",
    "pcgamer.com": "Tech & Gaming",
    "gamespot.com": "Tech & Gaming",
    "polygon.com": "Tech & Gaming",
    "lifehacker.com": "Tech & Gaming",
    "slashgear.com": "Tech & Gaming",
    "androidcentral.com": "Tech & Gaming",
    "macrumors.com": "Tech & Gaming",
    "appleinsider.com": "Tech & Gaming",
    "windowscentral.com": "Tech & Gaming",
    "howtogeek.com": "Tech & Gaming",
    
    # Entertainment
    "buzzfeed.com": "Entertainment",
    "variety.com": "Entertainment",
    "hollywoodreporter.com": "Entertainment",
    "people.com": "Entertainment",
    "tmz.com": "Entertainment",
    "billboard.com": "Entertainment",
    "rollingstone.com": "Entertainment",
    "pitchfork.com": "Entertainment",
    "ew.com": "Entertainment",
    "eonline.com": "Entertainment",
    "variety.com": "Entertainment",
    "popsugar.com": "Entertainment",
    "decider.com": "Entertainment",
    "screenrant.com": "Entertainment",
    "collider.com": "Entertainment",
    "wegotthiscovered.com": "Entertainment",
    "comingsoon.net": "Entertainment",
    "deadline.com": "Entertainment",
    "vulture.com": "Entertainment",
    "complex.com": "Entertainment",
    
    # Sports
    "espn.com": "Sports",
    "bleacherreport.com": "Sports",
    "cbssports.com": "Sports",
    "nbcsports.com": "Sports",
    "foxsports.com": "Sports",
    "sbnation.com": "Sports",
    "theathletic.com": "Sports",
    "yardbarker.com": "Sports",
    "rivals.com": "Sports",
    "247sports.com": "Sports",
    "maxpreps.com": "Sports",
    "rotowire.com": "Sports",
    "golfdigest.com": "Sports",
    "runnersworld.com": "Sports",
    "tennis.com": "Sports",
    "deadspin.com": "Sports",
    "barstoolsports.com": "Sports",
    "draftkings.com": "Sports",
    "fanduel.com": "Sports",
    "ufc.com": "Sports",
    
    # Retail Media & E-Commerce / Travel aggregates
    "tripadvisor.com": "Retail Media & E-Commerce",
    "expedia.com": "Retail Media & E-Commerce",
    "zillow.com": "Retail Media & E-Commerce",
    "redfin.com": "Retail Media & E-Commerce",
    "realtor.com": "Retail Media & E-Commerce",
    "wayfair.com": "Retail Media & E-Commerce",
    "booking.com": "Retail Media & E-Commerce",
    "hotels.com": "Retail Media & E-Commerce",
    "priceline.com": "Retail Media & E-Commerce",
    "kayak.com": "Retail Media & E-Commerce",
    "stubhub.com": "Retail Media & E-Commerce",
    "ticketmaster.com": "Retail Media & E-Commerce",
    "yelp.com": "Retail Media & E-Commerce",
    "opentable.com": "Retail Media & E-Commerce",
    "grubhub.com": "Retail Media & E-Commerce",
    "instacart.com": "Retail Media & E-Commerce",
    "autotrader.com": "Retail Media & E-Commerce",
    "cars.com": "Retail Media & E-Commerce",
    "truecar.com": "Retail Media & E-Commerce",
    "carvana.com": "Retail Media & E-Commerce"
}

CACHE_DIR = ".cache"
os.makedirs(CACHE_DIR, exist_ok=True)

# Map SSP domains to their respective sellers.json URLs
SSP_SELLERS_URLS = {
    "google.com": "https://realtimebidding.google.com/sellers.json",
    "criteo.com": "https://www.criteo.com/sellers.json",
    "rubiconproject.com": "https://www.rubiconproject.com/sellers.json",
    "magnite.com": "https://www.rubiconproject.com/sellers.json"
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
}

def fetch_with_cache(url, cache_filename, max_age_days=1):
    cache_path = os.path.join(CACHE_DIR, cache_filename)
    if os.path.exists(cache_path):
        mtime = os.path.getmtime(cache_path)
        age_days = (time.time() - mtime) / (24 * 3600)
        if age_days < max_age_days:
            print(f"Loading {cache_filename} from local cache...")
            with open(cache_path, "r", encoding="utf-8") as f:
                return json.load(f)
            
    print(f"Fetching {url} from remote server...")
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
        response.raise_for_status()
        data = response.json()
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return data
    except Exception as e:
        print(f"Error fetching sellers.json from {url}: {e}")
        if os.path.exists(cache_path):
            print(f"Fallback: Loading expired cache for {cache_filename}...")
            with open(cache_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return None

def load_sellers_json_mappings():
    mappings = {
        "google.com": {},
        "criteo.com": {},
        "rubiconproject.com": {}
    }
    
    # 1. Google
    google_data = fetch_with_cache(SSP_SELLERS_URLS["google.com"], "google_sellers.json")
    if google_data and "sellers" in google_data:
        for seller in google_data["sellers"]:
            seller_id = seller.get("seller_id")
            if seller_id:
                mappings["google.com"][seller_id] = {
                    "name": seller.get("name", "Confidential") if not seller.get("is_confidential") else "Confidential",
                    "seller_type": seller.get("seller_type", "UNKNOWN").upper(),
                    "is_active": not seller.get("is_passthrough", False)
                }

    # 2. Criteo
    criteo_data = fetch_with_cache(SSP_SELLERS_URLS["criteo.com"], "criteo_sellers.json")
    if criteo_data and "sellers" in criteo_data:
        for seller in criteo_data["sellers"]:
            seller_id = seller.get("seller_id")
            if seller_id:
                mappings["criteo.com"][seller_id] = {
                    "name": seller.get("name", "Confidential") if not seller.get("is_confidential") else "Confidential",
                    "seller_type": seller.get("seller_type", "UNKNOWN").upper(),
                    "is_active": not seller.get("is_passthrough", False)
                }

    # 3. Magnite
    magnite_data = fetch_with_cache(SSP_SELLERS_URLS["rubiconproject.com"], "magnite_sellers.json")
    if magnite_data and "sellers" in magnite_data:
        for seller in magnite_data["sellers"]:
            seller_id = str(seller.get("seller_id"))
            if seller_id:
                mappings["rubiconproject.com"][seller_id] = {
                    "name": seller.get("name", "Confidential") if not seller.get("is_confidential") else "Confidential",
                    "seller_type": seller.get("seller_type", "UNKNOWN").upper(),
                    "is_active": not seller.get("is_passthrough", False)
                }
                
    return mappings

def scrape_ads_txt(domain, category, timeout=15):
    url = f"https://{domain}/ads.txt"
    print(f"Scraping ads.txt for {domain} ({category})...")
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        if response.status_code != 200:
            if not domain.startswith("www."):
                alt_url = f"https://www.{domain}/ads.txt"
                print(f"  Received status {response.status_code}. Retrying with {alt_url}...")
                response = requests.get(alt_url, headers=HEADERS, timeout=timeout, allow_redirects=True)
                if response.status_code != 200:
                    print(f"  [Failed] HTTP {response.status_code} for {domain}")
                    return []
            else:
                print(f"  [Failed] HTTP {response.status_code} for {domain}")
                return []
                
        records = []
        for line in response.text.splitlines():
            if "#" in line:
                line = line.split("#")[0]
            line = line.strip()
            if not line:
                continue
                
            parts = [p.strip() for p in line.split(",")]
            if len(parts) < 3:
                continue
                
            ssp_domain = parts[0].lower()
            seller_id = parts[1]
            relationship = parts[2].upper()
            
            if "DIRECT" in relationship:
                relationship = "DIRECT"
            elif "RESELLER" in relationship:
                relationship = "RESELLER"
            else:
                continue
                
            records.append({
                "publisher_domain": domain,
                "publisher_category": category,
                "ssp_domain": ssp_domain,
                "seller_id": seller_id,
                "relationship": relationship
            })
            
        print(f"  [Success] Found {len(records)} supply path records.")
        return records
        
    except requests.exceptions.Timeout:
        print(f"  [Timeout] Timeout scraping {domain}")
    except Exception as e:
        print(f"  [Error] Failed scraping {domain}: {e}")
        
    return []

def scrape_market(market_name, publishers_dict, mappings):
    print(f"\n==========================================================")
    print(f"SCRAPING MARKET: {market_name.upper()} ({len(publishers_dict)} domains)")
    print(f"==========================================================")
    
    market_records = []
    for domain, category in publishers_dict.items():
        records = scrape_ads_txt(domain, category)
        market_records.extend(records)
        time.sleep(1.0)
        
    print(f"\nScraped total of {len(market_records)} raw records for {market_name.upper()}.")
    
    correlated_records = []
    for rec in market_records:
        pub_domain = rec["publisher_domain"]
        pub_cat = rec["publisher_category"]
        ssp_domain = rec["ssp_domain"]
        seller_id = rec["seller_id"]
        rel = rec["relationship"]
        
        mapping_key = None
        if "google.com" in ssp_domain:
            mapping_key = "google.com"
        elif "criteo.com" in ssp_domain:
            mapping_key = "criteo.com"
        elif "rubiconproject.com" in ssp_domain or "magnite.com" in ssp_domain:
            mapping_key = "rubiconproject.com"
            
        legal_entity = "N/A (Sellers.json Not Loaded)"
        
        if mapping_key:
            ssp_map = mappings[mapping_key]
            if seller_id in ssp_map:
                info = ssp_map[seller_id]
                legal_entity = info["name"]
                if not info["is_active"]:
                    legal_entity += " [INACTIVE]"
            else:
                legal_entity = "Unlisted / Unknown ID"
        else:
            legal_entity = "Not Tracked (Non-Top 3 SSP)"
            
        correlated_records.append({
            "publisher_domain": pub_domain,
            "publisher_category": pub_cat,
            "ssp_domain": ssp_domain,
            "seller_id": seller_id,
            "relationship": rel,
            "verified_legal_entity": legal_entity
        })
        
    df = pd.DataFrame(correlated_records)
    output_filename = f"{market_name.lower()}_adtech_supply_chain.csv"
    df.to_csv(output_filename, index=False)
    print(f"Saved {len(df)} correlated supply chain records to '{output_filename}'.")
    return df

def main():
    print("==========================================================")
    print("STEP 1: Fetching and parsing sellers.json for Google, Criteo, Magnite...")
    print("==========================================================")
    mappings = load_sellers_json_mappings()
    
    # Scrape India Market
    df_in = scrape_market("indian", PUBLISHERS_IN, mappings)
    
    # Scrape US Market
    df_us = scrape_market("us", PUBLISHERS_US, mappings)
    
    print("\n==========================================================")
    print("SUMMARY OF GENERATED DATASETS:")
    print(f"- Indian Market: {len(df_in)} paths saved to 'indian_adtech_supply_chain.csv'")
    print(f"- US Market: {len(df_us)} paths saved to 'us_adtech_supply_chain.csv'")
    print("==========================================================")

if __name__ == "__main__":
    main()
