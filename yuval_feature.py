import pandas as pd
import numpy as np
from sklearn.feature_extraction.text import TfidfVectorizer
from pathlib import Path

# נתיבים
PROJECT_DIR = Path(r"C:\Users\yuval\Desktop\לימודים\ML")
INPUT_FILE = PROJECT_DIR / "processed_data_separated.csv"


def print_top_features(df, column_name, title, vectorizer_params={'max_features': 1000}):
    """
    פונקציה גנרית לניתוח TF-IDF והדפסה בשורה אחת
    """
    print("\n" + "=" * 60)
    print(f"ANALYSIS: {title}")
    print("=" * 60)

    # מילוי חוסרים
    df[column_name] = df[column_name].fillna('')

    # חישוב TF-IDF
    print(f"Calculating TF-IDF for {column_name}...")
    tfidf = TfidfVectorizer(**vectorizer_params)
    tfidf_matrix = tfidf.fit_transform(df[column_name])
    feature_names = np.array(tfidf.get_feature_names_out())

    unique_labels = df['label'].unique()

    for label in unique_labels:
        # שליפת השורות של הקטגוריה
        indices = df.index[df['label'] == label].tolist()
        if not indices: continue

        # חישוב ממוצע הציון לכל מילה בקטגוריה
        class_matrix = tfidf_matrix[indices]
        mean_scores = np.array(class_matrix.mean(axis=0)).flatten()

        # מיון ולקחת את ה-10 הכי חזקים
        top_indices = mean_scores.argsort()[-10:][::-1]

        print(f"\nCategory: {label.upper()}")

        # יצירת הרשימה המופרדת בפסיקים
        results = []
        for i in top_indices:
            if mean_scores[i] > 0:
                results.append(f"{feature_names[i]} ({mean_scores[i]:.3f})")

        print(", ".join(results))


def analyze_top_specialists(df):
    print("\n" + "=" * 60)
    print("PART 3: TOP 10 SPECIALIST AUTHORS")
    print("=" * 60)

    # ניקוי וסינון כותבים
    df['author'] = df['author'].fillna('unknown')
    df_clean = df[~df['author'].isin(['unknown', 'unknown author', 'guardian staff'])]

    # יצירת המטריצה
    author_matrix = pd.crosstab(df_clean['author'], df_clean['label'])

    # סינון כותבים פעילים (לפחות 3 כתבות)
    active_authors = author_matrix[author_matrix.sum(axis=1) >= 3].copy()

    if active_authors.empty:
        print("No active authors found.")
        return

    # זיהוי מומחים (כתבו בקטגוריה אחת בלבד)
    is_specialist = (active_authors > 0).sum(axis=1) == 1
    specialists = active_authors[is_specialist].copy()

    # --- התיקון נמצא כאן ---
    # קודם מחשבים את הערכים, ורק בסוף מכניסים לטבלה

    # 1. מציאת הקטגוריה (שם העמודה עם הערך המקסימלי)
    # (עובד תקין כי הטבלה מכילה כרגע רק מספרים)
    categories = specialists.idxmax(axis=1)

    # 2. מציאת מספר הכתבות (הערך המקסימלי בשורה)
    article_counts = specialists.max(axis=1)

    # 3. השמה לתוך הטבלה (עכשיו אפשר להוסיף טקסט כי סיימנו לחשב)
    specialists['Category'] = categories
    specialists['Article_Count'] = article_counts

    # מיון לפי מספר הכתבות (מהגדול לקטן) ולקיחת ה-10 הראשונים
    top_10_specialists = specialists.sort_values(by='Article_Count', ascending=False).head(10)

    print(f"{'AUTHOR':<30} | {'CATEGORY':<15} | {'COUNT'}")
    print("-" * 60)

    for author, row in top_10_specialists.iterrows():
        print(f"{author:<30} | {row['Category']:<15} | {row['Article_Count']}")


def main():
    if not INPUT_FILE.exists():
        print("Error: processed_data_separated.csv not found.")
        return

    print("Loading data...")
    df = pd.read_csv(INPUT_FILE)

    # 1. ניתוח תגיות (Tags)
    print_top_features(df, 'tags', "TOP TF-IDF SCORES FOR TAGS", {'max_features': 500})

    # 2. ניתוח מיני-כותרת (Trail Text)
    print_top_features(df, 'trail_text', "TOP TF-IDF SCORES FOR TRAIL TEXT",
                       {'max_features': 1000, 'stop_words': 'english'})

    # 3. ניתוח כותבים מומחים (Top 10)
    analyze_top_specialists(df)


if __name__ == "__main__":
    main()