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

# Default model settings
DEFAULT_LLM_MODEL = "mistralai/mistral-small-24b-instruct-2501:free"
DEFAULT_LLM_PROVIDER = "openrouter"  # Options: "openrouter", "openai", "anthropic", "custom"

def get_api_settings():
    """Get API settings from environment variables or command line args"""
    # Check for API key in environment
    api_key = os.environ.get("OPENROUTER_API_KEY", "")
    if not api_key:
        api_key = os.environ.get("OPENAI_API_KEY", "")
    if not api_key:
        api_key = os.environ.get("ANTHROPIC_API_KEY", "")
    
    # Check for model in environment
    model = os.environ.get("LLM_MODEL", DEFAULT_LLM_MODEL)
    
    # Check for provider in environment
    provider = os.environ.get("LLM_PROVIDER", DEFAULT_LLM_PROVIDER)
    
    # Log what was found
    logger.info(f"API Provider: {provider}")
    logger.info(f"API Model: {model}")
    logger.info(f"API Key Found: {'Yes' if api_key else 'No'}")
    
    return {
        "api_key": api_key,
        "model": model,
        "provider": provider
    }

def call_llm(system_prompt, user_prompt, api_settings):
    """
    Generic function to call an LLM based on the provider
    
    Args:
        system_prompt (str): System prompt for the LLM
        user_prompt (str): User prompt for the LLM
        api_settings (dict): Dictionary with API settings
        
    Returns:
        str: LLM response text
    """
    provider = api_settings["provider"]
    api_key = api_settings["api_key"]
    model = api_settings["model"]
    
    if not api_key:
        logger.warning("No API key found for any provider")
        return None
    
    if provider == "openrouter":
        return call_openrouter_llm(system_prompt, user_prompt, api_key, model)
    elif provider == "openai":
        return call_openai_llm(system_prompt, user_prompt, api_key, model)
    elif provider == "anthropic":
        return call_anthropic_llm(system_prompt, user_prompt, api_key, model)
    else:
        logger.error(f"Unknown provider: {provider}")
        return None

def call_openrouter_llm(system_prompt, user_prompt, api_key, model):
    """Call OpenRouter API for LLM response"""
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://github.com/tofunori/montreal-lima-flight-monitor",
            "X-Title": "Montreal-Lima Flight Monitor"
        }
        
        data = {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        }
        
        logger.info(f"Sending request to OpenRouter with model {model}")
        response = requests.post(
            "https://openrouter.ai/api/v1/chat/completions", 
            headers=headers, 
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            logger.info("Successfully received response from OpenRouter")
            return result["choices"][0]["message"]["content"]
        else:
            logger.error(f"Error from OpenRouter API: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error calling OpenRouter: {str(e)}")
        return None

def call_openai_llm(system_prompt, user_prompt, api_key, model):
    """Call OpenAI API for LLM response"""
    try:
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        data = {
            "model": model or "gpt-3.5-turbo",
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ]
        }
        
        logger.info(f"Sending request to OpenAI with model {model}")
        response = requests.post(
            "https://api.openai.com/v1/chat/completions", 
            headers=headers, 
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            logger.info("Successfully received response from OpenAI")
            return result["choices"][0]["message"]["content"]
        else:
            logger.error(f"Error from OpenAI API: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error calling OpenAI: {str(e)}")
        return None

def call_anthropic_llm(system_prompt, user_prompt, api_key, model):
    """Call Anthropic API for LLM response"""
    try:
        headers = {
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01"
        }
        
        data = {
            "model": model or "claude-3-sonnet-20240229",
            "max_tokens": 1000,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_prompt}]
        }
        
        logger.info(f"Sending request to Anthropic with model {model}")
        response = requests.post(
            "https://api.anthropic.com/v1/messages",
            headers=headers, 
            json=data
        )
        
        if response.status_code == 200:
            result = response.json()
            logger.info("Successfully received response from Anthropic")
            return result["content"][0]["text"]
        else:
            logger.error(f"Error from Anthropic API: {response.status_code} - {response.text}")
            return None
    except Exception as e:
        logger.error(f"Error calling Anthropic: {str(e)}")
        return None

def process_natural_language(query, api_settings=None):
    """
    Process a natural language query using an LLM to extract flight search parameters.
    
    Args:
        query (str): Natural language query from the user
        api_settings (dict): Optional API settings
        
    Returns:
        dict: Extracted parameters for flight search
    """
    # Get API settings if not provided
    if api_settings is None:
        api_settings = get_api_settings()
    
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
    
    # Call LLM
    assistant_message = call_llm(system_prompt, query, api_settings)
    
    if assistant_message:
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
        logger.warning("No LLM response, using basic keyword extraction")
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
    
    # Add parameters
    if params.get("origin"):
        cmd.extend(["--origin", params["origin"]])
    
    if params.get("destination"):
        cmd.extend(["--destination", params["destination"]])
    
    if params.get("depart_date"):
        # Check which parameter name is correct
        try:
            # First, check if the script has a "--help" option to see available parameters
            help_result = subprocess.run(["python", "flight_monitor.py", "--help"], capture_output=True, text=True)
            help_text = help_result.stdout.lower()
            
            # Check which parameter name exists in the help text
            if "--depart" in help_text:
                cmd.extend(["--depart", params["depart_date"]])
            elif "-l" in help_text or "--depart_date" in help_text:
                cmd.extend(["-l", params["depart_date"]])
            elif "--departure-date" in help_text:
                cmd.extend(["--departure-date", params["depart_date"]])
            else:
                # Try a common parameter name
                cmd.extend(["--depart", params["depart_date"]])
        except Exception as e:
            logger.error(f"Error checking parameter names: {str(e)}")
            # Fallback to using --depart
            cmd.extend(["--depart", params["depart_date"]])
    
    if params.get("return_date"):
        # Similar logic for return date
        try:
            if help_text and "--return" in help_text:
                cmd.extend(["--return", params["return_date"]])
            elif help_text and "-r" in help_text:
                cmd.extend(["-r", params["return_date"]])
            elif help_text and "--return_date" in help_text:
                cmd.extend(["--return_date", params["return_date"]])
            else:
                cmd.extend(["--return", params["return_date"]])
        except Exception:
            cmd.extend(["--return", params["return_date"]])
    
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

