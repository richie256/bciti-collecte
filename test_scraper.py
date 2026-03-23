from scraper import get_next_collections
import logging

logging.basicConfig(level=logging.INFO)

def test_scraper():
    print("Fetching collection schedule for Sector M...")
    next_dates = get_next_collections()
    if next_dates:
        print("\nNext collection dates found:")
        for key, date in next_dates.items():
            date_str = date.isoformat() if date else "Not found"
            print(f"- {key}: {date_str}")
    else:
        print("No collection dates found.")

if __name__ == "__main__":
    test_scraper()
