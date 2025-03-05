import streamlit as st
import openai
import requests
import re
from datetime import datetime, timedelta

# Set up your API keys here
openai.api_key = st.secrets["OPENAI_API_KEY"]
aviationstack_api_key = st.secrets["AVIATIONSTACK_API_KEY"]
openweather_api_key = st.secrets["OPENWEATHER_API_KEY"]

# Initialize session state to keep track of conversation history
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "system", "content": "You are a friendly and helpful airline customer service assistant. Engage with the user warmly, like a human would. You can assist with flight status, flight availability, booking assistance, baggage policies, cancellation policies, frequent flyer program information, and provide real-time updates including weather information."}
    ]
    st.session_state.greeted = False

# Function to get flight status from AviationStack
def get_flight_status(flight_number):
    url = "http://api.aviationstack.com/v1/flights"
    params = {
        'access_key': aviationstack_api_key,
        'flight_iata': flight_number
    }
    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()
        if 'data' in data and len(data['data']) > 0:
            flight_info = data['data'][0]
            airline = flight_info.get('airline', {}).get('name', 'Unknown Airline')
            flight_iata = flight_info.get('flight', {}).get('iata', 'Unknown Flight')
            flight_status = flight_info.get('flight_status', 'Status not available')
            departure_airport = flight_info.get('departure', {}).get('airport', 'Unknown Departure Airport')
            arrival_airport = flight_info.get('arrival', {}).get('airport', 'Unknown Arrival Airport')
            departure_time = flight_info.get('departure', {}).get('scheduled', 'Unknown Departure Time')
            arrival_time = flight_info.get('arrival', {}).get('scheduled', 'Unknown Arrival Time')
            departure_terminal = flight_info.get('departure', {}).get('terminal', 'N/A')
            departure_gate = flight_info.get('departure', {}).get('gate', 'N/A')
            arrival_terminal = flight_info.get('arrival', {}).get('terminal', 'N/A')
            arrival_gate = flight_info.get('arrival', {}).get('gate', 'N/A')

            # Get weather information
            departure_iata = flight_info.get('departure', {}).get('iata')
            arrival_iata = flight_info.get('arrival', {}).get('iata')
            departure_weather = get_weather_info(departure_iata)
            arrival_weather = get_weather_info(arrival_iata)

            flight_details = (
                f"**Flight Status for {flight_iata}:**\n"
                f"- **Airline:** {airline}\n"
                f"- **Status:** {flight_status.capitalize()}\n"
                f"- **Departure Airport:** {departure_airport}\n"
                f"  - **Terminal:** {departure_terminal}\n"
                f"  - **Gate:** {departure_gate}\n"
                f"- **Scheduled Departure:** {departure_time}\n"
                f"- **Arrival Airport:** {arrival_airport}\n"
                f"  - **Terminal:** {arrival_terminal}\n"
                f"  - **Gate:** {arrival_gate}\n"
                f"- **Scheduled Arrival:** {arrival_time}\n"
                f"\n**Departure Weather at {departure_airport}:**\n{departure_weather}"
                f"\n**Arrival Weather at {arrival_airport}:**\n{arrival_weather}"
            )
            return flight_details
        else:
            return "I'm sorry, I couldn't find any data for that flight number. Please double-check the flight number and try again."
    else:
        return f"Error: Unable to retrieve data (Status Code: {response.status_code}). Please try again later."

