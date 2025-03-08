#!/usr/bin/env python3
"""
Simplified runner for the Montreal to Lima Flight Price Monitor.
Uses configuration from .env file or environment variables.
"""

import logging
from flight_monitor import FlightPriceMonitor
from config import (
    AMADEUS_API_KEY, 
    AMADEUS_API_SECRET,
    ORIGIN, 
    DESTINATION,
    PRICE_THRESHOLD,
    CHECK_INTERVAL_HOURS,
    NOTIFICATION_EMAIL,
    get_smtp_settings
)

def main():
    """Run the flight price monitor with configuration from environment variables."""
    # Configure logging
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler("flight_monitor.log"),
            logging.StreamHandler()
        ]
    )
    logger = logging.getLogger(__name__)
    
    logger.info("Starting Montreal to Lima Flight Price Monitor")
    logger.info(f"Monitoring flights from {ORIGIN} to {DESTINATION}")
    logger.info(f"Price threshold: ${PRICE_THRESHOLD:.2f} CAD")
    logger.info(f"Check interval: {CHECK_INTERVAL_HOURS} hours")
    
    # Create the monitor
    monitor = FlightPriceMonitor(
        api_key=AMADEUS_API_KEY,
        api_secret=AMADEUS_API_SECRET,
        origin=ORIGIN,
        destination=DESTINATION,
        email=NOTIFICATION_EMAIL,
        price_threshold=PRICE_THRESHOLD,
        check_interval_hours=CHECK_INTERVAL_HOURS,
        flexible_dates=True,  # Enable flexible dates by default
        days_range=3,  # Check ±3 days around each target date
        smtp_settings=get_smtp_settings()
    )
    
    try:
        # Start monitoring
        monitor.start_monitoring()
    except KeyboardInterrupt:
        logger.info("Monitoring stopped by user")
    except Exception as e:
        logger.error(f"Error in monitoring: {str(e)}")
        raise

if __name__ == "__main__":
    main()
