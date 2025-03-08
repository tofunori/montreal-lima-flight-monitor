#!/usr/bin/env python3
"""
Flight Assistant with LLM Integration
====================================

This script provides a natural language interface to the flight price monitor.
It allows users to make requests in conversational language rather than
using command-line arguments.

Author: Claude AI
GitHub: https://github.com/tofunori/montreal-lima-flight-monitor
"""

import os
import sys
import json
import logging
import argparse
import subprocess
import requests
from datetime import datetime, timedelta

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler("flight_assistant.log"),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# LLM API Settings - using OpenRouter with Mistral Small 24B model
OPENROUTER_API_KEY = os.environ.get("OPENROUTER_API_KEY", "")
OPENROUTER_API_URL = "https://openrouter.ai/api/v1/chat/completions"
LLM_MODEL = "mistralai/mistral-small-24b-instruct-2501:free"

def process_natural_language(query):
    """
    Process a natural language query using an LLM to extract flight search parameters.
    
    Args:
        query (str): Natural language query from the user
        
    Returns:
        dict: Extracted parameters for flight search
    """
    # If no API key is set, use a simpler rule-based approach
    if not OPENROUTER_API_KEY:
        logger.warning("No LLM API key set. Using basic keyword extraction.")
        return basic_parameter_extraction(query)
    
    # Prepare prompt for the LLM
    system_prompt = """
    You are a flight search assistant that helps extract structured parameters from natural language queries.
    Extract the following information from the user's query:
    - Origin city/airport
    - Destination city/airport
    - Departure date or date range
    - Return date or date range (if applicable)
    - Maximum number of stops preferred
    - Budget constraints
    - Preferred airlines (if mentioned)
    - Currency
    - Any other special requirements
    
    Format your response as a JSON object with these parameters. Use airport codes when possible.
    If information is not provided, use null for that field.
    """
    
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {OPENROUTER_API_KEY}",
            "HTTP-Referer": "https://github.com/tofunori/montreal-lima-flight-monitor", # Replace with your website
            "X-Title": "Montreal-Lima Flight Monitor"
        }
        
        data = {
            "model": LLM_MODEL,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": query}
            ]
        }
        
        logger.info(f"Sending query to LLM: {query[:100]}...")
        response = requests.post(OPENROUTER_API_URL, headers=headers, json=data)
        
        if response.status_code == 200:
            result = response.json()
            assistant_message = result["choices"][0]["message"]["content"]
            
            # Try to extract JSON from the response
            try:
                # Look for JSON block in the response
                json_start = assistant_message.find('{')
                json_end = assistant_message.rfind('}') + 1
                
                if json_start >= 0 and json_end > 0:
                    json_str = assistant_message[json_start:json_end]
                    params = json.loads(json_str)
                    return process_extracted_parameters(params)
                else:
                    logger.error("Could not find JSON in LLM response")
                    return basic_parameter_extraction(query)
            except json.JSONDecodeError:
                logger.error("Could not parse JSON from LLM response")
                return basic_parameter_extraction(query)
        else:
            logger.error(f"Error from LLM API: {response.status_code} - {response.text}")
            return basic_parameter_extraction(query)
            
    except Exception as e:
        logger.error(f"Error processing with LLM: {str(e)}")
        return basic_parameter_extraction(query)

