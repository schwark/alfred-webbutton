#!/usr/bin/env python3
# encoding: utf-8

import sys
import subprocess
import time
import os
import hashlib
import re
from workflow import Workflow, ICON_WEB, ICON_ERROR, ICON_INFO, web
from common import get_stored_data, save_stored_data
from urllib.parse import urlparse, urljoin

def get_safari_current_url():
    """Get the current URL from the active Safari tab"""
    apple_script = '''
        tell application "Safari"
            if frontmost then
                tell front document
                    get URL
                end tell
            end if
        end tell
    '''
    try:
        result = subprocess.run(['osascript', '-e', apple_script], 
                              capture_output=True, 
                              text=True)
        if result.returncode == 0 and result.stdout.strip():
            return result.stdout.strip()
    except Exception as e:
        return None
    return None

def get_command_parts(query):
    """Parse the command and its arguments"""
    parts = query.split() if query else []
    command = parts[0].lower() if parts else None
    args = parts[1:] if len(parts) > 1 else []
    return command, args

def looks_like_url(text):
    """Check if text looks like a URL"""
    # Remove common prefixes
    text = text.lower().strip()
    if text.startswith(('http://', 'https://', 'www.')):
        return True
    # Check for common TLDs
    if any(text.endswith(tld) for tld in ['.com', '.org', '.net', '.edu', '.gov', '.io']):
        return True
    # Check if contains a dot and no spaces
    return '.' in text and ' ' not in text

def get_command_suggestions(query):
    """Get list of commands that start with the query"""
    commands = {
        'add': 'Add a new web button',
        'adh': 'Add a header to a button',
        'adc': 'Add a cookie to a button',
        'adb': 'Add a POST body to a button',
        'mode': 'Set button mode (browser/quiet)',
        'remove': 'Remove a web button'
    }
    return [(cmd, desc) for cmd, desc in commands.items() if cmd.startswith(query.lower())]

def show_add_command(wf, args):
    """Show UI for add command"""
    if len(args) == 0:
        # Show basic help
        wf.add_item(
            title="wb add <url> [name]",
            subtitle="Add a new web button (use :cap to capture current Safari URL)",
            valid=False,
            icon=ICON_INFO
        )
        
        # Try to get current Safari URL and show as autocomplete option
        safari_url = get_safari_current_url()
        if safari_url:
            parsed = urlparse(safari_url)
            suggested_name = parsed.netloc.replace("www.", "")
            wf.add_item(
                title=f"Capture current Safari URL: {safari_url}",
                subtitle=f"↵ to add as '{suggested_name}'",
                autocomplete=f"add {safari_url} {suggested_name}",
                arg=f"add {safari_url} {suggested_name}",
                valid=True,
                icon=ICON_WEB
            )
    elif len(args) >= 1:
        url = args[0]
        name = args[1] if len(args) > 1 else None
        
        if url == ':cap':
            safari_url = get_safari_current_url()
            if safari_url:
                url = safari_url
                if not name:
                    # Generate name from URL if not provided
                    parsed = urlparse(safari_url)
                    name = parsed.netloc.replace("www.", "")
                wf.add_item(
                    title=f"Add web button: {name}",
                    subtitle=f"URL from Safari: {url}",
                    arg=f"add {url} {name}",
                    valid=True,
                    icon=ICON_WEB
                )
            else:
                wf.add_item(
                    title="Could not capture Safari URL",
                    subtitle="Make sure Safari is open and active",
                    valid=False,
                    icon=ICON_ERROR
                )
        else:
            wf.add_item(
                title=f"Add web button: {name if name else url}",
                subtitle=f"URL: {url}",
                arg=f"add {url} {name if name else ''}",
                valid=True,
                icon=ICON_WEB
            )

def escape_shell_arg(arg):
    """Escape an argument for shell execution"""
    # Replace any single quotes with '\''
    arg = arg.replace("'", "'\\''")
    # Wrap the entire argument in single quotes
    return f"'{arg}'"