def generate_response(query, params, result, api_settings=None):
    """
    Generate a natural language response based on the search results
    
    Args:
        query (str): Original user query
        params (dict): Extracted parameters
        result (str): Output from flight_monitor.py
        api_settings (dict): Optional API settings
        
    Returns:
        str: Natural language response
    """
    # Get API settings if not provided
    if api_settings is None:
        api_settings = get_api_settings()
    
    # If no LLM available or API key, use rule-based response
    if not api_settings["api_key"]:
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
        
        # Prepare the content for the LLM
        content = f"""
        Original user query: {query}
        
        Extracted search parameters:
        {json.dumps(params, indent=2)}
        
        Flight search results:
        {result[:2000]}  # Limit length to avoid token limits
        """
        
        # Call LLM
        response_text = call_llm(system_prompt, content, api_settings)
        
        if response_text:
            return response_text
        else:
            # Fall back to simple response
            return generate_response(query, params, result, {"api_key": None})

def main():
    """Main function to run the flight assistant."""
    parser = argparse.ArgumentParser(description="Flight Assistant with LLM Integration")
    parser.add_argument("query", nargs="*", help="Natural language query (e.g., 'find flights from Montreal to Lima in May 2025')")
    parser.add_argument("--interactive", action="store_true", help="Run in interactive mode")
    parser.add_argument("--api-key", help="API key for LLM provider")
    parser.add_argument("--model", help="Model to use for LLM")
    parser.add_argument("--provider", choices=["openrouter", "openai", "anthropic", "custom"], help="LLM provider")
    
    args = parser.parse_args()
    
    # Set up API settings from command line args
    api_settings = get_api_settings()
    if args.api_key:
        api_settings["api_key"] = args.api_key
    if args.model:
        api_settings["model"] = args.model
    if args.provider:
        api_settings["provider"] = args.provider
    
    if args.interactive:
        print("🛫 Assistant de vol interactif (tapez 'quit' pour quitter)")
        print("Exemples de questions:")
        print("- Trouve-moi des vols de Montréal à Lima en mai 2025")
        print("- Je cherche un vol de YUL à CUZ fin mai avec maximum 3 escales")
        print("- Flights from Montreal to Lima under $900 CAD in June")
        print("\nCommandes spéciales:")
        print("- 'quit' ou 'exit' : Quitter l'assistant")
        print("- 'model <nom>' : Changer de modèle LLM (ex: 'model gpt-4')")
        print("- 'provider <nom>' : Changer de fournisseur LLM (ex: 'provider openai')")
        print("- 'key <clé>' : Définir la clé API (ex: 'key sk-abc123')")
        
        while True:
            query = input("\n> ")
            
            if query.lower() in ["quit", "exit", "q", "quitter"]:
                break
            
            if not query.strip():
                continue
            
            # Check for special commands
            if query.startswith("model "):
                model_name = query[6:].strip()
                api_settings["model"] = model_name
                print(f"Modèle changé pour: {model_name}")
                continue
                
            if query.startswith("provider "):
                provider_name = query[9:].strip()
                if provider_name in ["openrouter", "openai", "anthropic", "custom"]:
                    api_settings["provider"] = provider_name
                    print(f"Fournisseur changé pour: {provider_name}")
                else:
                    print(f"Fournisseur non reconnu: {provider_name}")
                    print("Options: openrouter, openai, anthropic, custom")
                continue
                
            if query.startswith("key "):
                api_key = query[4:].strip()
                api_settings["api_key"] = api_key
                print("Clé API mise à jour")
                continue
                
            print("Traitement de votre demande...")
            params = process_natural_language(query, api_settings)
            print(f"Paramètres détectés: {json.dumps(params, indent=2, ensure_ascii=False)}")
            
            result = run_flight_monitor(params)
            response = generate_response(query, params, result, api_settings)
            
            print("\n" + "="*50)
            print(response)
            print("="*50)
    
    elif args.query:
        query = " ".join(args.query)
        params = process_natural_language(query, api_settings)
        print(f"Paramètres détectés: {json.dumps(params, indent=2, ensure_ascii=False)}")
        
        result = run_flight_monitor(params)
        response = generate_response(query, params, result, api_settings)
        
        print("\n" + "="*50)
        print(response)
        print("="*50)
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
