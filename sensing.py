import csv
import os
from pathlib import Path

# --- הגדרות נתיבים ---
PROJECT_DIR = Path(r"C:\Users\yuval\Desktop\לימודים\ML")
DATA_DIR = PROJECT_DIR / "data"
OUTPUT_FILE = PROJECT_DIR / "sensed_data.csv"


def parse_article_file(file_path):
    """
    פונקציה שמבצעת את ה"חישה" (Sensing):
    הופכת קובץ טקסט לא מובנה (Unstructured) למידע מובנה (Structured Dictionary).
    """
    try:
        # קריאת הקובץ
        content = file_path.read_text(encoding="utf-8")
        lines = content.splitlines()

        # בדיקה שהקובץ מכיל את כל השורות הנדרשות (לפי הפורמט שיצרנו)
        # הפורמט החדש הוא ארוך (כותרות, תגיות, תקציר וכו'), אז צריך לפחות 9 שורות
        if len(lines) < 9:
            return None

        # --- חילוץ המרכיבים לעמודות נפרדות ---

        # שורה 1: Metadata (The Guardian | Section | Date)
        header_parts = lines[0].split('|')
        date = header_parts[-1].strip() if len(header_parts) >= 3 else "Unknown"

        # שורה 2: Author
        author = lines[1].replace("By ", "").strip()

        # שורה 3: URL
        url = lines[2].strip()

        # שורה 4: Tags (המרכיב החדש)
        tags = lines[3].replace("Tags: ", "").strip()

        # שורה 6: Title (נמצאת באינדקס 5 בגלל שורות רווח)
        title = lines[5].strip()

        # שורה 8: Trail Text / Abstract (המרכיב החדש)
        trail_text = lines[7].strip()

        # שורה 10 והלאה: Body (גוף הכתבה)
        body = " ".join(lines[9:]).strip()

        # החזרת מילון שייצג שורה אחת בטבלה הסופית
        return {
            "date": date,
            "author": author,
            "url": url,
            "tags": tags,  # עמודה נפרדת לתגיות
            "title": title,  # עמודה נפרדת לכותרת
            "trail_text": trail_text,  # עמודה נפרדת לתקציר
            "body": body  # עמודה נפרדת לגוף הכתבה
        }

    except Exception as e:
        print(f"Error parsing file {file_path.name}: {e}")
        return None


def main():
    print("--- Starting Static Sensing Process ---")

    if not DATA_DIR.exists():
        print(f"Error: Data directory not found at {DATA_DIR}")
        return

    all_articles = []
    categories_found = []

    # מעבר על התיקיות (כל תיקייה היא Label)
    for category_dir in DATA_DIR.iterdir():
        if category_dir.is_dir():
            label = category_dir.name  # ה-Label נגזר משם התיקייה
            categories_found.append(label)
            print(f"Processing Label: {label}...")

            # מעבר על כל הקבצים בתיקייה
            files = list(category_dir.glob("*.txt"))
            for file_path in files:
                article_data = parse_article_file(file_path)

                if article_data:
                    # הוספת ה-Label (חובה לפי ההוראות)
                    article_data["label"] = label
                    all_articles.append(article_data)

    # שמירה לקובץ CSV
    if all_articles:
        # הגדרת העמודות בטבלה (כולל ה-Label וכל מרכיבי הכתבה)
        fieldnames = ["label", "title", "trail_text", "tags", "date", "author", "body", "url"]

        try:
            with open(OUTPUT_FILE, mode='w', encoding='utf-8', newline='') as csv_file:
                writer = csv.DictWriter(csv_file, fieldnames=fieldnames)

                # כתיבת כותרות העמודות
                writer.writeheader()

                # כתיבת השורות
                writer.writerows(all_articles)

            print(f"\nSuccess! Sensed Data created at: {OUTPUT_FILE}")
            print(f"Total samples processed: {len(all_articles)}")
            print(f"Columns created: {fieldnames}")

        except Exception as e:
            print(f"Error writing CSV: {e}")
    else:
        print("No articles found. Please check the data collection step.")


if __name__ == "__main__":
    main()