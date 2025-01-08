import cloudscraper
from bs4 import BeautifulSoup
import json
import os

# Skapa en cloudscraper-session
scraper = cloudscraper.create_scraper()

# Filnamn för JSON-data (källa och mål)
input_file = 'videos.json'
output_file = 'videos_updated.json'

# Ladda existerande data
def load_existing_data(file):
    if os.path.exists(file):
        with open(file, 'r', encoding='utf-8') as f:
            return json.load(f)
    return []

# Spara data i JSON-format
def save_data(data):
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(data, f, indent=4, ensure_ascii=False)

# Funktion för att skrapa information från en URL inklusive episoder och m3u8-länkar
def scrape_video_info(url):
    try:
        response = scraper.get(url)
        if response.status_code != 200:
            print(f"Misslyckades med att hämta: {url}")
            return None

        soup = BeautifulSoup(response.text, 'html.parser')

        # Hämta titel
        title_element = soup.select_one('.post-title h1')
        title = title_element.text.strip() if title_element else "Ingen titel hittad"

        # Hämta huvudbild (thumbnail)
        thumbnail_element = soup.select_one('.summary_image img')
        thumbnail = thumbnail_element['src'] if thumbnail_element else "Ingen thumbnail hittad"

        # Hämta fapped rate och total
        rating_element = soup.select_one('span#averagerate')
        fapped_rate = rating_element.text if rating_element else "N/A"

        total_votes_element = soup.select_one('span#countrate')
        fapped_total = total_votes_element.text if total_votes_element else "N/A"

        # Hämta visningar (viewed)
        viewed_element = soup.find_all('div', class_="summary-content")
        viewed = "N/A"
        for element in viewed_element:
            if "Total views" in element.text:
                viewed = ''.join(filter(str.isdigit, element.text))
                break

        # Hämta författare
        author_element = soup.select_one('.author-content a')
        author = author_element.text if author_element else "N/A"

        # Hämta genrer
        genres_element = soup.select('.genres-content a')
        genres = [genre.text for genre in genres_element] if genres_element else []

        # Hämta episoder
        episodes = []
        episode_container = soup.select('.listing-chapters_wrap ul.main.version-chap > li.wp-manga-chapter')

        if not episode_container:
            print("Inga episoder hittades.")
        else:
            for episode_item in episode_container:
                # Hämta episodens thumbnail
                episode_thumbnail_element = episode_item.find('img')
                episode_thumbnail = episode_thumbnail_element['src'] if episode_thumbnail_element else "Ingen thumbnail hittad"

                # Försök extrahera episodnumret från URL eller alt-text
                import re
                episode_number = None
                match = re.search(r"-(\d+)-eng", episode_thumbnail)
                if match:
                    episode_number = int(match.group(1))
                else:
                    alt_text = episode_thumbnail_element.get('alt', '')
                    alt_match = re.search(r"episode (\d+)", alt_text, re.IGNORECASE)
                    if alt_match:
                        episode_number = int(alt_match.group(1))
                if not episode_number:
                    episode_number = len(episodes) + 1

                # Generera m3u8-länk från thumbnail
                m3u8_url = "Ingen m3u8-länk genererad"
                match_id = re.search(r"hh/(.*?)/s_poster.jpg", episode_thumbnail)
                if match_id:
                    m3u8_id = match_id.group(1)
                    m3u8_url = f"https://master-lengs.org/api/v3/hh/{m3u8_id}/master.m3u8"

                # Lägg till episoddata
                episodes.append({
                    "episode_number": episode_number,
                    "episode_thumbnail": episode_thumbnail,
                    "m3u8_url": m3u8_url
                })

        # Sortera episoder så att episod 1 är längst ner
        episodes = sorted(episodes, key=lambda x: x['episode_number'], reverse=True)

        # Returnera som dictionary
        return {
            "title": title,
            "url": url,
            "thumbnail": thumbnail,
            "fapped_rate": fapped_rate,
            "fapped_total": fapped_total,
            "viewed": viewed,
            "author": author,
            "genres": genres,
            "episodes": episodes
        }

    except Exception as e:
        print(f"Fel vid skrapning av {url}: {e}")
        return None

# Uppdatera JSON med nya episoder
def update_video_data():
    # Ladda befintlig data från output-filen
    existing_data = load_existing_data(output_file)
    existing_urls = {video['url'] for video in existing_data}

    # Ladda alla serier och de senaste 10 från input-filen
    all_data = load_existing_data(input_file)
    recent_data = all_data[-10:]  # De senaste 10 serierna

    # Kontrollera de 10 senaste serierna
    for video in recent_data:
        print(f"Kontrollerar: {video['url']}")
        video_info = scrape_video_info(video['url'])

        if video_info:
            # Kontrollera om serien redan finns
            if video_info['url'] in existing_urls:
                # Uppdatera befintliga episoder
                for existing_video in existing_data:
                    if existing_video['url'] == video_info['url']:
                        existing_episodes = {ep['episode_number'] for ep in existing_video['episodes']}
                        new_episodes = [ep for ep in video_info['episodes'] if ep['episode_number'] not in existing_episodes]

                        if new_episodes:
                            print(f"✨ Nya episoder hittades för: {video['url']}")
                            existing_video['episodes'].extend(new_episodes)
                            existing_video['episodes'] = sorted(existing_video['episodes'], key=lambda x: x['episode_number'], reverse=True)
            else:
                # Lägg till den nya serien högst upp i listan
                print(f"✨ Ny serie läggs till: {video['url']}")
                existing_data.insert(0, video_info)  # Lägg till den nya serien högst upp

    # Spara uppdaterad data
    save_data(existing_data)
    print(f"\n✅ Uppdatering färdig! Data sparad i '{output_file}'.")


# Starta skrapningen
update_video_data()
