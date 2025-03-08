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

# LLM Provider Configuration
LLM_PROVIDERS = {
    # OpenRouter configuration
    "openrouter": {
        "api_key_env": "OPENROUTER_API_KEY",
        "api_url": "https://openrouter.ai/api/v1/chat/completions",
        "models": {
            "mistral-small": "mistralai/mistral-small-24b-instruct-2501:free",
            "mixtral": "mistralai/mixtral-8x7b-instruct-v0.1:free",
            "gemma": "google/gemma-1.1-7b-it:free",
            "llama3": "meta-llama/llama-3-8b-instruct:free",
            "phi": "microsoft/phi-2:free",
        },
        "headers": lambda api_key: {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}",
            "HTTP-Referer": "https://github.com/tofunori/montreal-lima-flight-monitor",
            "X-Title": "Montreal-Lima Flight Monitor"
        },
        "request_format": lambda model, system_prompt, user_content: {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ]
        },
        "response_parser": lambda response: response["choices"][0]["message"]["content"]
    },
    
    # OpenAI configuration
    "openai": {
        "api_key_env": "OPENAI_API_KEY",
        "api_url": "https://api.openai.com/v1/chat/completions",
        "models": {
            "gpt-3.5-turbo": "gpt-3.5-turbo",
            "gpt-4": "gpt-4",
            "gpt-4-turbo": "gpt-4-turbo-preview"
        },
        "headers": lambda api_key: {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        },
        "request_format": lambda model, system_prompt, user_content: {
            "model": model,
            "messages": [
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_content}
            ]
        },
        "response_parser": lambda response: response["choices"][0]["message"]["content"]
    },
    
    # Anthropic configuration
    "anthropic": {
        "api_key_env": "ANTHROPIC_API_KEY",
        "api_url": "https://api.anthropic.com/v1/messages",
        "models": {
            "claude-3-sonnet": "claude-3-sonnet-20240229",
            "claude-3-opus": "claude-3-opus-20240229",
            "claude-3-haiku": "claude-3-haiku-20240307",
            "claude-2": "claude-2.0"
        },
        "headers": lambda api_key: {
            "Content-Type": "application/json",
            "x-api-key": api_key,
            "anthropic-version": "2023-06-01"
        },
        "request_format": lambda model, system_prompt, user_content: {
            "model": model,
            "max_tokens": 1000,
            "system": system_prompt,
            "messages": [{"role": "user", "content": user_content}]
        },
        "response_parser": lambda response: response["content"][0]["text"]
    }
}

# Default LLM configuration - can be overridden via command line args
DEFAULT_PROVIDER = "openrouter"
DEFAULT_MODEL = "mistral-small"

def get_llm_config(provider_name=None, model_name=None):
    """
    Get the configuration for a specific LLM provider and model.
    
    Args:
        provider_name (str): Name of the LLM provider
        model_name (str): Name of the model
        
    Returns:
        tuple: (provider_config, model, api_key)
    """
    # Determine provider
    provider_name = provider_name or DEFAULT_PROVIDER
    if provider_name not in LLM_PROVIDERS:
        logger.warning(f"Provider {provider_name} not found. Using {DEFAULT_PROVIDER}.")
        provider_name = DEFAULT_PROVIDER
    
    provider_config = LLM_PROVIDERS[provider_name]
    
    # Get API key from environment variable
    api_key_env = provider_config["api_key_env"]
    api_key = os.environ.get(api_key_env, "")
    
    if not api_key:
        logger.warning(f"No API key found for {provider_name} (env: {api_key_env})")
        return None, None, None
    
    # Determine model
    model_name = model_name or DEFAULT_MODEL
    available_models = provider_config["models"]
    
    if model_name not in available_models:
        logger.warning(f"Model {model_name} not found for {provider_name}. Using default.")
        model_name = list(available_models.keys())[0]
    
    model = available_models[model_name]
    
    return provider_config, model, api_key

