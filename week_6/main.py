import requests

API_KEY = "db18fd7e7dedc0cdb65dd8f3207e8a17"

def get_weather(city):
    url = f"https://api.openweathermap.org/data/2.5/weather?q={city}&appid={API_KEY}&units=metric"

    response = requests.get(url)
    data = response.json()
    print(data)

    if data["cod"] != 200:
        print("\n❌ City not found! Try again.")
        return

    print("\n------ Weather Report ------")
    print("City:", data["name"])
    print("Country:", data["sys"]["country"])
    print("Temperature:", data["main"]["temp"], "°C")
    print("Humidity:", data["main"]["humidity"], "%")
    print("Weather:", data["weather"][0]["description"].title())
    print("----------------------------")

if __name__ == "__main__":
    city = input("Enter city name: ")
    get_weather(city)
