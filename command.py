#!/usr/bin/env python3
# encoding: utf-8

import sys
import json
import argparse
import webbrowser
from urllib.parse import urlparse, urlencode
from workflow import Workflow, web
from common import get_stored_data, save_stored_data

log = None

def load_web_buttons():
    """Load web buttons from storage"""
    return get_stored_data(wf, 'web_buttons') or []

def save_web_buttons(buttons):
    """Save web buttons to storage"""
    save_stored_data(wf, 'web_buttons', buttons)

def get_button_name_from_url(url):
    """Generate a button name from URL if not provided"""
    parsed = urlparse(url)
    return parsed.netloc.replace("www.", "")

def normalize_url(url):
    """Ensure URL has a scheme"""
    if not url.startswith(('http://', 'https://')):
        return 'https://' + url
    return url

def get_mode(button_name):
    """Get the mode for a specific button (browser or quiet)"""
    buttons = load_web_buttons()
    button = next((b for b in buttons if b['name'] == button_name), None)
    if not button:
        return 'browser'  # default mode if button not found
    return button.get('mode', 'browser')  # default to browser mode if not set

def set_mode(args):
    """Set the mode for a specific button (browser or quiet)"""
    if len(args) < 2:
        print("Error: Button name and mode required (browser or quiet)")
        return 1
    
    button_name, mode = args[0], args[1].lower()
    if mode not in ['browser', 'quiet']:
        print("Error: Invalid mode. Use 'browser' or 'quiet'")
        return 1
    
    buttons = load_web_buttons()
    button = next((b for b in buttons if b['name'] == button_name), None)
    if not button:
        print(f"Error: Button '{button_name}' not found")
        return 1
    
    button['mode'] = mode
    save_web_buttons(buttons)
    print(f"Mode for '{button_name}' set to: {mode}")
    return 0

def add_body(args):
    """Add a POST body to a web button"""
    if len(args) < 2:
        print("Error: Button name and body are required")
        return 1
    
    name = args[0]
    body = ' '.join(args[1:])
    
    buttons = load_web_buttons()
    button = next((b for b in buttons if b['name'] == name), None)
    if not button:
        print(f"Error: Button '{name}' not found")
        return 1
    
    button['body'] = body
    button['method'] = 'POST'  # Set method to POST when body is added
    save_web_buttons(buttons)
    print(f"Added POST body to {name}")
    return 0

def open_url(url, headers=None, cookies=None, button_name=None, method='GET', body=None):
    """Open URL with optional headers, cookies, and POST body"""
    try:
        # For cookies, we'll add them as URL parameters if possible
        if cookies and method == 'GET':
            parsed = urlparse(url)
            if not parsed.query:
                # Only add cookies as parameters if there are no existing parameters
                url = url + '?' + urlencode(cookies)
        
        # For headers, we'll use workflow.web
        if method == 'POST':
            r = web.post(url, headers=headers, data=body)
        else:
            if headers:
                r = web.get(url, headers=headers)
            else:
                # Just validate the URL exists
                r = web.get(url)
        
        r.raise_for_status()
        
        # Check the mode to determine how to handle the URL
        mode = get_mode(button_name) if button_name else 'browser'
        if mode == 'browser':
            if method == 'POST':
                print(f"POST request successful ({r.status_code})")
            webbrowser.open(url)
            print(f"Opened URL in browser: {url}")
        else:  # quiet mode
            print(f"URL response ({r.status_code}): {r.text[:200]}")
        
        return True
    except Exception as e:
        log.error(f"Error opening URL: {str(e)}")
        return False

def add_button(args):
    """Add a new web button"""
    if len(args) < 1:
        print("Error: URL is required")
        return 1
    
    url = normalize_url(args[0])
    name = args[1] if len(args) > 1 else get_button_name_from_url(url)
    
    buttons = load_web_buttons()
    
    # Check if button already exists
    if any(b['name'] == name for b in buttons):
        print(f"Error: Button '{name}' already exists")
        return 1
    
    new_button = {
        'name': name,
        'url': url,
        'headers': {},
        'cookies': {},
        'mode': 'browser',  # default mode
        'method': 'GET'     # default method
    }
    
    buttons.append(new_button)
    save_web_buttons(buttons)
    print(f"Added web button: {name} ({url})")
    return 0

