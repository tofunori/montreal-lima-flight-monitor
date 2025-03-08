#!/usr/bin/env python3
"""
AI Agent for Flight Price Monitoring - Montreal to Lima
======================================================

This script creates an AI agent that monitors flight prices from Montreal to Lima,
sending notifications when prices drop below a specified threshold.

The script uses the Amadeus API to search for flights and monitor prices.
It runs on a schedule (e.g., daily) and can send notifications via email or SMS.

Author: Claude AI
GitHub: https://github.com/tofunori/montreal-lima-flight-monitor
"""

import os
import json
import time
import logging
import smtplib
import argparse
import schedule
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from datetime import datetime, timedelta, date
from amadeus import Client, ResponseError

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

# Default Amadeus API credentials (for test environment)
DEFAULT_API_KEY = "yUMQuHBLUG10cuUsfw8zM8Cr1MKBmoP0" 
DEFAULT_API_SECRET = "NUbxODHbGuBNvLtL"

# Specific date range for May 29 - June 9, 2025
TARGET_DEPARTURE_DATE = date(2025, 5, 29)
TARGET_RETURN_DATE = date(2025, 6, 9)

class FlightPriceMonitor:
    def __init__(self, api_key=None, api_secret=None, origin="YUL", destination="LIM", 
                 email=None, price_threshold=None, check_interval_hours=24,
                 flexible_dates=False, days_range=3, smtp_settings=None,
                 max_stops=1, specific_dates=True):
        """
        Initialize the flight price monitor.
        
        Args:
            api_key (str): Amadeus API key (defaults to env var or included test key)
            api_secret (str): Amadeus API secret (defaults to env var or included test key)
            origin (str): Origin airport code (default: YUL for Montreal)
            destination (str): Destination airport code (default: LIM for Lima)
            email (str, optional): Email to send notifications to
            price_threshold (float, optional): Price threshold for notifications
            check_interval_hours (int): How often to check prices (in hours)
            flexible_dates (bool): Whether to check prices for a range of dates
            days_range (int): Number of days before/after the target date to check
            smtp_settings (dict, optional): SMTP settings for email notifications
            max_stops (int): Maximum number of stops allowed (default: 1)
            specific_dates (bool): Use specific date range May 29 - June 9, 2025
        """
        # Try to get API credentials from environment variables first, then use defaults
        self.api_key = api_key or os.environ.get('AMADEUS_API_KEY', DEFAULT_API_KEY)
        self.api_secret = api_secret or os.environ.get('AMADEUS_API_SECRET', DEFAULT_API_SECRET)
        
        self.origin = origin
        self.destination = destination
        self.email = email
        self.price_threshold = price_threshold
        self.check_interval_hours = check_interval_hours
        self.flexible_dates = flexible_dates
        self.days_range = days_range
        self.smtp_settings = smtp_settings
        self.lowest_price_seen = float('inf')
        self.previous_prices = {}
        self.max_stops = max_stops
        self.specific_dates = specific_dates
        
        logger.info(f"Initializing flight monitor for {origin} to {destination}")
        logger.info(f"Maximum stops: {max_stops}")
        if self.specific_dates:
            logger.info(f"Focusing on May 29 - June 9, 2025 date range")
        
        # Initialize Amadeus client
        self.amadeus = Client(
            client_id=self.api_key,
            client_secret=self.api_secret
        )
        
        # Create data directory if it doesn't exist
        if not os.path.exists('data'):
            os.makedirs('data')
            logger.info("Created data directory")
            
        # Load previous price data if it exists
        self.load_price_history()
        
    def load_price_history(self):
        """Load previous price data from file."""
        try:
            with open('data/price_history.json', 'r') as f:
                self.previous_prices = json.load(f)
                logger.info(f"Loaded price history: {len(self.previous_prices)} records")
        except (FileNotFoundError, json.JSONDecodeError):
            logger.info("No previous price history found or error reading file")
            self.previous_prices = {}
    
    def save_price_history(self):
        """Save current price data to file."""
        with open('data/price_history.json', 'w') as f:
            json.dump(self.previous_prices, f)
        logger.info(f"Saved price history: {len(self.previous_prices)} records")
    
    def generate_date_range(self, base_date, days_range):
        """
        Generate a range of dates around the base date.
        
        Args:
            base_date (datetime.date): The center date
            days_range (int): Number of days before/after to include
            
        Returns:
            list: List of dates in YYYY-MM-DD format
        """
        dates = []
        for i in range(-days_range, days_range + 1):
            date = (base_date + timedelta(days=i)).strftime("%Y-%m-%d")
            dates.append(date)
        return dates
    
    def check_prices(self, depart_date, return_date=None):
        """
        Check flight prices for a specific date or date range.
        
        Args:
            depart_date (str): Departure date in YYYY-MM-DD format
            return_date (str, optional): Return date for round trips
        
        Returns:
            list: List of flight offers
        """
        logger.info(f"Checking prices for {self.origin} to {self.destination} on {depart_date}")
        if return_date:
            logger.info(f"Return date: {return_date}")
        
        # Prepare search parameters
        search_params = {
            "originLocationCode": self.origin,
            "destinationLocationCode": self.destination,
            "departureDate": depart_date,
            "adults": 1,
            "currencyCode": "CAD",  # Canadian dollars
            "max": 20  # Increased to get more options for filtering
        }
        
        # Add return date for round trips
        if return_date:
            search_params["returnDate"] = return_date
            
        try:
            # Search for flight offers
            response = self.amadeus.shopping.flight_offers_search.get(**search_params)
            
            if not response.data:
                logger.info(f"No flights found for {depart_date}")
                return []
                
            logger.info(f"Found {len(response.data)} flight offers")
            return response.data
            
        except ResponseError as error:
            logger.error(f"Amadeus API error: {error}")
            return []
    
    def get_flight_details(self, offer):
        """
        Extract key details from a flight offer.
        
        Args:
            offer (dict): Flight offer data from Amadeus API
            
        Returns:
            dict: Dictionary with price, airlines, and offer ID
        """
        price = float(offer['price']['total'])
        airlines = []
        
        for itinerary in offer['itineraries']:
            for segment in itinerary['segments']:
                if segment['carrierCode'] not in airlines:
                    airlines.append(segment['carrierCode'])
        
        # Extract additional useful info
        segments = sum(len(itinerary['segments']) for itinerary in offer['itineraries'])
        is_direct = segments == 1
        
        # Skip flights with more than the maximum allowed stops
        # Each stop adds 1 to segment count (1 segment = direct, 2 segments = 1 stop, etc.)
        max_segments = self.max_stops + 1
        if segments > max_segments:
            logger.debug(f"Skipping flight with {segments-1} stops (more than max allowed: {self.max_stops})")
            return None
        
        # Extract departure and arrival times
        departure_time = offer['itineraries'][0]['segments'][0]['departure']['at']
        arrival_time = offer['itineraries'][0]['segments'][-1]['arrival']['at']
        
        return {
            'price': price,
            'airlines': airlines,
            'id': offer['id'],
            'is_direct': is_direct,
            'segments': segments,
            'stops': segments - 1,  # Number of stops
            'departure_time': departure_time,
            'arrival_time': arrival_time
        }
    
    def check_all_prices(self):
        """Check prices for all configured date ranges."""
        today = datetime.now().date()
        
        if self.specific_dates:
            # Generate dates focusing on the May 29 - June 9, 2025 target range
            departure_dates = []
            return_dates = []
            
            # If we're using flexible dates, add dates around the target dates
            if self.flexible_dates:
                departure_dates = self.generate_date_range(TARGET_DEPARTURE_DATE, self.days_range)
                return_dates = self.generate_date_range(TARGET_RETURN_DATE, self.days_range)
            else:
                # Just use the exact target dates
                departure_dates = [TARGET_DEPARTURE_DATE.strftime("%Y-%m-%d")]
                return_dates = [TARGET_RETURN_DATE.strftime("%Y-%m-%d")]
            
            logger.info(f"Checking {len(departure_dates)} departure dates and {len(return_dates)} return dates")
            
            # Check round-trip prices
            all_offers = []
            for depart_date in departure_dates:
                for return_date in return_dates:
                    offers = self.check_prices(depart_date, return_date)
                    
                    # Filter offers with more than max_stops
                    filtered_offers = []
                    for offer in offers:
                        details = self.get_flight_details(offer)
                        if details is not None:  # Only include if not filtered out
                            filtered_offers.append(offer)
                    
                    all_offers.extend(filtered_offers)
                    
                    # Don't overwhelm the API
                    time.sleep(1)
            
        else:
            # Original code - Generate dates for the next 3 months
            depart_dates = []
            for i in range(7, 90, 7):  # Weekly starting from 1 week ahead to 3 months
                depart_date = today + timedelta(days=i)
                
                if self.flexible_dates:
                    # Add dates around the target date
                    depart_dates.extend(self.generate_date_range(depart_date, self.days_range))
                else:
                    depart_dates.append(depart_date.strftime("%Y-%m-%d"))
            
            # Remove duplicates and sort
            depart_dates = sorted(list(set(depart_dates)))
            
            # Check prices for one-way trips
            all_offers = []
            for depart_date in depart_dates:
                offers = self.check_prices(depart_date)
                
                # Filter offers with more than max_stops
                filtered_offers = []
                for offer in offers:
                    details = self.get_flight_details(offer)
                    if details is not None:  # Only include if not filtered out
                        filtered_offers.append(offer)
                
                all_offers.extend(filtered_offers)
                
                # Don't overwhelm the API
                time.sleep(1)
        
        if not all_offers:
            logger.warning("No flight offers found for any dates")
            return
        
        # Find the cheapest offer
        cheapest_offer = min(all_offers, key=lambda x: float(x['price']['total']))
        cheapest_details = self.get_flight_details(cheapest_offer)
        
        # Update price history
        current_time = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        self.previous_prices[current_time] = cheapest_details['price']
        self.save_price_history()
        
        # Check if price dropped significantly or below threshold
        price = cheapest_details['price']
        if price < self.lowest_price_seen:
            drop_amount = self.lowest_price_seen - price
            drop_percent = (drop_amount / self.lowest_price_seen) * 100 if self.lowest_price_seen != float('inf') else 0
            
            logger.info(f"New lowest price found: ${price:.2f} (drop of ${drop_amount:.2f}, {drop_percent:.1f}%)")
            self.lowest_price_seen = price
            
            # Send notification if price is below threshold
            if self.price_threshold and price <= self.price_threshold:
                self.send_notification(cheapest_offer)
        
        logger.info(f"Cheapest price: ${price:.2f} with {', '.join(cheapest_details['airlines'])}")
        
        # Fix the nested f-string issue
        if cheapest_details['is_direct']:
            flight_type = "Direct"
        else:
            flight_type = f"Connecting ({cheapest_details['stops']} stops)"
        
        logger.info(f"{flight_type} flight with {cheapest_details['segments']} segment(s)")
        
        return cheapest_details
        
    def send_notification(self, offer):
        """
        Send notification about a price drop.
        
        Args:
            offer (dict): Flight offer data from Amadeus API
        """
        if not self.email:
            logger.info("No email configured for notifications")
            return
            
        flight_details = self.get_flight_details(offer)
        
        # Format departure and arrival times for display
        dep_dt = datetime.fromisoformat(flight_details['departure_time'].replace('Z', '+00:00'))
        arr_dt = datetime.fromisoformat(flight_details['arrival_time'].replace('Z', '+00:00'))
        dep_str = dep_dt.strftime("%Y-%m-%d %H:%M")
        arr_str = arr_dt.strftime("%Y-%m-%d %H:%M")
        
        # Create description of flight type
        if flight_details['is_direct']:
            flight_type = "Direct Flight"
        else:
            flight_type = f"Connecting Flight ({flight_details['stops']} stops)"
        
        # Create email message
        subject = f"Price Alert: Montreal to Lima - ${flight_details['price']:.2f}"
        body = f"""
        Flight Price Alert
        =================
        
        Montreal (YUL) to Lima (LIM)
        Price: ${flight_details['price']:.2f} CAD
        Airlines: {', '.join(flight_details['airlines'])}
        Departure: {dep_str}
        Arrival: {arr_str}
        {flight_type}
        
        This price is below your threshold of ${self.price_threshold}!
        Book now to secure this price!
        
        --
        Montreal-Lima Flight Monitor
        https://github.com/tofunori/montreal-lima-flight-monitor
        """
        
        try:
            self.send_email(subject, body)
            logger.info(f"Sent price alert notification to {self.email}")
        except Exception as e:
            logger.error(f"Failed to send notification: {str(e)}")
    
    def send_email(self, subject, body):
        """
        Send an email notification.
        
        Args:
            subject (str): Email subject
            body (str): Email body text
        """
        if self.smtp_settings:
            # Use provided SMTP settings
            sender_email = self.smtp_settings.get("sender_email")
            password = self.smtp_settings.get("password")
            smtp_server = self.smtp_settings.get("smtp_server")
            smtp_port = self.smtp_settings.get("smtp_port")
            
            message = MIMEMultipart()
            message["From"] = sender_email
            message["To"] = self.email
            message["Subject"] = subject
            
            message.attach(MIMEText(body, "plain"))
            
            try:
                with smtplib.SMTP_SSL(smtp_server, smtp_port) as server:
                    server.login(sender_email, password)
                    server.sendmail(sender_email, self.email, message.as_string())
                logger.info(f"Email sent successfully to {self.email}")
            except Exception as e:
                logger.error(f"Failed to send email: {str(e)}")
        else:
            # Just log the email content for demo purposes
            logger.info(f"Subject: {subject}")
            logger.info(f"Body: {body}")
            logger.info("No SMTP settings provided - email not actually sent")
        
    def start_monitoring(self):
        """Start the monitoring schedule."""
        # Run once immediately
        self.check_all_prices()
        
        # Schedule regular checks
        schedule.every(self.check_interval_hours).hours.do(self.check_all_prices)
        
        logger.info(f"Monitoring started - checking every {self.check_interval_hours} hours")
        
        # Run the scheduler
        try:
            while True:
                schedule.run_pending()
                time.sleep(60)
        except KeyboardInterrupt:
            logger.info("Monitoring stopped by user")
        except Exception as e:
            logger.error(f"Error in monitoring: {str(e)}")
            raise

