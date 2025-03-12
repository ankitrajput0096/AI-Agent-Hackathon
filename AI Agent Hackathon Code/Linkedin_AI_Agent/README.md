# LinkedIn Connection Request Sender

This project automates the process of sending connection requests on LinkedIn based on user-defined search queries. It utilizes the LinkedIn API and a custom query processor to find relevant profiles and send personalized connection messages.

## Features

- Search for LinkedIn profiles based on keywords and other parameters.
- Send personalized connection requests with auto-generated messages.
- Debugging and testing modes for development.

## Requirements

- Python 3.7 or higher
- Required Python packages listed in `requirements.txt`

## Setup Instructions

1. **Clone the repository**:
   ```bash
   git clone https://github.com/yourusername/linkedin-connection-request-sender.git
   cd linkedin-connection-request-sender
   ```

2. **Install dependencies**:
   ```bash
   pip install -r requirements.txt
   ```

3. **Set up environment variables**:
   Create a `.env` file in the root directory and add your LinkedIn credentials and GROQ API key:
   ```plaintext
   LINKEDIN_EMAIL=your_email@example.com
   LINKEDIN_PASSWORD=your_password
   GROQ_API_KEY=your_groq_api_key
   ```

4. **Run the application**:
   ```bash
   python main.py
   ```

5. **Usage**:
   - Enter your search query when prompted.
   - You can specify which profiles to connect with by entering their corresponding numbers.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any improvements or bug fixes.