def process_natural_language(query, provider_name=None, model_name=None):
    """
    Process a natural language query using an LLM to extract flight search parameters.
    
    Args:
        query (str): Natural language query from the user
        provider_name (str): Name of the LLM provider
        model_name (str): Name of the model
        
    Returns:
        dict: Extracted parameters for flight search
    """
    # Get LLM configuration
    provider_config, model, api_key = get_llm_config(provider_name, model_name)
    
    # If no valid configuration, use basic keyword extraction
    if not provider_config:
        logger.warning("No valid LLM configuration. Using basic keyword extraction.")
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
        # Prepare API request
        headers = provider_config["headers"](api_key)
        request_data = provider_config["request_format"](model, system_prompt, query)
        
        # Make API request
        logger.info(f"Sending query to {provider_name} ({model_name}): {query[:100]}...")
        response = requests.post(provider_config["api_url"], headers=headers, json=request_data)
        
        if response.status_code == 200:
            result = response.json()
            assistant_message = provider_config["response_parser"](result)
            
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
    
    # Add parameters
    if params.get("origin"):
        cmd.extend(["--origin", params["origin"]])
    
    if params.get("destination"):
        cmd.extend(["--destination", params["destination"]])
    
    if params.get("depart_date"):
        # The correct parameter name in flight_monitor.py is "depart" not "depart-date"
        cmd.extend(["--depart", params["depart_date"]])
    
    if params.get("return_date"):
        # The correct parameter name in flight_monitor.py is "return" not "return-date"
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

def generate_response(query, params, result, provider_name=None, model_name=None):
    """
    Generate a natural language response based on the search results
    
    Args:
        query (str): Original user query
        params (dict): Extracted parameters
        result (str): Output from flight_monitor.py
        provider_name (str): Name of the LLM provider
        model_name (str): Name of the model
        
    Returns:
        str: Natural language response
    """
    # Get LLM configuration
    provider_config, model, api_key = get_llm_config(provider_name, model_name)
    
    # If no valid configuration, use simple rule-based response
    if not provider_config:
        return generate_simple_response(query, params, result)
    
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
        
        # Prepare the content for the LLM
        user_content = f"""
        Original user query: {query}
        
        Extracted search parameters:
        {json.dumps(params, indent=2)}
        
        Flight search results:
        {result[:2000]}  # Limit length to avoid token limits
        """
        
        # Prepare API request
        headers = provider_config["headers"](api_key)
        request_data = provider_config["request_format"](model, system_prompt, user_content)
        
        # Make API request
        response = requests.post(provider_config["api_url"], headers=headers, json=request_data)
        
        if response.status_code == 200:
            result = response.json()
            return provider_config["response_parser"](result)
        else:
            logger.error(f"Error from LLM API: {response.status_code} - {response.text}")
            # Fall back to simple response
            return generate_simple_response(query, params, result)
            
    except Exception as e:
        logger.error(f"Error generating response with LLM: {str(e)}")
        # Fall back to simple response
        return generate_simple_response(query, params, result)

def generate_simple_response(query, params, result):
    """
    Generate a simple rule-based response without using an LLM.
    
    Args:
        query (str): Original user query
        params (dict): Extracted parameters
        result (str): Output from flight_monitor.py
        
    Returns:
        str: Simple response text
    """
    # Determine language (very basic detection)
    is_french = any(word in query.lower() for word in [
        "bonjour", "vol", "prix", "cherche", "trouve", "montreal", "montréal", 
        "escale", "date", "aller", "retour", "mai", "juin", "juillet"
    ])
    
    if is_french:
        response = f"J'ai recherché des vols avec les paramètres suivants:\n"
        response += f"- Origine: {params['origin']}\n"
        response += f"- Destination: {params['destination']}\n"
        response += f"- Date de départ: {params['depart_date']}\n"
        
        if params['return_date']:
            response += f"- Date de retour: {params['return_date']}\n"
        
        response += f"- Maximum d'escales: {params['max_stops']}\n"
        
        if params['budget']:
            response += f"- Budget maximum: {params['budget']} {params['currency']}\n"
    else:
        response = f"I searched for flights with the following parameters:\n"
        response += f"- Origin: {params['origin']}\n"
        response += f"- Destination: {params['destination']}\n"
        response += f"- Departure date: {params['depart_date']}\n"
        
        if params['return_date']:
            response += f"- Return date: {params['return_date']}\n"
        
        response += f"- Maximum stops: {params['max_stops']}\n"
        
        if params['budget']:
            response += f"- Maximum budget: {params['budget']} {params['currency']}\n"
    
    # Extract key information from result
    if "No flight offers found" in result:
        if is_french:
            response += "\nJe n'ai pas trouvé de vols correspondant à ces critères. Essayez peut-être avec plus d'escales ou des dates différentes."
        else:
            response += "\nI didn't find any flights matching these criteria. You might want to try with more stops or different dates."
    else:
        # Try to extract price information
        import re
        price_match = re.search(r"Cheapest price: \$([\d\.]+)", result)
        if price_match:
            price = price_match.group(1)
            if is_french:
                response += f"\nJ'ai trouvé un vol à ${price} {params['currency']}.\n"
            else:
                response += f"\nI found a flight for ${price} {params['currency']}.\n"
        
        # Try to extract airline information
        airline_match = re.search(r"with (.+?)(?=\n|$)", result)
        if airline_match:
            airlines = airline_match.group(1)
            if is_french:
                response += f"Compagnie(s) aérienne(s): {airlines}\n"
            else:
                response += f"Airline(s): {airlines}\n"
        
        # Try to extract booking links
        if is_french:
            response += "\nConsultez les résultats complets dans le terminal pour voir les liens de réservation."
        else:
            response += "\nCheck the complete results in the terminal to see booking links."
    
    return response