def basic_parameter_extraction(query):
    """
    Extract flight parameters from a query using simple keyword matching.
    This is a fallback if LLM processing is not available.
    
    Args:
        query (str): Natural language query
        
    Returns:
        dict: Extracted parameters for flight search
    """
    query = query.lower()
    params = {
        "origin": None,
        "destination": None,
        "depart_date": None,
        "return_date": None,
        "max_stops": 3,
        "budget": None,
        "currency": "CAD",
        "flexible": True,
        "range": 3
    }
    
    # Simple city/airport extraction
    cities = {
        "montreal": "YUL",
        "lima": "LIM",
        "cusco": "CUZ",
        "la paz": "LPB",
        "toronto": "YYZ",
        "new york": "JFK",
        "mexico city": "MEX",
        "bogota": "BOG"
    }
    
    # Extract origin and destination
    for city, code in cities.items():
        if f"from {city}" in query or f"de {city}" in query:
            params["origin"] = code
        elif f"to {city}" in query or f"à {city}" in query or f"a {city}" in query:
            params["destination"] = code
    
    # Extract dates
    # This is a very basic implementation and would need to be much more sophisticated
    months = {
        "january": "01", "février": "02", "march": "03", "april": "04", 
        "may": "05", "juin": "06", "july": "07", "august": "08", 
        "september": "09", "october": "10", "november": "11", "december": "12",
        "jan": "01", "fév": "02", "mar": "03", "apr": "04", 
        "mai": "05", "jun": "06", "jul": "07", "aug": "08", 
        "sep": "09", "oct": "10", "nov": "11", "dec": "12"
    }
    
    # Very basic date extraction
    for month, month_num in months.items():
        if month in query:
            if params["depart_date"] is None:
                params["depart_date"] = f"2025-{month_num}-15"  # Default to middle of month
            elif params["return_date"] is None:
                params["return_date"] = f"2025-{month_num}-25"  # Default to later in month
    
    # Extract budget
    import re
    budget_match = re.search(r'(\d+)\s*\$|\$\s*(\d+)', query)
    if budget_match:
        budget = budget_match.group(1) or budget_match.group(2)
        params["budget"] = float(budget)
    
    # Extract stops
    for i in range(5):
        if f"{i} stop" in query or f"{i} escale" in query:
            params["max_stops"] = i
    
    # Default dates if none found
    if params["depart_date"] is None:
        # Default to 3 months from now
        future_date = datetime.now() + timedelta(days=90)
        params["depart_date"] = future_date.strftime("%Y-%m-%d")
    
    if params["return_date"] is None and "one way" not in query and "aller simple" not in query:
        # Default to 2 weeks after departure
        depart_date = datetime.strptime(params["depart_date"], "%Y-%m-%d")
        return_date = depart_date + timedelta(days=14)
        params["return_date"] = return_date.strftime("%Y-%m-%d")
    
    return params

def process_extracted_parameters(params):
    """
    Process and validate parameters extracted by the LLM.
    
    Args:
        params (dict): Raw parameters from LLM
        
    Returns:
        dict: Processed and validated parameters
    """
    processed = {
        "origin": None,
        "destination": None,
        "depart_date": None,
        "return_date": None,
        "max_stops": 3,
        "budget": None,
        "currency": "CAD",
        "flexible": True,
        "range": 3
    }
    
    # Copy over simple parameters
    for key in ["origin", "destination", "max_stops", "currency"]:
        if key in params and params[key]:
            processed[key] = params[key]
    
    # Process budget
    if "budget" in params and params["budget"]:
        try:
            processed["budget"] = float(params["budget"])
        except (ValueError, TypeError):
            logger.warning(f"Could not convert budget to float: {params['budget']}")
    
    # Process dates
    if "departure_date" in params and params["departure_date"]:
        # Try to parse the date
        try:
            # Handle date ranges
            if " to " in params["departure_date"]:
                start_date, end_date = params["departure_date"].split(" to ")
                processed["depart_date"] = parse_date(start_date)
                processed["flexible"] = True
            else:
                processed["depart_date"] = parse_date(params["departure_date"])
        except Exception as e:
            logger.warning(f"Error parsing departure date: {str(e)}")
    
    if "return_date" in params and params["return_date"]:
        try:
            # Handle date ranges
            if " to " in params["return_date"]:
                start_date, end_date = params["return_date"].split(" to ")
                processed["return_date"] = parse_date(end_date)  # Use the end of the range
                processed["flexible"] = True
            else:
                processed["return_date"] = parse_date(params["return_date"])
        except Exception as e:
            logger.warning(f"Error parsing return date: {str(e)}")
    
    # Default dates if none found
    if processed["depart_date"] is None:
        # Default to 3 months from now
        future_date = datetime.now() + timedelta(days=90)
        processed["depart_date"] = future_date.strftime("%Y-%m-%d")
    
    if processed["return_date"] is None and params.get("trip_type") != "one-way":
        # Default to 2 weeks after departure
        depart_date = datetime.strptime(processed["depart_date"], "%Y-%m-%d")
        return_date = depart_date + timedelta(days=14)
        processed["return_date"] = return_date.strftime("%Y-%m-%d")
    
    return processed

