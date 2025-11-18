import os
import serpapi
from firebase_admin import firestore

def clear_collection(db, collection_name, batch_size=100):
    """
    Deletes all documents in a Firestore collection.
    """
    try:
        coll_ref = db.collection(collection_name)
        docs = coll_ref.limit(batch_size).stream()
        deleted = 0

        for doc in docs:
            print(f"Deleting doc {doc.id} => {doc.to_dict()}")
            doc.reference.delete()
            deleted += 1

        if deleted >= batch_size:
            return clear_collection(db, collection_name, batch_size)

        print(f"Collection '{collection_name}' cleared.")
    except Exception as e:
        print(f"Error clearing collection {collection_name}: {e}")

def get_google_news_data(db):
    """
    Fetches news articles from Google News using SerpAPI and saves them to Firestore.
    """
    print("Starting Google News data fetch...")

    # Get SerpAPI key from environment variable
    serpapi_key = os.environ.get('SERP_API_KEY')
    if not serpapi_key:
        print("SERP_API_KEY environment variable not set. Skipping news fetch.")
        return

    # Clear the existing news articles
    clear_collection(db, 'news_articles')

    search_terms = [
        "lomautus", "irtisanomiset", "yt-neuvottelut", "työllisyys",
        "työttömyys", "talouskasvu", "VM:n ennuste", "OP:n ennuste",
        "Nordean ennuste", "EK:n työmarkkinakatsaus", "työvoimapula",
        "rekrytointi-ilmapiiri"
    ]

    for term in search_terms:
        print(f"Fetching news for term: '{term}'")
        try:
            params = {
                "engine": "google_news",
                "q": term,
                "hl": "fi",
                "gl": "fi",
                "tbs": "qdr:m",  # Past month
                "num": 10,       # Max 10 results
                "api_key": serpapi_key
            }

            search = serpapi.search(params)
            results = search.as_dict()
            news_results = results.get("news_results", [])

            for article in news_results:
                # Ensure the link is a valid URL
                if not article.get("link", "").startswith("http"):
                    continue

                doc_data = {
                    "title": article.get("title"),
                    "link": article.get("link"),
                    "source": article.get("source"),
                    "date": article.get("date"),
                    "snippet": article.get("snippet"),
                    "search_term": term,
                    "timestamp": firestore.SERVER_TIMESTAMP
                }
                db.collection('news_articles').add(doc_data)

            print(f"Found and saved {len(news_results)} articles for '{term}'.")

        except Exception as e:
            print(f"Error fetching or saving news for term '{term}': {e}")

    print("Google News data fetch completed.")