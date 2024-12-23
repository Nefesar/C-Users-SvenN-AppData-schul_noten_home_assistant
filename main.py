import json
import requests
from bs4 import BeautifulSoup
import paho.mqtt.client as mqtt

def scrape_notes():
    # URL und Login-Daten
    login_url = "http://regelschule-steinbach-hallenberg.de/hip/login.php"
    data_url = "http://regelschule-steinbach-hallenberg.de/hip/getdata.php?mode=detail"
    login_data = {
        'username': 'AlvNot',
        'password': 'FJQTV'
    }

    # Starten einer Session
    session = requests.Session()

    # Einloggen auf der Webseite
    login_page = session.get(login_url)
    login_soup = BeautifulSoup(login_page.content, 'html.parser')

    # POST-Anfrage mit Login-Daten
    response = session.post(login_url, data=login_data)

    # Abrufen der Seite nach dem Login
    response = session.get(data_url)

    # Überprüfen, ob der Abruf erfolgreich war
    if response.status_code != 200:
        print("Fehler beim Abrufen der Seite!")
        return {}, {}

    # Extrahieren des HTML-Inhalts
    soup = BeautifulSoup(response.content, 'html.parser')

    subjects = {
        "Mathematik": "#content > div > table:nth-child(8)",
        "Deutsch": "#content > div > table:nth-child(6)",
        "Englisch": "#content > div > table:nth-child(10)",
        "Physik": "#content > div > table:nth-child(12)",
        "Chemie": "#content > div > table:nth-child(16)",
        "Biologie": "#content > div > table:nth-child(14)",
        "Geschichte": "#content > div > table:nth-child(18)",
        "Sport": "#content > div > table:nth-child(26)",
        "Wirtschaft-Recht-Technik": "#content > div > table:nth-child(28)",
        "Natur und Technik": "#content > div > table:nth-child(30)"
    }

    noten_data = {}
    averages = {}

    for fach, selector in subjects.items():
        table = soup.select_one(selector)
        if table:
            rows = table.find_all('tr')
            total_grades = 0
            count_grades = 0
            noten_list = []
            for row in rows:
                columns = row.find_all('td')
                if columns:
                    datum = columns[0].text.strip()
                    noten = [column.text.strip() for column in columns[1:]]
                    try:
                        note_num = int(noten[0])  # Extrahiere die Note als Zahl
                        total_grades += note_num
                        count_grades += 1
                    except ValueError:
                        continue  # Ignoriere ungültige Noten
                    formatted_noten = ", ".join(noten)
                    noten_list.append({"datum": datum, "noten": formatted_noten})

            noten_data[fach] = noten_list

            if count_grades > 0:
                averages[fach] = total_grades / count_grades
            else:
                averages[fach] = None
        else:
            print(f"{fach}-Tabelle nicht gefunden.")
    
    return noten_data, averages

def send_via_mqtt(data, averages):
    broker_ip = "192.168.178.127"
    broker_port = 1883
    mqtt_username = "sven"
    mqtt_password = "sven"

    client = mqtt.Client()
    client.username_pw_set(mqtt_username, mqtt_password)
    client.connect(broker_ip, broker_port, 60)
    client.loop_start()

    # Sende Noten und Durchschnittswerte für jedes Fach an ein eigenes Topic
    for fach, noten in data.items():
        payload = {
            "noten": noten,
            "durchschnitt": averages.get(fach, None)
        }
        topic = f"schule/noten/{fach.replace(' ', '_')}"
        result = client.publish(topic, json.dumps(payload))
        result.wait_for_publish()

        if result.rc == mqtt.MQTT_ERR_SUCCESS:
            print(f"Daten erfolgreich gesendet: {topic}")
        else:
            print(f"Fehler beim Senden der Daten: {topic}")

    client.loop_stop()
    client.disconnect()

def print_results(data, averages):
    print("Noten-Daten:")
    for fach, noten in data.items():
        print(f"Fach: {fach}")
        for entry in noten:
            print(f"  Datum: {entry['datum']}, Noten: {entry['noten']}")

    print("\nDurchschnittswerte:")
    for fach, avg in averages.items():
        if avg is not None:
            print(f"{fach}: {avg:.2f}")
        else:
            print(f"{fach}: Keine Noten verfügbar")

if __name__ == '__main__':
    data, averages = scrape_notes()
    print_results(data, averages)
    send_via_mqtt(data, averages)
