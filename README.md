# TeleWatch

TeleWatch is a Python application that monitors Telegram messages and forwards them to organized forum topics using Telegram bots. It helps you keep track of conversations across multiple accounts and chats in a centralized forum structure.

## ⚠️ Development Status

**This project is currently in active development and should be considered unstable.**

**WARNING: Do not use this application with your main/primary Telegram accounts!**

- Database schema and configuration format may change without notice
- Breaking changes may be introduced in future updates
- Data loss or corruption is possible during development

**Recommendations:**
- Use only test accounts for development and testing
- Backup any important data before running the application
- Expect frequent updates that may require reconfiguration
- Monitor the repository for breaking changes and migration guides

## Features

- **Multi-account support**: Monitor multiple Telegram user accounts simultaneously
- **Bot integration**: Use Telegram bots to forward and organize messages
- **Forum organization**: Automatically create forum topics for each chat/user
- **Message tracking**: Track new messages, deletions, and media files
- **Blacklist/whitelist support (Limited)**: Control which chats to monitor
- **Media handling**: Download and forward media files including photos, videos, and voice messages
- **Self-destructing media**: Special handling for messages with TTL (time-to-live)

## Requirements

- Python 3.13+
- Telegram API credentials (app_id and app_hash)
- Telegram bot tokens
- User account credentials (phone numbers and passwords)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/MRRollMan/TeleWatch.git
cd TeleWatch
```

2. Install dependencies:
```bash
pip install -r requirements.txt
```

3. Create configuration file:
```bash
cp config.json.example config.json
```

4. Edit `config.json` with your credentials (see Configuration section)

## Configuration

Create a `config.json` file based on the example:

```json
{
  "app_id": "1234567",
  "app_hash": "abcdef1234567890abcdef1234567890",
  "forum_name": "TeleWatch",
  "forum_about": "TeleWatch monitoring forum",
  "files_topic_title": "Files",
  "bots": [
    {"name": "monitor_bot", "token": "123456789:ABCDEFghijklmnopqrstuvwxyz12345678"}
  ],
  "users": [
    {"name": "main_account", "phone": "+1234567890", "password": "your_2fa_password"},
    {"name": "secondary_account", "phone": "+0987654321", "password": "your_2fa_password"}
  ]
}
```

### Configuration Parameters

- **app_id** & **app_hash**: Telegram API credentials (get from https://my.telegram.org)
- **forum_name**: Name for the monitoring forum that will be created
- **forum_about**: Description for the forum
- **files_topic_title**: Name for the topic where media files will be organized
- **bots**: Array of bot configurations with name and token
- **users**: Array of user accounts to monitor with session name, phone, and 2FA password (if specified)

## Usage

1. Run the application:
```bash
python main.py
```

2. On first run, you'll need to:
   - Authenticate each user account (enter verification codes)
   - The application will automatically create a forum for each user
   - Bots will be added to the forums with appropriate permissions

3. The application will:
   - Monitor all conversations from configured accounts
   - Create topic threads for each chat/contact
   - Forward messages to appropriate topics
   - Track message deletions (Limited)
   - Handle media files and self-destructing content

## Features in Detail

### Message Monitoring
- [x] Monitors private messages (group chats and channels in the future)
- [ ] Monitors edited messages
- [ ] Configurable filtering (ignore users/groups/channels)

### Forum Organization
- [x] Automatic forum creation for each monitored account
- [x] Individual topics for each chat/contact
- [x] Pinned information messages with contact details

### Bot Management
- [x] Multiple bot support for load balancing
- [x] Automatic bot addition to forums
- [x] Administrative permissions management
- [x] Topic creation and management

### Media Handling
- [ ] Download and forward photos, videos, voice messages
- [x] Special handling for self-destructing media
- [x] Organized file storage in dedicated topics

## Disclaimer

**IMPORTANT: This project is created solely for educational purposes to demonstrate Telegram API usage and Python programming concepts.**

This software is **NOT recommended for use in any way that violates Telegram's Terms of Service or applicable laws**. 

Users must:
- Ensure full compliance with [Telegram's Terms of Service](https://telegram.org/tos)
- Respect privacy rights and obtain proper consent before monitoring conversations
- Comply with all applicable local, national, and international laws regarding data privacy and communication monitoring
- Use this software only for legitimate educational, research, or personal learning purposes

The developers:
- Do not endorse or encourage any misuse of this software
- Are not responsible for any violations of terms of service, privacy laws, or other legal issues arising from the use of this application

**Use at your own risk and responsibility.**

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## Support

For issues and questions, please create an issue in the repository.