def main():
    """Main function to run the flight price monitor."""
    parser = argparse.ArgumentParser(description="Flight Price Monitor for Montreal to Lima")
    parser.add_argument("--api-key", help="Amadeus API key (defaults to environment variable AMADEUS_API_KEY)")
    parser.add_argument("--api-secret", help="Amadeus API secret (defaults to environment variable AMADEUS_API_SECRET)")
    parser.add_argument("--origin", default="YUL", help="Origin airport code (default: YUL)")
    parser.add_argument("--destination", default="LIM", help="Destination airport code (default: LIM)")
    parser.add_argument("--email", help="Email for price notifications")
    parser.add_argument("--threshold", type=float, help="Price threshold for notifications")
    parser.add_argument("--interval", type=int, default=24, help="Check interval in hours")
    parser.add_argument("--flexible", action="store_true", help="Check flexible dates")
    parser.add_argument("--range", type=int, default=3, help="Days range for flexible dates")
    parser.add_argument("--max-stops", type=int, default=1, help="Maximum number of stops (default: 1)")
    parser.add_argument("--any-dates", action="store_true", help="Check any dates (not just May 29-June 9, 2025)")
    parser.add_argument("--test", action="store_true", help="Run once and exit (don't start scheduler)")
    
    args = parser.parse_args()
    
    monitor = FlightPriceMonitor(
        api_key=args.api_key,
        api_secret=args.api_secret,
        origin=args.origin,
        destination=args.destination,
        email=args.email,
        price_threshold=args.threshold,
        check_interval_hours=args.interval,
        flexible_dates=args.flexible,
        days_range=args.range,
        max_stops=args.max_stops,
        specific_dates=not args.any_dates
    )
    
    try:
        if args.test:
            # Just run once and exit
            results = monitor.check_all_prices()
            logger.info("Test completed. Exiting.")
            return results
        else:
            # Start continuous monitoring
            monitor.start_monitoring()
    except KeyboardInterrupt:
        logger.info("Monitoring stopped by user")
    except Exception as e:
        logger.error(f"Error in monitoring: {str(e)}")
        raise

if __name__ == "__main__":
    main()
