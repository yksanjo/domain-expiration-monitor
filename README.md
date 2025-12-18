# DomainWatch 🌐

> **Domain Expiration Monitor** - Monitor multiple domains and get alerts before they expire. Never lose a domain due to expiration again.

[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)
[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![Status: Active](https://img.shields.io/badge/status-active-success.svg)](https://github.com/yksanjo/DomainWatch)
[![GitHub stars](https://img.shields.io/github/stars/yksanjo/DomainWatch?style=social)](https://github.com/yksanjo/DomainWatch)

**DomainWatch** keeps track of all your domains' expiration dates and sends you alerts before they expire. Perfect for agencies, developers, and businesses managing multiple domains.

## Features

- 🌐 Multi-domain monitoring
- ⏰ Expiration date tracking
- 🔔 Email/Slack notifications
- 📊 Domain status dashboard
- 📅 Configurable alert thresholds
- 🔄 Auto-renewal reminders

## Installation

```bash
pip install -r requirements.txt
```

## Configuration

Create a `.env` file:

```env
# Notification Settings
EMAIL_TO=your-email@example.com
SLACK_WEBHOOK_URL=https://hooks.slack.com/services/YOUR/WEBHOOK/URL

# Alert Settings
ALERT_DAYS_BEFORE=30,14,7,1  # Days before expiration to alert
```

## Usage

### Add Domain

```bash
python monitor.py --add example.com
```

### Check All Domains

```bash
python monitor.py --check
```

### List Monitored Domains

```bash
python monitor.py --list
```

### Remove Domain

```bash
python monitor.py --remove example.com
```

### Start Continuous Monitoring

```bash
python monitor.py --watch
```

## Domain Data Sources

The monitor uses WHOIS data to check expiration dates. Supported:
- All standard TLDs (.com, .org, .net, etc.)
- Country code TLDs
- New gTLDs

## License

MIT License