def show_adh_command(wf, args):
    """Show UI for adh (add header) command"""
    if len(args) < 1:
        wf.add_item(
            title='wb adh <button-name> "<header-name>" "<header-value>"',
            subtitle="Add a header to a web button (use quotes for values with spaces)",
            valid=False,
            icon=ICON_INFO
        )
        return

    button_name = args[0]
    buttons = get_stored_data(wf, 'web_buttons') or []
    button = next((b for b in buttons if b['name'] == button_name), None)
    
    if not button:
        wf.add_item(
            title=f"Button '{button_name}' not found",
            subtitle="Please create the button first using 'wb add <url>'",
            valid=False,
            icon=ICON_ERROR
        )
        return

    if len(args) < 3:
        wf.add_item(
            title=f"Add header to {button_name}",
            subtitle='Usage: wb adh <button-name> "<header-name>" "<header-value>"',
            valid=False,
            icon=ICON_INFO
        )
    else:
        header_name, header_value = args[1], args[2]
        # Escape each argument individually
        escaped_args = [
            escape_shell_arg(button_name),
            escape_shell_arg(header_name),
            escape_shell_arg(header_value)
        ]
        arg_str = ' '.join(escaped_args)
        wf.add_item(
            title=f"Add header to {button_name}",
            subtitle=f"{header_name}: {header_value}",
            arg=f"adh {arg_str}",
            valid=True,
            icon=ICON_WEB
        )

def show_adc_command(wf, args):
    """Show UI for adc (add cookie) command"""
    if len(args) < 1:
        wf.add_item(
            title='wb adc <button-name> "<cookie1>=<value1>; cookie2=<value2>"',
            subtitle="Add one or more cookies to a web button (separate multiple cookies with ;)",
            valid=False,
            icon=ICON_INFO
        )
        return

    button_name = args[0]
    buttons = get_stored_data(wf, 'web_buttons') or []
    button = next((b for b in buttons if b['name'] == button_name), None)
    
    if not button:
        wf.add_item(
            title=f"Button '{button_name}' not found",
            subtitle="Please create the button first using 'wb add <url>'",
            valid=False,
            icon=ICON_ERROR
        )
        return

    if len(args) < 2:
        wf.add_item(
            title=f"Add cookie(s) to {button_name}",
            subtitle='Usage: wb adc <button-name> "name1=value1; name2=value2"',
            valid=False,
            icon=ICON_INFO
        )
    else:
        cookie_str = args[1]
        # Split cookies by semicolon and strip whitespace
        cookies = [c.strip() for c in cookie_str.split(';')]
        invalid_cookies = [c for c in cookies if '=' not in c]
        
        if invalid_cookies:
            # Show error for invalid cookies
            wf.add_item(
                title="Invalid cookie format",
                subtitle=f"These cookies are invalid (missing '='): {', '.join(invalid_cookies)}",
                valid=False,
                icon=ICON_ERROR
            )
        else:
            # All cookies are valid
            escaped_args = [
                escape_shell_arg(button_name),
                escape_shell_arg(cookie_str)
            ]
            arg_str = ' '.join(escaped_args)
            wf.add_item(
                title=f"Add {len(cookies)} cookie(s) to {button_name}",
                subtitle=f"Cookies: {cookie_str}",
                arg=f"adc {arg_str}",
                valid=True,
                icon=ICON_WEB
            )
            # Show individual cookies being added
            for cookie in cookies:
                wf.add_item(
                    title=f"Adding cookie: {cookie}",
                    subtitle=f"To button: {button_name}",
                    valid=False,
                    icon=ICON_INFO
                )

def show_adb_command(wf, args):
    """Show UI for adb (add body) command"""
    if len(args) < 1:
        wf.add_item(
            title='wb adb <button-name> "<body>"',
            subtitle="Add a POST body to a web button (use quotes for JSON or spaces)",
            valid=False,
            icon=ICON_INFO
        )
        return

    button_name = args[0]
    buttons = get_stored_data(wf, 'web_buttons') or []
    button = next((b for b in buttons if b['name'] == button_name), None)
    
    if not button:
        wf.add_item(
            title=f"Button '{button_name}' not found",
            subtitle="Please create the button first using 'wb add <url>'",
            valid=False,
            icon=ICON_ERROR
        )
        return

    if len(args) < 2:
        wf.add_item(
            title=f"Add POST body to {button_name}",
            subtitle='Usage: wb adb <button-name> "<body>"',
            valid=False,
            icon=ICON_INFO
        )
        if button.get('body'):
            wf.add_item(
                title="Current POST body",
                subtitle=button['body'],
                valid=False,
                icon=ICON_INFO
            )
    else:
        body = args[1]
        # Escape each argument individually
        escaped_args = [
            escape_shell_arg(button_name),
            escape_shell_arg(body)
        ]
        arg_str = ' '.join(escaped_args)
        wf.add_item(
            title=f"Add POST body to {button_name}",
            subtitle=f"Body: {body}",
            arg=f"adb {arg_str}",
            valid=True,
            icon=ICON_WEB
        )

