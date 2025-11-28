import pandas as pd
import re
import nltk
from nltk.corpus import stopwords
from pathlib import Path

# --- הגדרות והורדות ---
nltk.download('stopwords', quiet=True)

PROJECT_DIR = Path(r"C:\Users\yuval\Desktop\לימודים\ML")
INPUT_FILE = PROJECT_DIR / "sensed_data.csv"
OUTPUT_FILE = PROJECT_DIR / "processed_data_separated.csv"  # שיניתי שם כדי שיהיה ברור שזה מופרד

STOP_WORDS = set(stopwords.words('english'))


def clean_text_noise(text):
    """
    מנקה רעשים ומסיר Stop Words (אותה פונקציה, תופעל על כל עמודה בנפרד)
    """
    if not isinstance(text, str):
        return ""

    # 1. המרה לקטנות
    text = text.lower()

    # 2. השארת אותיות בלבד
    text = re.sub(r'[^a-z\s]', '', text)

    # 3. טוקניזציה
    words = text.split()

    # 4. הסרת מילות עצירה ומילים קצרות
    filtered_words = [w for w in words if w not in STOP_WORDS and len(w) > 2]

    return " ".join(filtered_words)


def main():
    print("--- Starting Pre-processing (Cleaning Separate Columns) ---")

    if not INPUT_FILE.exists():
        print(f"Error: {INPUT_FILE} not found.")
        return

    df = pd.read_csv(INPUT_FILE)
    initial_count = len(df)
    print(f"Loaded {initial_count} articles.")

    # 1. ניקוי שורות בסיסי (כפילויות וחסרים)
    df = df.dropna(subset=['title'])
    df = df.drop_duplicates(subset=['url'])

    # 2. ניקוי שם הכותב
    df['author'] = df['author'].fillna('unknown').astype(str)
    df['author'] = df['author'].apply(lambda x: x.lower().replace('by ', '').strip())

    # 3. ניקוי עמודות הטקסט (בנפרד!)
    text_columns = ['title', 'trail_text', 'tags', 'body']

    print(f"Cleaning text columns: {text_columns}...")

    for col in text_columns:
        # מילוי ערכים חסרים כדי שהפונקציה לא תיכשל
        df[col] = df[col].fillna('')
        # הפעלת פונקציית הניקוי על העמודה הנוכחית
        df[col] = df[col].apply(clean_text_noise)

    # 4. סינון: נשמור רק כתבות שיש בהן לפחות מיני-כותרת (Trail Text) תקינה
    # (כי זה מה שרצית להשתמש בו בשלב הבא)
    df = df[df['trail_text'].str.len() > 2]

    # 5. שמירה
    # אנחנו שומרים את כל העמודות המקוריות (אחרי שניקינו אותן)
    # אין יותר 'processed_text' מאוחד
    final_columns = ['label', 'title', 'trail_text', 'tags', 'body', 'author', 'date', 'url']

    # סינון העמודות שקיימות בפועל ב-df
    cols_to_save = [c for c in final_columns if c in df.columns]

    df[cols_to_save].to_csv(OUTPUT_FILE, index=False)

    print(f"Success! Saved separated processed data to: {OUTPUT_FILE}")
    print(f"Final article count: {len(df)}")
    print("Sample of cleaned Trail Text:")
    print(df['trail_text'].iloc[0])


if __name__ == "__main__":
    main()