# Function to get flight schedules from AviationStack
def get_flight_schedules(departure_city, arrival_city, date):
    url = "http://api.aviationstack.com/v1/flights"
    params = {
        'access_key': aviationstack_api_key,
        'dep_iata': departure_city,
        'arr_iata': arrival_city,
        'flight_date': date
    }
    response = requests.get(url, params=params)

    if response.status_code == 200:
        data = response.json()

        # Check for error in API response
        if 'error' in data:
            api_error_message = data['error']['message']
            return f"Sorry, there was an error retrieving flight data: {api_error_message}"

        if 'data' in data and len(data['data']) > 0:
            flights_info = []
            for flight in data['data']:
                airline = flight.get('airline', {}).get('name', 'Unknown Airline')
                flight_iata = flight.get('flight', {}).get('iata', 'Unknown Flight')
                departure_airport = flight.get('departure', {}).get('airport', 'Unknown Departure Airport')
                departure_time = flight.get('departure', {}).get('scheduled', 'Unknown Departure Time')
                arrival_airport = flight.get('arrival', {}).get('airport', 'Unknown Arrival Airport')
                arrival_time = flight.get('arrival', {}).get('scheduled', 'Unknown Arrival Time')
                flight_status = flight.get('flight_status', 'Status not available').capitalize()
                departure_terminal = flight.get('departure', {}).get('terminal', 'N/A')
                departure_gate = flight.get('departure', {}).get('gate', 'N/A')
                arrival_terminal = flight.get('arrival', {}).get('terminal', 'N/A')
                arrival_gate = flight.get('arrival', {}).get('gate', 'N/A')

                flight_details = (
                    f"- **Airline:** {airline}\n"
                    f"  **Flight Number:** {flight_iata}\n"
                    f"  **Status:** {flight_status}\n"
                    f"  **Departure Airport:** {departure_airport}\n"
                    f"    - **Terminal:** {departure_terminal}\n"
                    f"    - **Gate:** {departure_gate}\n"
                    f"  **Scheduled Departure:** {departure_time}\n"
                    f"  **Arrival Airport:** {arrival_airport}\n"
                    f"    - **Terminal:** {arrival_terminal}\n"
                    f"    - **Gate:** {arrival_gate}\n"
                    f"  **Scheduled Arrival:** {arrival_time}\n"
                )
                flights_info.append(flight_details)

            response_message = f"Here are the available flights from {departure_city.upper()} to {arrival_city.upper()} on {date}:\n\n"
            response_message += "\n".join(flights_info)
            return response_message
        else:
            return f"I'm sorry, I couldn't find any flights from {departure_city.upper()} to {arrival_city.upper()} on {date}."
    else:
        return f"Error: Unable to retrieve data (Status Code: {response.status_code}). Please try again later."

# Function to get weather information from OpenWeatherMap
def get_weather_info(location):
    # If the location is an IATA code, map it to a city name
    iata_to_city = {
        'JFK': 'New York',
        'LAX': 'Los Angeles',
        'SFO': 'San Francisco',
        'ORD': 'Chicago',
        'MIA': 'Miami',
        'ATL': 'Atlanta',
        'DFW': 'Dallas',
        'DEN': 'Denver',
        'SEA': 'Seattle',
        'BOS': 'Boston',
        # Add more mappings as needed
    }

    if location is None or location == '':
        return "Weather information not available."

    city_name = iata_to_city.get(location.upper(), location)

    url = "http://api.openweathermap.org/data/2.5/weather"
    params = {
        'q': city_name,
        'appid': openweather_api_key,
        'units': 'metric'
    }
    response = requests.get(url, params=params)
    if response.status_code == 200:
        weather_data = response.json()
        description = weather_data['weather'][0]['description'].capitalize()
        temperature = weather_data['main']['temp']
        humidity = weather_data['main']['humidity']
        weather_info = (
            f"- **Condition:** {description}\n"
            f"- **Temperature:** {temperature}°C\n"
            f"- **Humidity:** {humidity}%"
        )
        return weather_info
    else:
        return "Weather information not available."

# Function to check if the user is asking about baggage policies
def is_baggage_inquiry(user_input):
    baggage_keywords = ['baggage', 'luggage', 'bag', 'carry-on', 'checked bag', 'baggage allowance', 'baggage policy', 'baggage fees']
    return any(keyword in user_input.lower() for keyword in baggage_keywords)

# Function to provide baggage policy information
def get_baggage_policy():
    baggage_policy = (
        "**Baggage Policy Information:**\n"
        "- **Carry-on Baggage:** Passengers are allowed one carry-on bag and one personal item.\n"
        "- **Checked Baggage:** The allowance for checked bags depends on your ticket class.\n"
        "  - Economy Class: 1 bag up to 23 kg (50 lbs)\n"
        "  - Business Class: 2 bags up to 32 kg (70 lbs) each\n"
        "- **Excess Baggage Fees:** Additional fees apply for overweight or extra bags.\n"
        "- **Special Items:** Sports equipment and musical instruments may have special regulations.\n"
        "\nFor more detailed information, please visit our [Baggage Policy](https://www.exampleairline.com/baggage-policy) page or let me know if you have specific questions!"
    )
    return baggage_policy

# Function to check if the user is asking about cancellation policies
def is_cancellation_inquiry(user_input):
    cancellation_keywords = ['cancel', 'change', 'refund', 'reschedule', 'cancellation policy', 'change flight']
    return any(keyword in user_input.lower() for keyword in cancellation_keywords)

# Function to provide cancellation and change policy information
def get_cancellation_policy():
    cancellation_policy = (
        "**Cancellation and Change Policy:**\n"
        "- **24-Hour Flexibility:** You can change or cancel your flight within 24 hours of booking without any fees.\n"
        "- **Fees:** After 24 hours, fees may apply depending on your fare type.\n"
        "  - Economy Saver: Changes and cancellations are subject to a fee of $200.\n"
        "  - Economy Flex: Changes are free; cancellations are subject to a fee of $100.\n"
        "  - Business Class: Changes and cancellations are free.\n"
        "- **Refunds:** Refunds will be processed to the original form of payment within 7-10 business days.\n"
        "\nIf you need assistance with changing or cancelling your flight, please provide your booking reference or contact our customer service at 1-800-EXAMPLE."
    )
    return cancellation_policy