def show_remove_command(wf, args):
    """Show UI for remove command"""
    if len(args) == 0:
        wf.add_item(
            title="wb remove <name>",
            subtitle="Remove a web button",
            valid=False,
            icon=ICON_INFO
        )
    else:
        name = args[0]
        wf.add_item(
            title=f"Remove web button: {name}",
            subtitle="This action cannot be undone",
            arg=f"remove {name}",
            valid=True,
            icon=ICON_ERROR
        )

def show_mode_command(wf, args):
    """Show mode command options"""
    if len(args) < 2:
        # Show help for mode command
        wf.add_item(
            title='Set Button Mode',
            subtitle='Usage: wb mode <button-name> <browser|quiet>',
            valid=False,
            icon=ICON_INFO
        )
        # Show list of buttons to choose from
        buttons = get_stored_data(wf, 'web_buttons') or []
        for button in buttons:
            current_mode = button.get('mode', 'browser')
            wf.add_item(
                title=f"{button['name']} ({current_mode})",
                subtitle=f"Current mode: {current_mode}. Select to change.",
                autocomplete=f"mode {button['name']} ",
                valid=False,
                icon=ICON_WEB if current_mode == 'browser' else ICON_INFO
            )
        return

    button_name = args[1]
    buttons = get_stored_data(wf, 'web_buttons') or []
    button = next((b for b in buttons if b['name'] == button_name), None)
    
    if not button:
        wf.add_item(
            title=f"Button '{button_name}' not found",
            subtitle="Please create the button first using 'wb add <url>'",
            valid=False,
            icon=ICON_ERROR
        )
        return

    if len(args) < 3:
        # Show mode options for the selected button
        current_mode = button.get('mode', 'browser')
        wf.add_item(
            title=f'Set Browser Mode for {button_name}',
            subtitle=f"Currently: {current_mode}",
            arg=f'mode {button_name} browser',
            valid=True,
            icon=ICON_WEB
        )
        wf.add_item(
            title=f'Set Quiet Mode for {button_name}',
            subtitle=f"Currently: {current_mode}",
            arg=f'mode {button_name} quiet',
            valid=True,
            icon=ICON_INFO
        )
    else:
        mode = args[2].lower()
        if mode in ['browser', 'quiet']:
            wf.add_item(
                title=f'Set Mode for {button_name}: {mode}',
                subtitle=f"Currently: {button.get('mode', 'browser')}",
                arg=f'mode {button_name} {mode}',
                valid=True,
                icon=ICON_WEB if mode == 'browser' else ICON_INFO
            )
        else:
            wf.add_item(
                title='Invalid Mode',
                subtitle="Use 'browser' or 'quiet'",
                valid=False,
                icon=ICON_ERROR
            )

def update_button_usage(wf, button_name):
    """Update the last used timestamp for a button"""
    buttons = load_web_buttons()
    button = next((b for b in buttons if b['name'] == button_name), None)
    if button:
        button['last_used'] = time.time()
        save_web_buttons(buttons)

def load_web_buttons():
    """Load web buttons from storage"""
    buttons = get_stored_data(wf, 'web_buttons')
    if buttons is None:
        buttons = []
        wf.logger.debug('No web buttons found in storage')
    else:
        wf.logger.debug(f'Loaded {len(buttons)} buttons from storage')
    
    # Ensure all buttons have a last_used field
    for button in buttons:
        if 'last_used' not in button:
            button['last_used'] = 0  # Default to 0 for never used
    return buttons

