import os
import re
import time
import json
import pandas as pd
import requests

# 1. INPUT DATA: Top Indian publishing domains across news, finance, and entertainment
PUBLISHING_DOMAINS = [
    "moneycontrol.com",
    "timesofindia.indiatimes.com",
    "ndtv.com",
    "indianexpress.com",
    "hindustantimes.com",
    "thehindu.com",
    "news18.com",
    "livemint.com",
    "firstpost.com",
    "scroll.in",
    "republicworld.com",
    "indiatvnews.com",
    "gadgets360.com"
]

CACHE_DIR = ".cache"
os.makedirs(CACHE_DIR, exist_ok=True)

# Map SSP domains to their respective sellers.json URLs
SSP_SELLERS_URLS = {
    "google.com": "https://realtimebidding.google.com/sellers.json",
    "criteo.com": "https://www.criteo.com/sellers.json",
    "rubiconproject.com": "https://www.rubiconproject.com/sellers.json",
    "magnite.com": "https://www.rubiconproject.com/sellers.json" # Rubicon is Magnite
}

HEADERS = {
    "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,image/webp,*/*;q=0.8"
}

def fetch_with_cache(url, cache_filename, max_age_days=1):
    """
    Fetch a URL and cache it locally to prevent unnecessary repeated large downloads.
    """
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
        
        # Save to cache
        with open(cache_path, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return data
    except Exception as e:
        print(f"Error fetching sellers.json from {url}: {e}")
        # If remote fetch fails, try to load from expired cache as backup
        if os.path.exists(cache_path):
            print(f"Fallback: Loading expired cache for {cache_filename}...")
            with open(cache_path, "r", encoding="utf-8") as f:
                return json.load(f)
        return None

def load_sellers_json_mappings():
    """
    Loads sellers.json for the top 3 networks (Google, Criteo, Magnite) and creates lookup indexes.
    """
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
            seller_id = str(seller.get("seller_id"))  # Sometimes int, normalize to string
            if seller_id:
                mappings["rubiconproject.com"][seller_id] = {
                    "name": seller.get("name", "Confidential") if not seller.get("is_confidential") else "Confidential",
                    "seller_type": seller.get("seller_type", "UNKNOWN").upper(),
                    "is_active": not seller.get("is_passthrough", False)
                }
                
    return mappings

def scrape_ads_txt(domain, timeout=15):
    """
    Fetches the public ads.txt file for a domain and parses it.
    """
    url = f"https://{domain}/ads.txt"
    print(f"Scraping ads.txt for {domain}...")
    
    try:
        response = requests.get(url, headers=HEADERS, timeout=timeout, allow_redirects=True)
        if response.status_code != 200:
            # If standard root domain fails, try with www
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
            # Strip comments
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
            
            # Standardize relationship
            if "DIRECT" in relationship:
                relationship = "DIRECT"
            elif "RESELLER" in relationship:
                relationship = "RESELLER"
            else:
                continue # Skip invalid relationship lines
                
            records.append({
                "publisher_domain": domain,
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

def main():
    print("==========================================================")
    print("STEP 1: Fetching and parsing sellers.json for Google, Criteo, Magnite...")
    print("==========================================================")
    mappings = load_sellers_json_mappings()
    
    print("\n==========================================================")
    print("STEP 2: Scraping ads.txt for top Indian domains...")
    print("==========================================================")
    
    all_ads_records = []
    for domain in PUBLISHING_DOMAINS:
        records = scrape_ads_txt(domain)
        all_ads_records.extend(records)
        # Sleep for rate limiting and politeness
        time.sleep(1.0)
        
    print(f"\nScraped total of {len(all_ads_records)} raw records from ads.txt files.")
    
    print("\n==========================================================")
    print("STEP 3 & 4: Correlation Engine - Matching ads.txt with sellers.json...")
    print("==========================================================")
    
    correlated_records = []
    
    for rec in all_ads_records:
        pub_domain = rec["publisher_domain"]
        ssp_domain = rec["ssp_domain"]
        seller_id = rec["seller_id"]
        rel = rec["relationship"]
        
        # Determine normalized SSP mapping key
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
            # Match account ID
            if seller_id in ssp_map:
                info = ssp_map[seller_id]
                legal_entity = info["name"]
                # Append active state or seller type details if we want, but name is main
                if not info["is_active"]:
                    legal_entity += " [INACTIVE]"
            else:
                legal_entity = "Unlisted / Unknown ID"
        else:
            legal_entity = "Not Tracked (Non-Top 3 SSP)"
            
        correlated_records.append({
            "publisher_domain": pub_domain,
            "ssp_domain": ssp_domain,
            "seller_id": seller_id,
            "relationship": rel,
            "verified_legal_entity": legal_entity
        })
        
    # Create DataFrame
    df = pd.DataFrame(correlated_records)
    
    # Save to CSV
    output_filename = "indian_adtech_supply_chain.csv"
    df.to_csv(output_filename, index=False)
    print(f"\nSaved {len(df)} correlated supply chain records to '{output_filename}'.")
    
    # Print short summary
    print("\nSummary of results:")
    print(df["ssp_domain"].value_counts().head(10))

if __name__ == "__main__":
    main()
