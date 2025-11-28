import requests
import re
from pathlib import Path

# --- הגדרות וקבועים ---
API_KEY = "e9f8ab45-8bc9-438a-ab86-9574083165d7"  # המפתח שלך
BASE_URL = "https://content.guardianapis.com/search"
PROJECT_DIR = Path(r"C:\Users\yuval\Desktop\לימודים\ML")

CATEGORIES = ['news', 'sport', 'Opinion', 'culture']
# העליתי קצת את הכמות כדי לפצות על כתבות שיימחקו בסינון (כמו התיקונים)
ARTICLES_PER_CATEGORY = 200


def clean_html(raw_html):
    """פונקציה לניקוי תגיות HTML משדה ה-TrailText"""
    if not raw_html:
        return ""
    cleanr = re.compile('<.*?>')
    cleantext = re.sub(cleanr, '', raw_html)
    return cleantext.strip()


def create_article_content(article):
    fields = article.get("fields", {})
    body = (fields.get("bodyText") or "").strip()

    # בדיקה בסיסית שיש תוכן
    if not body:
        return None

    # חילוץ שדות בסיסיים
    section = article.get("sectionName", "General")
    date = (article.get("webPublicationDate") or "")[:10]
    byline = fields.get("byline", "Unknown Author")
    url = article.get("webUrl", "")
    title = fields.get("headline", article.get("webTitle", "Untitled"))

    # --- חלק 1: התיקון לבעיית ה-News ---
    # סינון אגרסיבי של כתבות "תיקונים והבהרות"
    # אם המילים Correction/Clarification מופיעות בכותרת או בכותב - מדלגים
    low_title = title.lower()
    low_byline = byline.lower()

    if "correction" in low_title or "clarification" in low_title:
        return None
    if "corrections" in low_byline:  # תופס את 'Corrections and clarifications editor'
        return None

    # --- חלק 2: חילוץ התוספות (תגיות ומיני-כותרת) ---

    # חילוץ המיני-כותרת (Trail Text) וניקוי מ-HTML
    trail_text = clean_html(fields.get("trailText", ""))

    # חילוץ התגיות (Tags)
    tags_data = article.get("tags", [])
    # יוצרים רשימה של שמות התגיות (למשל: 'World news', 'Politics')
    tags_names = [t.get('webTitle') for t in tags_data]
    tags_str = ", ".join(tags_names)

    # --- בניית הטקסט הסופי לשמירה ---
    return (
        f"The Guardian | {section} | {date}\n"
        f"By {byline}\n"
        f"{url}\n"
        f"Tags: {tags_str}\n"  # הוספת התגיות
        f"\n"
        f"{title}\n"
        f"{'-' * 20}\n"
        f"{trail_text}\n"  # הוספת המיני-כותרת
        f"{'-' * 60}\n"
        f"{body}\n"
    )


def main():
    print(f"Fetching data to: {PROJECT_DIR}")

    for category in CATEGORIES:
        clean_category = category.lower()
        if clean_category == 'opinion':
            api_section = 'commentisfree'
        else:
            api_section = clean_category

        print(f"--- Processing: {category} (Asking API for: {api_section}) ---")

        params = {
            "api-key": API_KEY,
            "page-size": ARTICLES_PER_CATEGORY,
            "section": api_section,
            "order-by": "newest",
            # הוספנו את trailText ואת trailText לרשימת השדות
            "show-fields": "headline,byline,bodyText,trailText",
            # הוספנו בקשה לקבלת כל התגיות
            "show-tags": "all"
        }

        try:
            resp = requests.get(BASE_URL, params=params)
            resp.raise_for_status()
            results = resp.json()["response"].get("results", [])

            if not results:
                print(f"NO RESULTS for {category}")
                continue

            output_dir = PROJECT_DIR / "data" / category
            output_dir.mkdir(parents=True, exist_ok=True)

            count = 0
            for article in results:
                article_id = article["id"].replace("/", "_")
                file_path = output_dir / f"{article_id}.txt"

                # אנחנו לא בודקים if exists כי אנחנו רוצים לדרוס קבצים ישנים
                # כדי שיתעדכנו עם התגיות והמיני-כותרת החדשות
                content = create_article_content(article)

                # אם התוכן חזר ריק (בגלל הסינון שלנו) - לא שומרים
                if content:
                    file_path.write_text(content, encoding="utf-8")
                    count += 1

            print(f"Successfully saved {count} articles in {category}")

        except Exception as e:
            print(f"Error fetching {category}: {e}")


if __name__ == "__main__":
    main()