def get_favicon_path(url):
    """Get the path to the cached favicon for a URL"""
    parsed = urlparse(url)
    domain = parsed.netloc
    if not domain:
        return None
    
    # Create hash of domain to use as filename
    filename = hashlib.md5(domain.encode('utf-8')).hexdigest() + '.ico'
    cache_dir = os.path.join(wf.cachedir, 'favicons')
    
    # Ensure cache directory exists
    if not os.path.exists(cache_dir):
        os.makedirs(cache_dir)
    
    return os.path.join(cache_dir, filename)

def fetch_favicon(url):
    """Fetch and cache favicon for a URL"""
    favicon_path = get_favicon_path(url)
    if not favicon_path:
        return None
    
    # If favicon is already cached and less than a week old, use it
    if os.path.exists(favicon_path):
        if time.time() - os.path.getmtime(favicon_path) < 7 * 24 * 60 * 60:
            return favicon_path
    
    try:
        parsed = urlparse(url)
        base_url = f"{parsed.scheme}://{parsed.netloc}"
        
        # Try common favicon locations
        favicon_urls = [
            urljoin(base_url, '/favicon.ico'),
            urljoin(base_url, '/favicon.png'),
            urljoin(base_url, '/apple-touch-icon.png'),
            urljoin(base_url, '/apple-touch-icon-precomposed.png')
        ]
        
        # Try to get favicon URL from HTML
        try:
            r = web.get(base_url)
            r.raise_for_status()
            html = r.text
            
            # Find link tags with rel containing icon
            icon_pattern = r'<link[^>]+?rel=[\'"]((?:shortcut |apple-touch-)?icon)[\'"](.*?)>'
            href_pattern = r'href=[\'"](.*?)[\'"]'
            
            for match in re.finditer(icon_pattern, html, re.IGNORECASE | re.DOTALL):
                link_tag = match.group(0)
                href_match = re.search(href_pattern, link_tag)
                if href_match:
                    href = href_match.group(1)
                    favicon_urls.insert(0, urljoin(base_url, href))
        except Exception as e:
            wf.logger.debug(f"Error parsing HTML for favicon: {str(e)}")
        
        # Try each favicon URL until one works
        for favicon_url in favicon_urls:
            try:
                wf.logger.debug(f"Trying favicon URL: {favicon_url}")
                r = web.get(favicon_url, stream=True)
                r.raise_for_status()
                
                # Check content type
                content_type = r.headers.get('content-type', '').lower()
                if not any(t in content_type for t in ['image/', 'icon', 'favicon']):
                    continue
                
                with open(favicon_path, 'wb') as f:
                    for chunk in r.iter_content(chunk_size=1024):
                        f.write(chunk)
                
                # Verify file was written and has content
                if os.path.exists(favicon_path) and os.path.getsize(favicon_path) > 0:
                    return favicon_path
                else:
                    os.remove(favicon_path)
            except Exception as e:
                wf.logger.debug(f"Error fetching favicon from {favicon_url}: {str(e)}")
                continue
        
    except Exception as e:
        wf.logger.debug(f"Error in favicon fetch process for {url}: {str(e)}")
    
    return None

def show_buttons(wf, query):
    """Show list of web buttons"""
    buttons = load_web_buttons()
    
    # Sort buttons by last_used timestamp (most recent first)
    buttons.sort(key=lambda x: x.get('last_used', 0), reverse=True)
    
    # If no query, show all buttons sorted by last use
    if not query:
        if not buttons:
            wf.add_item(
                title="No web buttons found",
                subtitle="Use 'wb add <url>' to create one",
                valid=False,
                icon=ICON_INFO
            )
            return
            
        for button in buttons:
            subtitle_parts = []
            if button.get('headers'):
                subtitle_parts.append(f"{len(button['headers'])} headers")
            if button.get('cookies'):
                subtitle_parts.append(f"{len(button['cookies'])} cookies")
            if button.get('body'):
                subtitle_parts.append("POST body")
            mode = button.get('mode', 'browser')
            subtitle_parts.append(f"Mode: {mode}")
            
            subtitle = f"{button['url']} ({', '.join(subtitle_parts)})"
            
            # Get favicon for the button
            icon = fetch_favicon(button['url']) or ICON_WEB
            
            wf.add_item(
                title=button['name'],
                subtitle=subtitle,
                arg=f"open {button['name']}",
                valid=True,
                icon=icon
            )
        return
    
    # Handle URL-like queries
    if looks_like_url(query):
        wf.add_item(
            title=f"Open URL: {query}",
            subtitle="Press Enter to open in browser",
            arg=f"open_url {query}",
            valid=True,
            icon=ICON_WEB
        )
    
    # Filter and score buttons based on query
    query_lower = query.lower()
    for button in buttons:
        name = button['name'].lower()
        url = button['url'].lower()
        
        if query_lower in name or query_lower in url:
            subtitle_parts = []
            if button.get('headers'):
                subtitle_parts.append(f"{len(button['headers'])} headers")
            if button.get('cookies'):
                subtitle_parts.append(f"{len(button['cookies'])} cookies")
            if button.get('body'):
                subtitle_parts.append("POST body")
            mode = button.get('mode', 'browser')
            subtitle_parts.append(f"Mode: {mode}")
            
            subtitle = f"{button['url']} ({', '.join(subtitle_parts)})"
            
            # Get favicon for the button
            icon = fetch_favicon(button['url']) or ICON_WEB
            
            wf.add_item(
                title=button['name'],
                subtitle=subtitle,
                arg=f"open {button['name']}",
                valid=True,
                icon=icon
            )