def parse_date(date_str):
    """
    Parse a date string in various formats
    
    Args:
        date_str (str): Date string to parse
        
    Returns:
        str: Date in YYYY-MM-DD format
    """
    formats = [
        "%Y-%m-%d",
        "%d/%m/%Y",
        "%m/%d/%Y",
        "%B %d, %Y",
        "%d %B %Y",
        "%b %d, %Y",
        "%d %b %Y"
    ]
    
    for fmt in formats:
        try:
            date_obj = datetime.strptime(date_str, fmt)
            return date_obj.strftime("%Y-%m-%d")
        except ValueError:
            continue
    
    # If no format matches, try extracting year, month, day with regex
    import re
    year_match = re.search(r'20\d\d', date_str)
    year = year_match.group(0) if year_match else "2025"
    
    month_dict = {
        "jan": "01", "fév": "02", "mar": "03", "apr": "04", 
        "may": "05", "jun": "06", "jul": "07", "aug": "08", 
        "sep": "09", "oct": "10", "nov": "11", "dec": "12",
        "january": "01", "february": "02", "march": "03", "april": "04", 
        "may": "05", "june": "06", "july": "07", "august": "08", 
        "september": "09", "october": "10", "november": "11", "december": "12"
    }
    
    month = "01"  # Default
    for m, num in month_dict.items():
        if m in date_str.lower():
            month = num
            break
    
    day_match = re.search(r'\b(\d{1,2})\b', date_str)
    day = day_match.group(0).zfill(2) if day_match else "15"  # Default to middle of month
    
    return f"{year}-{month}-{day}"

