# Shooting Score Tracker

This project is a Telegram bot designed for participants of a shooting group to submit their shooting results via private messages. The bot ensures that only members of a specified group can send their results and maintains a leaderboard that is updated bi-weekly.

## Features

- Users can submit their best shooting series and the number of tens/central tens
- Users must give consent to data processing before using the bot
- The bot compares new submissions with previous results and notifies users if their new results are worse
- Special encouraging messages are sent when users submit successful results
- Users are categorized into different skill groups based on their scores (Beginners, Advanced, Professionals)
- Special handling for child users with positive feedback on improvement
- A leaderboard is generated and published every two weeks on Monday mornings
- Users can check their current results using the `/status` command
- Admin functionality to manage user data and results

## Project Structure

```
shooting-score-tracker
├── data                       # Directory for storing database files
│   ├── consent.db             # Database storing user consent information
│   └── scoreboard.db          # Database storing shooting scores and leaderboard data
│   └── scoreboard_YYYY-MM-DD.db # Daily backup of the scoreboard database
├── docker-compose.yml         # Configuration for Docker Compose deployment
├── Dockerfile                 # Instructions for building the Docker image
├── policy.pdf                 # PDF document containing the usage policy
├── README.md                  # Project documentation
├── requirements.txt           # Python dependencies
└── src                        # Source code directory
    ├── config.py              # Application configuration settings
    ├── database               # Database-related code
    │   ├── consent_db.py      # Database operations for user consent
    │   ├── __init__.py        # Makes the directory a Python package
    │   └── results_db.py      # Database operations for shooting results
    ├── main.py                # Application entry point
    ├── publish_leaderboard.py # Script to publish the leaderboard
    └── user                   # User-related functionality
        ├── admin.py           # Admin functionality for managing users
        ├── consent.py         # Handling user consent logic
        ├── __init__.py        # Makes the directory a Python package
        ├── leaderboard.py     # Leaderboard generation and management
        ├── membership.py      # Group membership verification
        └── messages.py        # Message handling and formatting
```

## Setup Instructions

1. Clone the repository:
   ```
   git clone <repository-url>
   cd shooting-score-tracker
   ```

2. Create a virtual environment and activate it:
   ```
   python -m venv venv
   source venv/bin/activate  # On Windows use `venv\Scripts\activate`
   ```

3. Install the required dependencies:
   ```
   pip install -r requirements.txt
   ```

4. Create a `.env` file with the following variables:
   ```
   BOT_TOKEN=your_telegram_bot_token
   CHAT_ID=your_target_group_chat_id
   DATA_DIR=./data  # Optional, defaults to ./data
   ```

5. Ensure that a `policy.pdf` file exists in the project directory. This file contains the usage policy that users need to agree to before using the bot.

6. Run the bot:
   ```
   python src/main.py
   ```

## Usage

### For Users
- Start using the bot by sending `/start` command and agreeing to the data processing policy
- Submit results by sending a message with your best series and the number of tens in the format: `92 3`
- Use the `/status` command to check your current results
- Use the `/leaderboard` command to view the leaderboard for your skill group
- Use the `/leaderboard_all` command to view the leaderboard for all skill groups
- Use the `/revoke` command to revoke your consent for data processing
- Use the `/help` command to view the list of available commands

### For Admins
The bot includes admin functionality for managing users and their data:
- Admin commands can be accessed by authorized administrators
- Admin functions include modifying user results and deleting user data

## Docker Deployment

To deploy the application using Docker:

1. Make sure Docker and Docker Compose are installed
2. Build and start the containers:
   ```
   docker-compose up -d
   ```
3. The bot will run in the background and restart automatically if it crashes

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any enhancements or bug fixes.