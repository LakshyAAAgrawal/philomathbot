# Philomath Bot
A telegram chatbot to follow topics on Wikipedia and get related articles in regular interval.

## Development Setup
1. Clone the repository
2. Execute
   ```bash
   cp src/config.json.sample src/config.json
   ```
3. Enter the configuration details in src/config.json
4. create a virtual environment for python:
   ```
   virtualenv philomathbot
   ```
   Activate the virtual environment
   ```
   source philomathbot/bin/activate
   ```
5. Install the required modules:
   ```
   pip install -r requirements.txt
   ```
6. Run the bot
   ```
   cd src/
   python3 main.py
   ```	