# Function to check if the user is asking about frequent flyer program
def is_frequent_flyer_inquiry(user_input):
    ff_keywords = ['frequent flyer', 'loyalty program', 'miles', 'points', 'membership', 'reward program']
    return any(keyword in user_input.lower() for keyword in ff_keywords)

# Function to provide frequent flyer program information
def get_frequent_flyer_info():
    ff_info = (
        "**Frequent Flyer Program Information:**\n"
        "- **Enrollment:** Join our Frequent Flyer Program for free and start earning miles today!\n"
        "- **Earning Miles:** Earn miles on flights, hotel stays, car rentals, and with our partners.\n"
        "- **Redeeming Miles:** Redeem miles for flights, seat upgrades, and other rewards.\n"
        "- **Tier Benefits:** Enjoy exclusive benefits like priority boarding, lounge access, and extra baggage allowance as you move up tiers.\n"
        "\nTo enroll or learn more, visit our [Frequent Flyer Program](https://www.exampleairline.com/frequent-flyer) page or let me know if you have questions!"
    )
    return ff_info

# Function to check if the user is asking about weather
def is_weather_inquiry(user_input):
    weather_keywords = ['weather', 'temperature', 'forecast', 'weather like']
    return any(keyword in user_input.lower() for keyword in weather_keywords)

# Function to provide weather information
def get_weather_response(user_input):
    # Convert input to lowercase
    user_input = user_input.lower()
    # Remove punctuation for better matching
    user_input_clean = re.sub(r'[^\w\s]', '', user_input)
    # Improved regex pattern to match various weather inquiries
    location_match = re.search(
        r'weather.*(?:at|in|like at|like in|for)?\s+([a-zA-Z\s]{3,})', user_input_clean
    )
    if location_match:
        location = location_match.group(1).strip()
        # Remove any trailing words like 'airport'
        location = re.sub(r'\bairport\b', '', location).strip()
    else:
        # Default to extracting the last word as the location
        words = user_input_clean.split()
        if words:
            location = words[-1]
        else:
            location = ''
    
    # Check if location is valid
    if not location:
        return "I'm sorry, I couldn't determine the location for the weather information. Please specify the city or airport."

    weather_info = get_weather_info(location)
    response = f"**Current weather at {location.title()}:**\n{weather_info}"
    return response

# Function to extract flight number from user input
def extract_flight_number(user_input):
    flight_number_match = re.search(r'\b([A-Za-z]{2}\s?\d{1,4})\b', user_input)
    if flight_number_match:
        flight_number = flight_number_match.group(1).replace(" ", "")
        return flight_number
    else:
        return None

# Function to extract city codes and date from user input
def extract_flight_search_details(user_input):
    # Remove ordinal indicators
    user_input = re.sub(r'(\d+)(st|nd|rd|th)', r'\1', user_input.lower())

    # Regular expressions to find dates
    date_match = re.search(r'\b(\w+\s\d{1,2}(?:,|\s)\d{4})\b', user_input)
    if not date_match:
        date_match = re.search(r'\b(\d{4}/\d{2}/\d{2})\b', user_input)
    if not date_match:
        date_match = re.search(r'\b(\d{4}-\d{2}-\d{2})\b', user_input)
    if not date_match:
        date_match = re.search(r'\b(\d{1,2}/\d{1,2}/\d{4})\b', user_input)
    if date_match:
        date_str = date_match.group(1)
        # Try multiple date formats
        for fmt in ('%B %d %Y', '%B %d, %Y', '%Y/%m/%d', '%Y-%m-%d', '%m/%d/%Y'):
            try:
                date = datetime.strptime(date_str, fmt).strftime('%Y-%m-%d')
                break
            except ValueError:
                date = None
    else:
        date = None

    # Map city names to IATA codes
    city_to_iata = {
        'new york': 'JFK',
        'los angeles': 'LAX',
        'san francisco': 'SFO',
        'chicago': 'ORD',
        'miami': 'MIA',
        'california': 'LAX',
        'atlanta': 'ATL',
        'dallas': 'DFW',
        'denver': 'DEN',
        'seattle': 'SEA',
        'boston': 'BOS',
        # Add more cities as needed
    }

    # Extract departure and arrival cities
    departure_city = None
    arrival_city = None
    for city in city_to_iata.keys():
        if city in user_input.lower():
            if any(prefix + city in user_input.lower() for prefix in ['from ', 'leaving ', 'departing ']):
                departure_city = city_to_iata[city]
            elif any(prefix + city in user_input.lower() for prefix in ['to ', 'arriving at ', 'going to ', 'destination ', 'arriving in ']):
                arrival_city = city_to_iata[city]
    return departure_city, arrival_city, date

