import cloudscraper
from bs4 import BeautifulSoup
import json
import os

# Skapa en cloudscraper-session
scraper = cloudscraper.create_scraper()

# Filnamn för JSON-data
json_file = 'videos.json'

# Ställ in om de olika sektionerna ska skrapas (1 = På, 0 = Av)
NYHETER = 1  # För /release/
CATEGORIES_ON = 0  # För att skrapa kategorier
CATEGORIES = ["uncensored", "tentacle", "yuri"]  # Lägg enkelt till fler kategorier här

# Funktion för att ladda befintlig data från JSON om den redan existerar
def load_existing_data():
    if os.path.exists(json_file):
        with open(json_file, 'r', encoding='utf-8') as file:
            return json.load(file)
    return []

# Funktion för att spara data kontinuerligt med UTF-8
def save_data(data):
    with open(json_file, 'w', encoding='utf-8') as file:
        json.dump(data, file, indent=4, ensure_ascii=False)

# Funktion för att skrapa en enskild sida och returnera videoobjekt
def scrape_videos(url):
    try:
        response = scraper.get(url)
        if response.status_code == 404:
            return None  # Stoppar loopen när vi når en 404
        soup = BeautifulSoup(response.text, 'html.parser')

        # Lista för att spara videoinformation från sidan
        video_list = []

        # Hitta huvudbehållaren som innehåller alla videor
        content_listing = soup.find('div', class_="page-content-listing item-big_thumbnail")

        # Gå igenom varje "page-listing-item"
        if content_listing:
            for page_listing in content_listing.find_all('div', class_="page-listing-item"):
                # Gå igenom varje kolumn där videorna finns
                for video_item in page_listing.find_all('div', class_="col-6 col-md-zarat badge-pos-1"):
                    # Hämta titeln och länken
                    title_element = video_item.find('h3')
                    title = title_element.get_text(strip=True) if title_element else "Okänd titel"

                    video_link_element = video_item.find('a', href=True)
                    video_link = video_link_element['href'] if video_link_element else "Ingen länk hittad"

                    # Lägg till i listan om det inte redan finns
                    video_list.append({
                        "title": title,
                        "url": video_link
                    })
        return video_list
    except Exception as e:
        print(f"Fel uppstod vid skrapning: {e}")
        return None

# Skrapa årsbaserade nyheter (release) med stopp om gammal video hittas
def scrape_releases():
    existing_data = load_existing_data()
    unique_links = {item['url'] for item in existing_data}

    for year in range(2024, 1990, -1):
        print(f"\n>>> Skrapar år: {year}")
        page = 1

        while True:
            url = f"https://hentaihaven.xxx/release/{year}/" if page == 1 else f"https://hentaihaven.xxx/release/{year}/page/{page}/"
            print(f"Skrapar: {url}")
            videos = scrape_videos(url)
            if videos is None:
                print(f"Inga fler sidor för {year}. Avslutar året.")
                break

            new_videos = []
            for video in videos:
                if video['url'] in unique_links:
                    # Spara de nya videorna innan vi avslutar
                    if new_videos:
                        existing_data.extend(new_videos)
                        unique_links.update([video['url'] for video in new_videos])
                        save_data(existing_data)
                        print(f"{len(new_videos)} nya videor sparade för {year}.")
                    print(f"Redan skrapad video hittad: {video['title']}. Avslutar skrapning för NYHETER.")
                    return
                new_videos.append(video)

            # Lägg till nya videor i datan om det finns några
            if new_videos:
                existing_data.extend(new_videos)
                unique_links.update([video['url'] for video in new_videos])
                save_data(existing_data)
                print(f"{len(new_videos)} nya videor sparade för {year} - Sida {page}.")
            else:
                print(f"Inga nya videor hittades på sida {page}.")
            page += 1

    print("Skrapning av RELEASE-sektionen klar!")


# Funktion för att skrapa generiska kategorier
def scrape_category(category):
    existing_data = load_existing_data()
    unique_links = {item['url'] for item in existing_data}

    print(f"\n>>> Skrapar kategori: {category}")
    page = 1

    while True:
        url = f"https://hentaihaven.xxx/series/{category}/" if page == 1 else f"https://hentaihaven.xxx/series/{category}/page/{page}/"
        print(f"Skrapar: {url}")
        videos = scrape_videos(url)
        if videos is None:
            print(f"Inga fler sidor i kategorin '{category}'.")
            break

        # Lägg till nya videor utan dubbletter
        new_videos = [video for video in videos if video['url'] not in unique_links]
        if new_videos:
            existing_data.extend(new_videos)
            unique_links.update([video['url'] for video in new_videos])
            save_data(existing_data)
            print(f"{len(new_videos)} nya videor sparade för kategori '{category}' - Sida {page}.")
        else:
            print(f"Inga nya videor hittades på sida {page}.")
        page += 1

    print(f"Skrapning av kategorin '{category}' är klar!")

# Huvudfunktion som kontrollerar vad som ska skrapas
def scrape_all():
    if NYHETER == 1:
        scrape_releases()
    else:
        print("Skrapning av RELEASE är avstängd.")

    if CATEGORIES_ON == 1:
        for category in CATEGORIES:
            scrape_category(category)
    else:
        print("Skrapning av CATEGORIES är avstängd.")

# Starta skrapningen
scrape_all()