def split_args_with_quotes(query):
    """Split query into args, preserving quoted strings as single arguments"""
    import shlex
    try:
        # Use shlex to properly handle quoted strings
        return shlex.split(query)
    except ValueError:
        # If quotes are unmatched, fall back to simple splitting
        return query.split()

def main(wf):
    query = wf.args[0] if len(wf.args) > 0 else None
    wf.logger.debug(f"Query: <{query}>")
    
    # Treat empty string or whitespace as no query
    if not query or query.strip() == '':
        show_buttons(wf, None)
        wf.send_feedback()
        return 0
    
    command, args = get_command_parts(query)
    
    if not command:
        show_buttons(wf, query)
    elif command == 'add':
        show_add_command(wf, args)
    elif command == 'adh':
        show_adh_command(wf, args)
    elif command == 'adc':
        show_adc_command(wf, args)
    elif command == 'adb':
        show_adb_command(wf, args)
    elif command == 'mode':
        show_mode_command(wf, args)
    elif command == 'remove':
        show_remove_command(wf, args)
    else:
        show_buttons(wf, query)
    
    wf.send_feedback()
    return 0

def show_help(wf):
    """Show help about available commands"""
    wf.add_item(
        title='Add Web Button',
        subtitle='wb add <url> [name]',
        valid=False,
        icon=ICON_INFO
    )
    wf.add_item(
        title='Add Header',
        subtitle='wb adh <button-name> <header-name> <header-value>',
        valid=False,
        icon=ICON_INFO
    )
    wf.add_item(
        title='Add Cookie',
        subtitle='wb adc <button-name> <cookie-name>=<cookie-value>',
        valid=False,
        icon=ICON_INFO
    )
    wf.add_item(
        title='Add POST Body',
        subtitle='wb adb <button-name> <body>',
        valid=False,
        icon=ICON_INFO
    )
    wf.add_item(
        title='Remove Button',
        subtitle='wb remove <name>',
        valid=False,
        icon=ICON_INFO
    )
    wf.add_item(
        title='Set Mode',
        subtitle='wb mode <button-name> <browser|quiet>',
        valid=False,
        icon=ICON_INFO
    )
    wf.add_item(
        title='Search and Open',
        subtitle='wb <query>',
        valid=False,
        icon=ICON_INFO
    )
    # Add update commands
    wf.add_item(
        title='Check for Updates',
        subtitle='wb workflow:update',
        valid=False,
        icon=ICON_INFO
    )
    wf.add_item(
        title='Toggle Auto Update',
        subtitle='wb workflow:autoupdate / workflow:noautoupdate',
        valid=False,
        icon=ICON_INFO
    )
    wf.add_item(
        title='Toggle Pre-releases',
        subtitle='wb workflow:prereleases / workflow:noprereleases',
        valid=False,
        icon=ICON_INFO
    )

if __name__ == '__main__':
    wf = Workflow(
        update_settings={
            'github_slug': 'schwark/alfred-webbutton',
            'frequency': 1  # Check for updates daily
        },
        help_url='https://github.com/schwark/alfred-webbutton'
    )
    sys.exit(wf.run(main)) 