# Function to extract destination from flight information
def extract_destination_from_flight_info(flight_info_text):
    match = re.search(r'\*\*Arrival Airport:\*\*\s+(.+)', flight_info_text)
    if match:
        arrival_airport = match.group(1).strip()
        return arrival_airport
    return None

# Function to get chatbot response from OpenAI
def get_chatbot_response(messages):
    try:
        response = openai.ChatCompletion.create(
            model="gpt-3.5-turbo",
            messages=messages
        )
        return response.choices[0].message['content'].strip()
    except Exception as e:
        return f"Error: {str(e)}"

# Function to handle user input submission
def submit_input():
    user_input = st.session_state.user_input
    if user_input:
        st.session_state.messages.append({"role": "user", "content": user_input})

        # Flags to check which functionalities are requested
        flight_status_requested = any(keyword in user_input.lower() for keyword in ['status', 'delayed', 'delay'])
        weather_requested = any(keyword in user_input.lower() for keyword in ['weather', 'temperature', 'forecast', 'weather like'])
        baggage_inquiry = is_baggage_inquiry(user_input)
        cancellation_inquiry = is_cancellation_inquiry(user_input)
        frequent_flyer_inquiry = is_frequent_flyer_inquiry(user_input)

        # Check if user is asking for flight status by flight number
        flight_number = extract_flight_number(user_input)
        if flight_number and flight_status_requested:
            flight_info = get_flight_status(flight_number)
            st.session_state.messages.append({"role": "assistant", "content": flight_info})
            st.write("Chatbot:", flight_info)

            # If weather at destination is requested
            if weather_requested:
                destination = extract_destination_from_flight_info(flight_info)
                if destination:
                    weather_info = get_weather_info(destination)
                    response = f"**Weather at {destination}:**\n{weather_info}"
                else:
                    response = "I'm sorry, I couldn't determine the destination for the weather information."
                st.session_state.messages.append({"role": "assistant", "content": response})
                st.write("Chatbot:", response)
            return

        # Check if user is asking for flight schedules between cities
        departure_city, arrival_city, date = extract_flight_search_details(user_input)
        if departure_city and arrival_city and date:
            flight_info = get_flight_schedules(departure_city, arrival_city, date)
            st.session_state.messages.append({"role": "assistant", "content": flight_info})
            st.write("Chatbot:", flight_info)
            return

        # Check for weather inquiries not related to flight status
        if weather_requested and not flight_number:
            weather_info = get_weather_response(user_input)
            st.session_state.messages.append({"role": "assistant", "content": weather_info})
            st.write("Chatbot:", weather_info)
            return

        # Check for baggage policy inquiries
        if baggage_inquiry:
            baggage_info = get_baggage_policy()
            st.session_state.messages.append({"role": "assistant", "content": baggage_info})
            st.write("Chatbot:", baggage_info)
            return

        # Check for cancellation policy inquiries
        if cancellation_inquiry:
            cancellation_info = get_cancellation_policy()
            st.session_state.messages.append({"role": "assistant", "content": cancellation_info})
            st.write("Chatbot:", cancellation_info)
            return

        # Check for frequent flyer program inquiries
        if frequent_flyer_inquiry:
            ff_info = get_frequent_flyer_info()
            st.session_state.messages.append({"role": "assistant", "content": ff_info})
            st.write("Chatbot:", ff_info)
            return

        # Default response using OpenAI API
        response = get_chatbot_response(st.session_state.messages)
        st.session_state.messages.append({"role": "assistant", "content": response})
        st.write("Chatbot:", response)
    else:
        st.write("Chatbot: Please enter a message.")

    st.session_state.user_input = ""

# Streamlit app setup
st.title("Airline Customer Service Chatbot")
st.write("Ask about flight status, flight availability, booking assistance, baggage policies, cancellation policies, frequent flyer program, weather information, or other airline services!")

# Personalized greeting for first-time users
if not st.session_state.greeted:
    greeting_message = "Hello! Welcome to our airline chatbot service 😊. How can I assist you today?"
    st.session_state.messages.append({"role": "assistant", "content": greeting_message})
    st.session_state.greeted = True
    st.write("Chatbot:", greeting_message)

# Input from user
user_input = st.text_input("Your message:", key="user_input", on_change=submit_input)

# Display conversation history
st.write("### Conversation History")
for message in st.session_state.messages[1:]:  # Skip the system message
    if message["role"] == "user":
        st.write(f"**You**: {message['content']}")
    else:
        st.write(f"**Chatbot**: {message['content']}")
