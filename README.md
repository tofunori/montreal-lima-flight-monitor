# Montreal to Lima Flight Price Monitor

An AI-powered flight price monitoring agent that tracks prices from Montreal (YUL) to Lima (LIM) and notifies you when they drop below your target threshold.

This tool uses the Amadeus Flight Offers Search API to regularly check flight prices and can send you notifications via email when it finds a great deal.

![Flight Monitoring Banner](https://placehold.co/1200x300/EEE/31343C?text=Montreal+to+Lima+Flight+Monitor&font=montserrat)

## Features

- 🔍 **Automated Price Tracking**: Regularly checks flight prices from Montreal to Lima
- 📊 **Price History**: Saves historical price data to help you understand trends
- 📧 **Email Notifications**: Sends alerts when prices drop below your target
- 📅 **Flexible Date Search**: Can search a range of dates to find the best deals
- 🔄 **Customizable Schedule**: Configure how often to check for new prices
- 🛫 **Airline and Route Details**: Provides detailed information about each flight option
- ✈️ **Connection Filtering**: Limit results to direct flights or maximum one stop
- 🗓️ **Specific Date Range**: Optimized for May 29 - June 9, 2025 travel window

## Prerequisites

- Python 3.8 or higher
- An Amadeus for Developers account (free)
- (Optional) Email account for notifications

## Quick Start

### 1. Clone the repository

```bash
git clone https://github.com/tofunori/montreal-lima-flight-monitor.git
cd montreal-lima-flight-monitor
```

### 2. Install dependencies

```bash
pip install -r requirements.txt
```

### 3. Run with default settings (test mode)

The script includes test API credentials that you can use to try it out immediately:

```bash
python flight_monitor.py --test
```

This will perform a single price check and display the results without starting the continuous monitoring.

### 4. Check May 29 - June 9, 2025 with maximum one stop

```bash
python flight_monitor.py --interval 24 --max-stops 1 --email your@email.com
```

This will check prices daily for the May 29 - June 9, 2025 travel window, filtering to only include flights with at most one stop.

## Configuration Options

### Command Line Arguments

| Argument | Description | Default |
|----------|-------------|---------|
| `--api-key` | Amadeus API key | Uses env var or included test key |
| `--api-secret` | Amadeus API secret | Uses env var or included test key |
| `--origin` | Origin airport code | YUL (Montreal) |
| `--destination` | Destination airport code | LIM (Lima) |
| `--email` | Email for price notifications | None |
| `--threshold` | Price threshold for notifications | None |
| `--interval` | Check interval in hours | 24 |
| `--flexible` | Check flexible dates | False |
| `--range` | Days range for flexible dates | 3 |
| `--max-stops` | Maximum number of stops | 1 |
| `--any-dates` | Check any dates (not just May 29-June 9) | False |
| `--test` | Run once and exit | False |

### Environment Variables

Instead of passing API credentials on the command line, you can set them as environment variables:

```bash
export AMADEUS_API_KEY=your_api_key
export AMADEUS_API_SECRET=your_api_secret
```

On Windows:
```cmd
set AMADEUS_API_KEY=your_api_key
set AMADEUS_API_SECRET=your_api_secret
```

### Getting Your Own API Credentials

While this script includes test API credentials, it's recommended to obtain your own:

1. Sign up for a free account at [Amadeus for Developers](https://developers.amadeus.com/)
2. Create a new application under "My Self-Service Workspace"
3. Choose the "Test environment" to get started (no credit card required)
4. Copy your API Key and API Secret

## Usage Examples

### Basic Usage - Monitor Prices for May 29 - June 9, 2025

```bash
python flight_monitor.py --threshold 800 --email your@email.com
```

This will:
- Start monitoring flights from Montreal to Lima for May 29 - June 9, 2025
- Check prices every 24 hours
- Send an email notification when a price below $800 CAD is found
- Only include flights with at most one stop

### Check Daily with Flexible Dates Around May 29 - June 9

```bash
python flight_monitor.py --flexible --range 3 --threshold 750 --interval 24
```

This will:
- Check prices daily
- Search for flights on a range of dates (±3 days around May 29 for departure and June 9 for return)
- Set alert threshold to $750 CAD
- Only include flights with at most one stop

### Search for Direct Flights Only

```bash
python flight_monitor.py --max-stops 0 --threshold 900
```

This will:
- Only check for direct flights (no stops)
- Set alert threshold to $900 CAD
- Focus on May 29 - June 9, 2025 date range

### Check Any Date (Not Just May 29 - June 9)

```bash
python flight_monitor.py --any-dates --flexible --threshold 700
```

This will:
- Check flights for various dates (not just the May 29 - June 9 period)
- Use flexible date search
- Set alert threshold to $700 CAD
- Only include flights with at most one stop

## Email Notifications Setup

To receive email notifications when prices drop below your threshold, you need to:

1. Provide your email address with the `--email` parameter
2. Configure SMTP settings by editing the script (see the `send_email` method)

Alternatively, you can set up the agent on an AWS Lambda function or other cloud service and use their email capabilities.

## Running as a Background Service

### Using Screen (Linux/macOS)

```bash
screen -S flight_monitor
python flight_monitor.py --threshold 800 --email your@email.com
# Press Ctrl+A, then D to detach
```

To reconnect to the session:
```bash
screen -r flight_monitor
```

### Using systemd (Linux)

Create a service file:
```bash
sudo nano /etc/systemd/system/flight-monitor.service
```

Add this content:
```
[Unit]
Description=Montreal to Lima Flight Price Monitor
After=network.target

[Service]
User=yourusername
WorkingDirectory=/path/to/montreal-lima-flight-monitor
ExecStart=/usr/bin/python3 /path/to/montreal-lima-flight-monitor/flight_monitor.py --threshold 800 --email your@email.com
Restart=on-failure

[Install]
WantedBy=multi-user.target
```

Start the service:
```bash
sudo systemctl daemon-reload
sudo systemctl start flight-monitor
sudo systemctl enable flight-monitor
```

## Deployment Options

### AWS Lambda

You can deploy this script to AWS Lambda to run on a schedule without maintaining a server:

1. Modify the script to use AWS SES for email notifications
2. Package the script and dependencies into a Lambda deployment package
3. Set up a CloudWatch Events rule to trigger the function on your desired schedule

### Heroku

You can also deploy to Heroku using a worker dyno:

1. Create a `Procfile` with: `worker: python flight_monitor.py --threshold 800 --email your@email.com`
2. Push to Heroku and scale the worker dyno up

## Security Considerations

- Do not hardcode your real API credentials or email SMTP passwords in the script
- Use environment variables or a secure credential manager
- The included test credentials are for demonstration purposes only and have limited functionality

## Troubleshooting

### API Rate Limits

Amadeus API has rate limits. If you encounter errors, try:
- Increasing the interval between checks
- Reducing the number of dates you're searching
- Moving to the Amadeus production environment (requires registration with credit card)

### No Flights Found

If no flights are found:
- Verify the airport codes are correct
- Try searching further in advance
- Check if there are direct flights available between your chosen airports

### Email Notifications Not Working

- Check your SMTP settings
- Verify your email address is correct
- Check spam/junk folder
- Some email providers block automated emails

## License

This project is released under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [Amadeus for Developers](https://developers.amadeus.com/) for providing the flight search API
- This project was created with assistance from Claude AI

---

## About Montreal to Lima Flights

- The journey between Montreal (YUL) and Lima (LIM) is approximately 6,600 km
- Flight duration is typically 8-12 hours depending on connections
- Common airlines serving this route include Air Canada, United Airlines, Avianca, and LATAM
- Many flights connect through cities like Toronto, Newark, Mexico City, or Bogotá
- Best time to visit Lima is during their winter (May to October) when it's less humid

## Contribute

Contributions are welcome! Please feel free to submit a Pull Request.
