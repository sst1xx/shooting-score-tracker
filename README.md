# Shooting Score Tracker

This project is a Telegram bot designed for participants of a shooting group to submit their shooting results via private messages. The bot ensures that only members of a specified group can send their results and maintains a leaderboard that is updated bi-weekly.

## Features

- Users can submit their best shooting series and the number of tens.
- Users can attach a photo with their results. //TODO
- The bot compares new submissions with previous results and notifies users if their new results are worse.
- A leaderboard is generated and published every two weeks on Monday mornings (depends on your cron settings)
- Users can check their current results using the `/status` command.

## Project Structure

```
shooting-score-tracker
├── data                       # Directory for storing database files
│   ├── consent.db             # Database storing user consent information
│   └── scoreboard.db          # Database storing shooting scores and leaderboard data
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

4. Create a `.env` file based on the `.env.example` template and add your Telegram bot token.

5. Ensure that a `policy.pdf` file exists in the project directory. This file is required for the Docker build to complete successfully.

6. Users must read and agree to the policy before they can use the bot. The bot will prompt new users to review and accept the terms outlined in the policy document.

7. Run the bot:
   ```
   python src/main.py
   ```

## Usage

- To submit results, send a message to the bot with your best series and the number of tens.
- Use the `/status` command to check your current results.
- The leaderboard will be published in the specified group every two weeks.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any enhancements or bug fixes.