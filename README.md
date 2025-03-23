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
├── src
│   ├── main.py          # Entry point of the bot application
│   ├── database.py      # Database operations for user results
│   ├── scheduler.py     # Scheduling tasks for leaderboard publication
│   ├── utils.py         # Utility functions for input validation and message formatting
│   └── config.py        # Configuration settings for the bot
├── data
│   └── bot_database.sqlite # SQLite database for storing user results
├── requirements.txt      # List of dependencies
├── .env.example          # Template for environment variables
├── .gitignore            # Files and directories to ignore by Git
└── README.md             # Documentation for the project
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

5. Run the bot:
   ```
   python src/main.py
   ```

## Usage

- To submit results, send a message to the bot with your best series and the number of tens.
- Use the `/status` command to check your current results.
- The leaderboard will be published in the specified group every two weeks.

## Contributing

Contributions are welcome! Please open an issue or submit a pull request for any enhancements or bug fixes.