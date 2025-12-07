import requests
import re
import time
from pathlib import Path

# --- Configuration ---

# Add your list of keys here
API_KEYS = [
    "e9f8ab45-8bc9-438a-ab86-9574083165d7",
    "93d9ebb5-0fab-40d0-b82d-ed72f8d54105",
    "36e5cde5-ac71-439b-9318-c3bbe66fb81c",

]

BASE_URL = "https://content.guardianapis.com/search"
# Make sure this path matches where your current 900 articles are!
PROJECT_DIR = Path(r"C:\Users\yuval\Desktop\לימודים\ML\data")

CATEGORIES = ['news', 'sport', 'Opinion', 'culture']

# We want 1000 NEW articles per key (Total 4000)
# Split across 4 categories = 250 new articles per category, per key.
TARGET_NEW_ARTICLES_PER_KEY = 1000
TARGET_PER_CATEGORY = int(TARGET_NEW_ARTICLES_PER_KEY / len(CATEGORIES))

PAGE_SIZE = 50


def clean_html(raw_html):
    if not raw_html:
        return ""
    cleanr = re.compile('<.*?>')
    return re.sub(cleanr, '', raw_html).strip()


def create_article_content(article):
    fields = article.get("fields", {})
    body = (fields.get("bodyText") or "").strip()

    if not body:
        return None

    section = article.get("sectionName", "General")
    date = (article.get("webPublicationDate") or "")[:10]
    byline = fields.get("byline", "Unknown Author")
    url = article.get("webUrl", "")
    title = fields.get("headline", article.get("webTitle", "Untitled"))

    # Filter Corrections
    if "correction" in title.lower() or "clarification" in title.lower():
        return None
    if "corrections" in byline.lower():
        return None

    trail_text = clean_html(fields.get("trailText", ""))
    tags_names = [t.get('webTitle') for t in article.get("tags", [])]
    tags_str = ", ".join(tags_names)

    return (
        f"The Guardian | {section} | {date}\n"
        f"By {byline}\n"
        f"{url}\n"
        f"Tags: {tags_str}\n"
        f"\n"
        f"{title}\n"
        f"{'-' * 20}\n"
        f"{trail_text}\n"
        f"{'-' * 60}\n"
        f"{body}\n"
    )


def main():
    print(f"Fetching data to: {PROJECT_DIR}")
    PROJECT_DIR.mkdir(parents=True, exist_ok=True)

    # This cursor tracks the page number for each category globally.
    # It ensures Key #2 starts searching where Key #1 ended.
    category_page_cursor = {category: 1 for category in CATEGORIES}

    for key_index, current_api_key in enumerate(API_KEYS):
        print(f"\n{'=' * 20} SWITCHING TO API KEY #{key_index + 1} {'=' * 20}")

        # Track how many NEW articles this specific key has collected
        key_total_collected = 0

        for category in CATEGORIES:
            print(f"\n--- Category: {category} (Looking for {TARGET_PER_CATEGORY} new articles) ---")

            clean_category = category.lower()
            api_section = 'commentisfree' if clean_category == 'opinion' else clean_category

            category_new_collected = 0

            # loop until we find enough NEW articles for this category
            while category_new_collected < TARGET_PER_CATEGORY:
                current_page = category_page_cursor[category]

                params = {
                    "api-key": current_api_key,
                    "page-size": PAGE_SIZE,
                    "page": current_page,
                    "section": api_section,
                    "order-by": "newest",
                    "show-fields": "headline,byline,bodyText,trailText",
                    "show-tags": "all"
                }

                try:
                    # Request data
                    resp = requests.get(BASE_URL, params=params)

                    # Handle Quota Limit (429)
                    if resp.status_code == 429:
                        print(f"!! Quota exceeded for Key #{key_index + 1}. Moving to next key...")
                        # Break the 'while' loop to skip to the next category/key
                        # But actually we want to break the CATEGORY loop too.
                        # For simplicity, we force the counters to max to exit this key.
                        category_new_collected = TARGET_PER_CATEGORY
                        key_total_collected = TARGET_NEW_ARTICLES_PER_KEY
                        break

                    resp.raise_for_status()
                    data = resp.json()
                    results = data["response"].get("results", [])

                    if not results:
                        print(f"No more historical data available for {category}.")
                        break

                    output_dir = PROJECT_DIR / "data" / category
                    output_dir.mkdir(parents=True, exist_ok=True)

                    page_saved_count = 0
                    skipped_count = 0

                    for article in results:
                        article_id = article["id"].replace("/", "_")
                        file_path = output_dir / f"{article_id}.txt"

                        # --- CRITICAL CHANGE: SKIP IF EXISTS ---
                        if file_path.exists():
                            skipped_count += 1
                            continue  # Skip to next article, don't save, don't count

                        # Process Content
                        content = create_article_content(article)
                        if content:
                            file_path.write_text(content, encoding="utf-8")
                            page_saved_count += 1
                            category_new_collected += 1

                    # Update User
                    print(f"   Page {current_page}: Saved {page_saved_count} new | Skipped {skipped_count} existing.")

                    # Move to next page for next time
                    category_page_cursor[category] += 1

                    # Small sleep to be polite
                    time.sleep(0.3)

                except Exception as e:
                    print(f"Error on {category} page {current_page}: {e}")
                    time.sleep(2)  # Wait a bit if error occurs
                    break

            key_total_collected += category_new_collected
            print(f"Finished {category} for this key. Total new: {category_new_collected}")

        print(f"Key #{key_index + 1} finished. Total new articles collected: {key_total_collected}")

    print("\nScript finished. You should now have your target dataset!")


if __name__ == "__main__":
    main()