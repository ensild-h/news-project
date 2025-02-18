from flask import Flask, render_template, request, redirect, url_for, jsonify
from collections import Counter, defaultdict
from collections import defaultdict
from textblob import TextBlob
from bs4 import BeautifulSoup
from database_utils import initialize_database
import requests
import re
import nltk
from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer
from nltk.corpus import stopwords
from sklearn.feature_extraction.text import TfidfVectorizer
import matplotlib.pyplot as plt
import io
import base64
import sqlite3
from datetime import datetime
import json

# Database connection function
def get_db_connection():
    try:
        conn = sqlite3.connect('news_analysis.db')
        conn.row_factory = sqlite3.Row
        return conn
    except sqlite3.DatabaseError as e:
        print(f"Database connection error: {e}")
        return None

nltk.download('punkt')
nltk.download('stopwords')
nltk.download('averaged_perceptron_tagger')

app = Flask(__name__, static_folder="static")

@app.after_request
def apply_csp(response):
    response.headers["Content-Security-Policy"] = (
        "default-src 'self'; "
        "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net; "
        "style-src 'self' 'unsafe-inline';"
    )
    return response


# Initialize the database
def initialize_database():
    connection = sqlite3.connect("news_analysis.db")
    cursor = connection.cursor()
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS analyses (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            original_text TEXT,
            summary TEXT,
            keywords TEXT,
            sentiment TEXT,
            category TEXT,
            timestamp TEXT
        )
    ''')
    connection.commit()
    connection.close()

# Helper Functions
def extract_text_from_url(url):
    try:
        response = requests.get(url)
        soup = BeautifulSoup(response.content, "html.parser")
        paragraphs = soup.find_all("p")
        text = " ".join(p.get_text() for p in paragraphs)
        return text
    except Exception as e:
        return ""

def summarize_text(text):
    sentences = nltk.sent_tokenize(text)
    return " ".join(sentences[:3])

def extract_keywords(text):
    def clean_text(text):
        # Remove special characters, numbers, and extra spaces
        return re.sub(r'[^a-zA-ZëËçÇüÜ\s]', '', text).strip()

    text = clean_text(text)
    words = text.split()
    
    # Remove stopwords
    filtered_words = [word for word in words if word.lower() not in albanian_stopwords]

    # Count word frequency
    word_freq = Counter(filtered_words)

    # Return the top 10 keywords by frequency
    return [word for word, _ in word_freq.most_common(10)]

# List of Albanian stopwords
albanian_stopwords = [
    "në", "të", "është", "se", "për", "shumë", "që", "së", "më", "me", "i", "e", "nga", "dhe",
    "kjo", "këtë", "këtu", "kështu", "këndej", "këtej", "unë", "ti", "ai", "ajo", "ne", "ju", "ata", "ato",
    "kemi", "kam", "ke", "ka", "kemi", "keni", "kanë", "jam", "je", "është", "jemi", "jeni", "janë",
    "do", "duhet", "duke", "dukej", "duket", "dukej", "duket", "dukej", "duket", "më", "me", "mu",
    "mua", "ti", "te", "të", "ty", "tua", "ai", "ajo", "ata", "ato", "ne", "na", "një", "as", "apo",
    "atë", "atëherë", "aty", "atyre", "kush", "çfarë", "ku", "kur", "ndër", "ndërsa", "ndonjë", "ndonjëri",
    "ndonjëra", "ndonjëherë", "nëse", "nuk", "ose", "pasi", "pse", "përse", "shpejt", "tek", "te",
    "tyre", "vetë", "vetëm", "ndër", "asnjë", "deri", "edhe", "gjithë", "gjithmonë", "gjithçka", "herë",
    "ishte", "janë", "jo", "kaq", "këtij", "këto", "madje", "mënyrë", "pas", "sa", "sepse", "si",
    "të gjithë", "tjetër", "veç", "çdo", "çka", "çështje"
]


def analyze_sentiment(text):
    blob = TextBlob(text)
    polarity = blob.sentiment.polarity
    if polarity > 0:
        return "Positive"
    elif polarity < 0:
        return "Negative"
    else:
        return "Neutral"

def save_to_database(original_text, summary, keywords, sentiment, category):
    try:
        connection = sqlite3.connect("news_analysis.db")
        cursor = connection.cursor()
        cursor.execute("""
            INSERT INTO analyses (original_text, summary, keywords, sentiment, category, timestamp)
            VALUES (?, ?, ?, ?, ?, ?)
        """, (original_text, summary, ", ".join(keywords), sentiment, category, datetime.now()))
        connection.commit()
        print("Data successfully saved to the database.")
    except sqlite3.Error as e:
        print(f"Error saving to the database: {e}")
    finally:
        connection.close()

def get_all_analyses():
    connection = sqlite3.connect("analysis.db")
    cursor = connection.cursor()
    cursor.execute("SELECT * FROM analyses")
    rows = cursor.fetchall()
    connection.close()
    return rows

def get_channel_comparison():
    conn = get_db_connection()
    cursor = conn.cursor()

    # Query to get counts for each channel
    cursor.execute("""
        SELECT category, sentiment, COUNT(*) 
        FROM analyses 
        GROUP BY category, sentiment
    """)
    rows = cursor.fetchall()
    conn.close()

    # Create a dictionary to structure the data
    channels = ['TOP CHANNEL', 'NEWS 24', 'EURONEWS', 'ABC NEWS', 'ORA NEWS']  # Update with your channels
    data = {channel: {'Positive': 0, 'Neutral': 0, 'Negative': 0} for channel in channels}
    for row in rows:
        category, sentiment, count = row
        if category in data:
            data[category][sentiment] = count
    return data

def get_statistics():
    connection = sqlite3.connect("analysis.db")
    cursor = connection.cursor()

    # Sentiment distribution
    cursor.execute("SELECT sentiment, COUNT(*) FROM analyses GROUP BY sentiment")
    sentiment_data = cursor.fetchall()

    # Top keywords
    cursor.execute("SELECT keywords FROM analyses")
    keywords = Counter(word for row in cursor.fetchall() for word in row[0].split(", "))
    top_keywords = keywords.most_common(10)

    # Analysis trends
    cursor.execute("SELECT DATE(timestamp), COUNT(*) FROM analyses GROUP BY DATE(timestamp)")
    trends = cursor.fetchall()

    # Category insights
    cursor.execute("SELECT category, COUNT(*) FROM analyses GROUP BY category")
    category_data = cursor.fetchall()

    connection.close()
    return sentiment_data, top_keywords, trends, category_data

def create_chart(data, chart_type, title, labels=None):
    plt.figure(figsize=(8, 6))
    if chart_type == "pie":
        plt.pie([x[1] for x in data], labels=[x[0] for x in data], autopct='%1.1f%%', startangle=140)
    elif chart_type == "bar":
        plt.bar([x[0] for x in data], [x[1] for x in data], color='skyblue')
        plt.xticks(rotation=45)
    elif chart_type == "line":
        plt.plot([x[0] for x in data], [x[1] for x in data], marker='o')
    plt.title(title)
    plt.tight_layout()
    buf = io.BytesIO()
    plt.savefig(buf, format="png")
    buf.seek(0)
    encoded_image = base64.b64encode(buf.read()).decode('utf-8')
    buf.close()
    return encoded_image

# Routes
@app.route("/", methods=["GET", "POST"])
def home():
    if request.method == "POST":
        text = request.form.get("text_input")
        url = request.form.get("url_input")
        category = request.form.get("category")  # Capture the selected category

        if url:
            text = extract_text_from_url(url)

        if not text:
            return render_template("home.html", error="Asnjë tekst nuk u dha ose nuk u përpunua.")  # Error in Albanian

        summary = summarize_text(text)
        keywords = extract_keywords(text)
        sentiment = analyze_sentiment(text)
        country = detect_country(text)  # Call detect_country here

        # Save the analysis to the database
        save_to_database(text, summary, keywords, sentiment, category)

        # Pass all the required data to the results.html template
        return render_template(
            "results.html",
            country=country,
            text=text,
            sentiment=sentiment,
            keywords=keywords,
            summary=summary,
            channel=category
        )

    # For GET requests, render the home page
    return render_template("home.html")

@app.route("/results", methods=["POST"])
def results():
    text = request.form.get("text")
    url = request.form.get("url")
    category = request.form.get("category")

    if url:
        text = extract_text_from_url(url)

    if not text:
        return render_template("home.html", error="Asnjë tekst nuk u dha ose nuk u përpunua.")

    summary = summarize_text(text)
    keywords = extract_keywords(text)
    sentiment = analyze_sentiment(text)
    country = detect_country(text)  # Detect relevant country from text

    # Save analysis to the database
    save_to_database(text, summary, keywords, sentiment, category)

    # Render results page with all data
    return render_template(
        "results.html",
        country=country,
        text=text,
        sentiment=sentiment,
        keywords=keywords,
        summary=summary,
        channel=category,
    )
    
def detect_country(text):
    # List of countries in Albanian
    countries_albanian = [
        'Shqipëri', 'Kosovë', 'Itali', 'Francë', 'Gjermani', 'Turqi', 
        'Greqi', 'Serbi', 'Austri', 'Spanjë', 'Maqedoni', 'Kroaci', 
        'Bosnjë', 'Mal i Zi', 'Zvicër'
    ]
    for country in countries_albanian:
        if country.lower() in text.lower():
            return country
    return 'Vendi i panjohur'  # "Unknown country" in Albanian

@app.route('/history')
def history():
    conn = get_db_connection()
    if conn:
        try:
            records = conn.execute('SELECT * FROM news ORDER BY created_at DESC').fetchall()
            conn.close()
            return render_template('history.html', records=records)
        except sqlite3.Error as e:
            print(f"Error fetching history data: {e}")
            return "Error fetching history data."
    return "Error connecting to the database."

@app.route('/statistics')
def statistics():
    conn = get_db_connection()
    if conn:
        try:
            # Sentiment distribution
            sentiments = conn.execute(
                "SELECT sentiment, COUNT(*) as count FROM analyses GROUP BY sentiment"
            ).fetchall()
            sentiment_data = {
                'labels': [row['sentiment'] for row in sentiments],
                'data': [row['count'] for row in sentiments]
            }

            # Top keywords
            keywords = conn.execute("SELECT keywords FROM analyses").fetchall()
            keyword_counts = Counter(
                word for row in keywords for word in row['keywords'].split(', ')
            )
            top_keywords = keyword_counts.most_common(10)
            keyword_data = {
                'labels': [word for word, _ in top_keywords],
                'data': [count for _, count in top_keywords]
            }

            # Analysis trends over time
            trends = conn.execute(
                "SELECT strftime('%Y-%m', timestamp) as month, COUNT(*) as count FROM analyses GROUP BY month"
            ).fetchall()
            trend_data = {
                'labels': [row['month'] for row in trends],
                'data': [row['count'] for row in trends]
            }

            # Category distribution
            categories = conn.execute(
                "SELECT category, COUNT(*) as count FROM analyses GROUP BY category"
            ).fetchall()
            category_data = {
                'labels': [row['category'] for row in categories],
                'data': [row['count'] for row in categories]
            }

            # Stats overview
            stats = conn.execute(
                "SELECT category, sentiment, COUNT(*) as total FROM analyses GROUP BY category, sentiment"
            ).fetchall()
            stats = [
                {
                    'channel': row['category'] if row['category'] else 'Unknown',
                    'sentiment': row['sentiment'],
                    'total': row['total']
                }
                for row in stats
            ]

            # Channel comparison data
            channel_comparison = conn.execute(
                "SELECT category, sentiment, COUNT(*) as count FROM analyses GROUP BY category, sentiment"
            ).fetchall()

            # Prepare channel comparison data
            channels = ['TOP CHANNEL', 'NEWS 24', 'EURONEWS', 'ABC NEWS', 'ORA NEWS']
            channel_data = {channel: {'Positive': 0, 'Neutral': 0, 'Negative': 0} for channel in channels}

            for row in channel_comparison:
                category, sentiment, count = row
                if category in channel_data:
                    channel_data[category][sentiment] = count

            channel_data_json = {
                'labels': list(channel_data.keys()),
                'positive': [v['Positive'] for v in channel_data.values()],
                'neutral': [v['Neutral'] for v in channel_data.values()],
                'negative': [v['Negative'] for v in channel_data.values()],
            }

            # Log all data for debugging
            print("Sentiment Data:", sentiment_data)
            print("Keyword Data:", keyword_data)
            print("Trend Data:", trend_data)
            print("Category Data:", category_data)
            print("Stats Overview:", stats)
            print("Channel Data:", channel_data_json)

            conn.close()

            # Pass the data to the template
            return render_template(
                'statistics.html',
                sentiment_data=sentiment_data,
                keyword_data=keyword_data,
                trend_data=trend_data,
                category_data=category_data,
                stats=stats,
                channel_data=channel_data_json
            )
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            return "Error loading statistics."
    return "Error connecting to the database."

if __name__ == "__main__":
    initialize_database()
    app.run(debug=True)