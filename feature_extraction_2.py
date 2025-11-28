import pandas as pd
import numpy as np
import joblib
from sklearn.feature_extraction.text import TfidfVectorizer
from pathlib import Path

# --- הגדרות נתיבים ---
PROJECT_DIR = Path(r"C:\Users\yuval\Desktop\לימודים\ML")
INPUT_FILE = PROJECT_DIR / "processed_data_separated.csv"  # הקובץ הנקי והמופרד
OUTPUT_FILE = PROJECT_DIR / "dataset_features_final.csv"  # הקובץ הסופי למודל
MODEL_DIR = PROJECT_DIR / "models"

if not MODEL_DIR.exists():
    MODEL_DIR.mkdir()


def analyze_top_features(df, vectorizer, tfidf_matrix, feature_type_name):
    """
    פונקציית עזר שמדפיסה את המילים/תגיות הכי חזקות בכל קטגוריה
    כדי שתוכלי לראות בעיניים שהחילוץ עובד טוב.
    """
    print(f"\n--- Top Significant {feature_type_name} per Category ---")
    unique_labels = df['label'].unique()
    feature_names = np.array(vectorizer.get_feature_names_out())

    for label in unique_labels:
        indices = df.index[df['label'] == label].tolist()
        if not indices: continue

        class_matrix = tfidf_matrix[indices]
        mean_scores = np.array(class_matrix.mean(axis=0)).flatten()

        # 10 המילים החזקות ביותר
        top_indices = mean_scores.argsort()[-10:][::-1]

        print(f"Category: {label.upper()}")
        # הדפסה נקייה
        results = [f"{feature_names[i]}" for i in top_indices]
        print(", ".join(results))


def get_specialist_authors(df, min_articles=3):
    """
    מחזירה רשימה של כותבים 'מומחים': כתבו לפחות 3 כתבות ורק בנושא אחד.
    """
    print(f"\nAnalyzing Author Specialization...")
    # סינון כותבים לא ידועים
    df_clean = df[~df['author'].isin(['unknown', 'unknown author', 'guardian staff'])]

    # יצירת מטריצת כותבים-נושאים
    author_matrix = pd.crosstab(df_clean['author'], df_clean['label'])

    # סינון לפי כמות כתבות
    active_authors = author_matrix[author_matrix.sum(axis=1) >= min_articles]

    # בדיקה: האם הכותב פעיל בדיוק בקטגוריה אחת?
    is_specialist = (active_authors > 0).sum(axis=1) == 1
    specialist_authors = active_authors[is_specialist].index.tolist()

    print(f"Found {len(specialist_authors)} specialist authors.")
    return specialist_authors


def main():
    print("--- Starting Feature Extraction (Trail Text + Tags + Authors) ---")

    if not INPUT_FILE.exists():
        print(f"Error: {INPUT_FILE} not found. Run preprocessing first.")
        return

    # 1. טעינת הנתונים
    print("Loading data...")
    df = pd.read_csv(INPUT_FILE)

    # מילוי ערכים חסרים (חשוב מאוד למניעת קריסות)
    df['trail_text'] = df['trail_text'].fillna('')
    df['tags'] = df['tags'].fillna('')
    df['author'] = df['author'].fillna('unknown')

    print(f"Total articles: {len(df)}")

    # --- חלק A: מאפיינים מה-Mini Headline (Trail Text) ---
    print("\n1. Extracting Mini-Headline Features (Top 1000)...")
    # משתמשים ב-1000 מילים כי הטקסט חופשי ומגוון
    trail_vectorizer = TfidfVectorizer(max_features=1000)
    X_trail = trail_vectorizer.fit_transform(df['trail_text'])

    # הצגת ניתוח קצר
    analyze_top_features(df, trail_vectorizer, X_trail, "Trail-Words")

    # יצירת DataFrame ושמירה עם קידומת trail_
    trail_features = pd.DataFrame(
        X_trail.toarray(),
        columns=[f"trail_{w}" for w in trail_vectorizer.get_feature_names_out()]
    )
    joblib.dump(trail_vectorizer, MODEL_DIR / "tfidf_trail.pkl")

    # --- חלק B: מאפיינים מהתגיות (Tags) ---
    print("\n2. Extracting Tag Features (Top 500)...")
    # לתגיות מספיק 500 כי אוצר המילים שם מצומצם ומדויק יותר
    tags_vectorizer = TfidfVectorizer(max_features=500)
    X_tags = tags_vectorizer.fit_transform(df['tags'])

    # הצגת ניתוח קצר
    analyze_top_features(df, tags_vectorizer, X_tags, "Tags")

    # יצירת DataFrame ושמירה עם קידומת tag_
    tags_features = pd.DataFrame(
        X_tags.toarray(),
        columns=[f"tag_{w}" for w in tags_vectorizer.get_feature_names_out()]
    )
    joblib.dump(tags_vectorizer, MODEL_DIR / "tfidf_tags.pkl")

    # --- חלק C: מאפייני כותבים מומחים (Authors) ---
    print("\n3. Extracting Specialist Author Features...")

    # שימוש בפונקציה החכמה לזיהוי מומחים
    selected_authors = get_specialist_authors(df, min_articles=3)

    # שמירת הרשימה לעתיד
    joblib.dump(selected_authors, MODEL_DIR / "authors_list.pkl")

    # יצירת עמודות (One-Hot Encoding)
    author_features = pd.DataFrame()
    for author in selected_authors:
        col_name = f"auth_{author.replace(' ', '_')}"
        author_features[col_name] = df['author'].apply(lambda x: 1 if x == author else 0)

    # --- חלק D: איחוד ושמירה סופית ---
    print("\n4. Combining all features...")

    # איפוס אינדקסים כדי שהחיבור יעבוד חלק (קריטי!)
    df.reset_index(drop=True, inplace=True)
    trail_features.reset_index(drop=True, inplace=True)
    tags_features.reset_index(drop=True, inplace=True)
    author_features.reset_index(drop=True, inplace=True)

    # חיבור כל הטבלאות לטבלה אחת ענקית
    final_dataset = pd.concat([trail_features, tags_features, author_features], axis=1)

    # הוספת ה-Label (עמודת המטרה) בסוף
    final_dataset['label'] = df['label']

    # שמירה לקובץ CSV
    final_dataset.to_csv(OUTPUT_FILE, index=False)

    print(f"\nSuccess! Final dataset saved to: {OUTPUT_FILE}")
    print(f"Dataset Dimensions: {final_dataset.shape}")
    print(f" - Trail Text features: {trail_features.shape[1]}")
    print(f" - Tag features: {tags_features.shape[1]}")
    print(f" - Author features: {author_features.shape[1]}")


if __name__ == "__main__":
    main()