def list_providers_and_models():
    """List all available LLM providers and their models."""
    print("Available LLM Providers and Models:")
    print("==================================")
    
    for provider, config in LLM_PROVIDERS.items():
        api_key_env = config["api_key_env"]
        api_key = os.environ.get(api_key_env, "")
        status = "✅ Configured" if api_key else "❌ Not configured"
        
        print(f"\n{provider.upper()} ({status}):")
        print(f"  API Key Environment Variable: {api_key_env}")
        
        print("  Available Models:")
        for model_name, model_id in config["models"].items():
            print(f"    - {model_name}: {model_id}")
    
    print("\nTo configure a provider, set the appropriate environment variable.")
    print("Example: export OPENAI_API_KEY=your_api_key")

def main():
    """Main function to run the flight assistant."""
    parser = argparse.ArgumentParser(description="Flight Assistant with LLM Integration")
    parser.add_argument("query", nargs="*", help="Natural language query (e.g., 'find flights from Montreal to Lima in May 2025')")
    parser.add_argument("--interactive", action="store_true", help="Run in interactive mode")
    parser.add_argument("--provider", help=f"LLM provider to use (default: {DEFAULT_PROVIDER})")
    parser.add_argument("--model", help=f"Model to use (default depends on provider)")
    parser.add_argument("--list", action="store_true", help="List available providers and models")
    
    args = parser.parse_args()
    
    if args.list:
        list_providers_and_models()
        return
    
    if args.interactive:
        print("🛫 Assistant de vol interactif (tapez 'quit' pour quitter)")
        print("Exemples de questions:")
        print("- Trouve-moi des vols de Montréal à Lima en mai 2025")
        print("- Je cherche un vol de YUL à CUZ fin mai avec maximum 3 escales")
        print("- Flights from Montreal to Lima under $900 CAD in June")
        
        # Show current provider and model
        provider_name = args.provider or DEFAULT_PROVIDER
        model_name = args.model or DEFAULT_MODEL
        provider_config, model, api_key = get_llm_config(provider_name, model_name)
        
        if provider_config and api_key:
            print(f"\nUsing LLM: {provider_name} / {model_name}")
        else:
            print("\nNo LLM configured. Using basic keyword extraction.")
            print("Use --list to see available providers and models.")
        
        while True:
            query = input("\n> ")
            
            if query.lower() in ["quit", "exit", "q", "quitter"]:
                break
                
            # Special commands
            if query.lower() == "providers":
                list_providers_and_models()
                continue
                
            if query.lower().startswith("use "):
                parts = query.lower().split()
                if len(parts) >= 3 and parts[0] == "use" and parts[2] == "model":
                    provider_name = parts[1]
                    model_name = parts[3] if len(parts) > 3 else None
                    provider_config, model, api_key = get_llm_config(provider_name, model_name)
                    
                    if provider_config and api_key:
                        print(f"Switched to {provider_name} / {model_name or 'default model'}")
                    else:
                        print(f"Failed to switch provider. Check if {provider_name} is configured.")
                    continue
            
            if not query.strip():
                continue
                
            print("Traitement de votre demande...")
            params = process_natural_language(query, provider_name, model_name)
            print(f"Paramètres détectés: {json.dumps(params, indent=2, ensure_ascii=False)}")
            
            result = run_flight_monitor(params)
            response = generate_response(query, params, result, provider_name, model_name)
            
            print("\n" + "="*50)
            print(response)
            print("="*50)
    
    elif args.query:
        query = " ".join(args.query)
        params = process_natural_language(query, args.provider, args.model)
        print(f"Paramètres détectés: {json.dumps(params, indent=2, ensure_ascii=False)}")
        
        result = run_flight_monitor(params)
        response = generate_response(query, params, result, args.provider, args.model)
        
        print("\n" + "="*50)
        print(response)
        print("="*50)
    
    else:
        parser.print_help()

if __name__ == "__main__":
    main()