def run_flight_monitor(params):
    """
    Run the flight_monitor.py script with the extracted parameters
    
    Args:
        params (dict): Extracted and processed parameters
        
    Returns:
        str: Command output
    """
    cmd = ["python", "flight_monitor.py"]
    
    # Looking at the actual flight_monitor.py code, I don't see any date parameters
    # in the argument parser. The script just uses TARGET_DEPARTURE_DATE and TARGET_RETURN_DATE constants.
    # So we can't pass the dates directly via command line arguments.
    
    if params.get("origin"):
        cmd.extend(["--origin", params["origin"]])
    
    if params.get("destination"):
        cmd.extend(["--destination", params["destination"]])
    
    if params.get("max_stops") is not None:
        cmd.extend(["--max-stops", str(params["max_stops"])])
    
    if params.get("budget"):
        cmd.extend(["--threshold", str(params["budget"])])
    
    if params.get("currency"):
        cmd.extend(["--currency", params["currency"]])
    
    if params.get("flexible"):
        cmd.append("--flexible")
    
    if params.get("range"):
        cmd.extend(["--range", str(params["range"])])
    
    # Run in test mode
    cmd.append("--test")
    
    # Execute command
    cmd_str = " ".join(cmd)
    logger.info(f"Running command: {cmd_str}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True)
        if result.returncode == 0:
            logger.info("Command executed successfully")
            return result.stdout
        else:
            logger.error(f"Command failed with exit code {result.returncode}")
            logger.error(f"STDERR: {result.stderr}")
            return f"Error executing command: {result.stderr}"
    except Exception as e:
        logger.error(f"Error running flight_monitor.py: {str(e)}")
        return f"Error: {str(e)}"

def generate_response(query, params, result):
    """
    Generate a natural language response based on the search results
    
    Args:
        query (str): Original user query
        params (dict): Extracted parameters
        result (str): Output from flight_monitor.py
        
    Returns:
        str: Natural language response
    """
    if not OPENROUTER_API_KEY:
        # Simple rule-based response if no LLM available
        response = f"J'ai recherché des vols avec les paramètres suivants:\n"
        response += f"- Origine: {params['origin']}\n"
        response += f"- Destination: {params['destination']}\n"
        response += f"- Date de départ: {params['depart_date']}\n"
        
        if params['return_date']:
            response += f"- Date de retour: {params['return_date']}\n"
        
        response += f"- Maximum d'escales: {params['max_stops']}\n"
        
        if params['budget']:
            response += f"- Budget maximum: {params['budget']} {params['currency']}\n"
        
        # Extract key information from result
        if "No flight offers found" in result:
            response += "\nJe n'ai pas trouvé de vols correspondant à ces critères. Essayez peut-être avec plus d'escales ou des dates différentes."
        else:
            # Try to extract price information
            import re
            price_match = re.search(r"Cheapest price: \$([\d\.]+)", result)
            if price_match:
                price = price_match.group(1)
                response += f"\nJ'ai trouvé un vol à ${price} {params['currency']}.\n"
            
            # Try to extract airline information
            airline_match = re.search(r"with (.+?)(?=\n|$)", result)
            if airline_match:
                airlines = airline_match.group(1)
                response += f"Compagnie(s) aérienne(s): {airlines}\n"
            
            # Try to extract booking links
            response += "\nConsultez les résultats complets dans le terminal pour voir les liens de réservation."
        
        return response
    
    else:
        # Use LLM to generate a more natural response
        try:
            system_prompt = """
            You are a bilingual (French/English) flight assistant helping users find flights. 
            Generate a natural, conversational response based on the original query and the flight search results.
            Respond in the same language as the user's query.
            
            Highlight the most important information:
            - Price and airline if a flight was found
            - Any booking links or next steps
            - Suggestions if no flights were found
            
            Keep your response concise and friendly. If the user spoke French, respond in French.
            """
            
            headers = {
                "Content-Type": "application/json",
                "Authorization": f"Bearer {OPENROUTER_API_KEY}",
                "HTTP-Referer": "https://github.com/tofunori/montreal-lima-flight-monitor", # Replace with your website
                "X-Title": "Montreal-Lima Flight Monitor"
            }
            
            # Prepare the content for the LLM
            content = f"""
            Original user query: {query}
            
            Extracted search parameters:
            {json.dumps(params, indent=2)}
            
            Flight search results:
            {result[:2000]}  # Limit length to avoid token limits
            """
            
            data = {
                "model": LLM_MODEL,
                "messages": [
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": content}
                ]
            }
            
            response = requests.post(OPENROUTER_API_URL, headers=headers, json=data)
            
            if response.status_code == 200:
                result = response.json()
                return result["choices"][0]["message"]["content"]
            else:
                logger.error(f"Error from LLM API: {response.status_code} - {response.text}")
                # Fall back to simple response
                return generate_response(query, params, result)
                
        except Exception as e:
            logger.error(f"Error generating response with LLM: {str(e)}")
            # Fall back to simple response
            return generate_response(query, params, result)

def main():
    """Main function to run the flight assistant."""
    parser = argparse.ArgumentParser(description="Flight Assistant with LLM Integration")
    parser.add_argument("query", nargs="*", help="Natural language query (e.g., 'find flights from Montreal to Lima in May 2025')")
    parser.add_argument("--interactive", action="store_true", help="Run in interactive mode")
    
    args = parser.parse_args()
    
    if args.interactive:
        print("🛫 Assistant de vol interactif (tapez 'quit' pour quitter)")
        print("Exemples de questions:")
        print("- Trouve-moi des vols de Montréal à Lima en mai 2025")
        print("- Je cherche un vol de YUL à CUZ fin mai avec maximum 3 escales")
        print("- Flights from Montreal to Lima under $900 CAD in June")
        
        while True:
            query = input("\n> ")
            
            if query.lower() in ["quit", "exit", "q", "quitter"]:
                break
            
            if not query.strip():
                continue
                
            print("Traitement de votre demande...")
            params = process_natural_language(query)
            print(f"Paramètres détectés: {json.dumps(params, indent=2, ensure_ascii=False)}")
            
            result = run_flight_monitor(params)
            response = generate_response(query, params, result)
            
            print("\n" + "="*50)
            print(response)
            print("="*50)
    
    elif args.query:
        query = " ".join(args.query)
        params = process_natural_language(query)
        print(f"Paramètres détectés: {json.dumps(params, indent=2, ensure_ascii=False)}")
        
        result = run_flight_monitor(params)
        response = generate_response(query, params, result)
        
        print("\n" + "="*50)
        print(response)
        print("="*50)
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
