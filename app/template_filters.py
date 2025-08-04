# app/template_filters.py
"""Custom Jinja2 filters for the application templates."""

def shorten_wallet_address(address, start_chars=2, end_chars=4):
    """
    Shorten a wallet address for display.
    
    Args:
        address (str): The full wallet address.
        start_chars (int): Number of characters to show from the start (after 0x).
        end_chars (int): Number of characters to show from the end.
        
    Returns:
        str: Shortened address or the original if it's too short.
    """
    if not address:
        return "Unknown"
    
    # Remove '0x' prefix for calculation if present
    prefix = ""
    clean_address = address
    if address.startswith("0x") or address.startswith("0X"):
        prefix = address[:2]
        clean_address = address[2:]
        
    total_needed = start_chars + end_chars
    if len(clean_address) <= total_needed:
        return address  # Return original if too short
        
    return f"{prefix}{clean_address[:start_chars]}...{clean_address[-end_chars:]}"