def add_header(args):
    """Add a header to a web button"""
    if len(args) < 3:
        print("Error: Button name, header name, and value are required")
        return 1
    
    name, header_name, header_value = args[0], args[1], ' '.join(args[2:])
    buttons = load_web_buttons()
    
    button = next((b for b in buttons if b['name'] == name), None)
    if not button:
        print(f"Error: Button '{name}' not found")
        return 1
    
    if 'headers' not in button:
        button['headers'] = {}
    
    button['headers'][header_name] = header_value
    save_web_buttons(buttons)
    print(f"Added header '{header_name}' to {name}")
    return 0

def add_cookie(args):
    """Add one or more cookies to a web button"""
    if len(args) < 2:
        print("Error: Button name and cookie are required")
        return 1
    
    name = args[0]
    cookie_str = ' '.join(args[1:])
    
    # Split cookies by semicolon and strip whitespace
    cookies = [c.strip() for c in cookie_str.split(';')]
    
    buttons = load_web_buttons()
    button = next((b for b in buttons if b['name'] == name), None)
    if not button:
        print(f"Error: Button '{name}' not found")
        return 1
    
    if 'cookies' not in button:
        button['cookies'] = {}
    
    # Process each cookie
    success = True
    for cookie in cookies:
        try:
            cookie_parts = cookie.split('=', 1)
            if len(cookie_parts) != 2:
                print(f"Error: Invalid cookie format for '{cookie}'. Must be name=value")
                success = False
                continue
            cookie_name, cookie_value = cookie_parts
            button['cookies'][cookie_name.strip()] = cookie_value.strip()
            print(f"Added cookie '{cookie_name.strip()}' to {name}")
        except Exception as e:
            print(f"Error adding cookie '{cookie}': {str(e)}")
            success = False
    
    if success:
        save_web_buttons(buttons)
        return 0
    return 1

def remove_button(args):
    """Remove a web button"""
    if len(args) < 1:
        print("Error: Button name is required")
        return 1
    
    name = args[0]
    buttons = load_web_buttons()
    
    if not any(b['name'] == name for b in buttons):
        print(f"Error: Button '{name}' not found")
        return 1
    
    buttons = [b for b in buttons if b['name'] != name]
    save_web_buttons(buttons)
    print(f"Removed web button: {name}")
    return 0

def open_button(args):
    """Open a web button"""
    if len(args) < 1:
        print("Error: Button name is required")
        return 1
    
    name = args[0]
    buttons = load_web_buttons()
    
    button = next((b for b in buttons if b['name'] == name), None)
    if not button:
        print(f"Error: Button '{name}' not found")
        return 1
    
    success = open_url(
        button['url'], 
        button.get('headers'), 
        button.get('cookies'), 
        name,
        button.get('method', 'GET'),
        button.get('body')
    )
    if success:
        print(f"Opened {button['name']}")
        return 0
    else:
        print(f"Failed to open {button['name']}")
        return 1

def open_direct_url(args):
    """Open a URL directly in the browser"""
    if len(args) < 1:
        print("Error: URL is required")
        return 1
    
    url = normalize_url(args[0])
    success = open_url(url)
    if success:
        print(f"Opened URL: {url}")
        return 0
    else:
        print(f"Failed to open URL: {url}")
        return 1

def main(wf):
    parser = argparse.ArgumentParser()
    parser.add_argument('command', help='Command to execute')
    parser.add_argument('args', nargs='*', help='Command arguments')
    
    args = parser.parse_args(wf.args)
    
    if args.command == 'add':
        return add_button(args.args)
    elif args.command == 'adh':
        return add_header(args.args)
    elif args.command == 'adc':
        return add_cookie(args.args)
    elif args.command == 'adb':
        return add_body(args.args)
    elif args.command == 'remove':
        return remove_button(args.args)
    elif args.command == 'open':
        return open_button(args.args)
    elif args.command == 'open_url':
        return open_direct_url(args.args)
    elif args.command == 'mode':
        return set_mode(args.args)
    else:
        print(f"Error: Unknown command '{args.command}'")
        return 1

if __name__ == '__main__':
    wf = Workflow(update_settings={
        'github_slug': 'schwark/alfred-webbutton'
    })
    log = wf.logger
    sys.exit(wf.run(main)) 