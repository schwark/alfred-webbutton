#!/usr/bin/env python3
# encoding: utf-8

import sys
from workflow import Workflow, ICON_WEB, ICON_ERROR, ICON_INFO
from common import get_stored_data
from urllib.parse import urlparse

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
        wf.add_item(
            title="wb add <url> [name]",
            subtitle="Add a new web button",
            valid=False,
            icon=ICON_INFO
        )
    elif len(args) >= 1:
        url = args[0]
        name = args[1] if len(args) > 1 else None
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

def show_buttons(wf, query):
    """Show list of buttons matching query"""
    buttons = get_stored_data(wf, 'web_buttons') or []
    
    if query:
        buttons = wf.filter(query, buttons, lambda x: x['name'])
    
    # Show matching buttons
    found_items = False
    
    if len(buttons) == 1:
        # If exactly one button is found, show all options for that button
        button = buttons[0]
        found_items = True
        
        # Show button info and open option
        subtitle_parts = []
        if button.get('headers'):
            subtitle_parts.append(f"{len(button['headers'])} headers")
        if button.get('cookies'):
            subtitle_parts.append(f"{len(button['cookies'])} cookies")
        if button.get('body'):
            subtitle_parts.append("POST")
        
        mode = button.get('mode', 'browser')
        subtitle_parts.append(f"mode: {mode}")
        
        subtitle = f"URL: {button['url']}"
        if subtitle_parts:
            subtitle += f" ({', '.join(subtitle_parts)})"
            
        # Open button option
        wf.add_item(
            title=f"Open {button['name']}",
            subtitle=subtitle,
            arg=f"open {button['name']}",
            valid=True,
            icon=ICON_WEB
        )
        
        # Add header option
        wf.add_item(
            title=f"Add Header to {button['name']}",
            subtitle="↵ to add a header",
            autocomplete=f"adh {button['name']} ",
            valid=False,
            icon=ICON_INFO
        )
        
        # Add cookie option
        wf.add_item(
            title=f"Add Cookie to {button['name']}",
            subtitle="↵ to add a cookie",
            autocomplete=f"adc {button['name']} ",
            valid=False,
            icon=ICON_INFO
        )
        
        # Add body option
        wf.add_item(
            title=f"Add POST Body to {button['name']}",
            subtitle="↵ to add a POST body",
            autocomplete=f"adb {button['name']} ",
            valid=False,
            icon=ICON_INFO
        )
        
        # Set mode option
        wf.add_item(
            title=f"Set Mode for {button['name']}",
            subtitle=f"Current mode: {mode}",
            autocomplete=f"mode {button['name']} ",
            valid=False,
            icon=ICON_INFO
        )
        
        # Remove button option
        wf.add_item(
            title=f"Remove {button['name']}",
            subtitle="↵ to remove this button",
            arg=f"remove {button['name']}",
            valid=True,
            icon=ICON_ERROR
        )
        
    else:
        # Show regular list of matching buttons
        for button in buttons:
            found_items = True
            subtitle_parts = []
            if button.get('headers'):
                subtitle_parts.append(f"{len(button['headers'])} headers")
            if button.get('cookies'):
                subtitle_parts.append(f"{len(button['cookies'])} cookies")
            if button.get('body'):
                subtitle_parts.append("POST")
            
            mode = button.get('mode', 'browser')
            subtitle_parts.append(f"mode: {mode}")
            
            subtitle = f"URL: {button['url']}"
            if subtitle_parts:
                subtitle += f" ({', '.join(subtitle_parts)})"
                
            wf.add_item(
                title=button['name'],
                subtitle=subtitle,
                arg=f"open {button['name']}",
                valid=True,
                icon=ICON_WEB
            )
    
    # If no buttons found and query looks like a URL, suggest adding it or opening it directly
    if not found_items:
        if query and looks_like_url(query):
            # Option to open URL directly
            wf.add_item(
                title=f"Open URL: {query}",
                subtitle="↵ to open this URL directly in your browser",
                arg=f"open_url {query}",
                valid=True,
                icon=ICON_WEB
            )
            # Option to add as web button
            item = wf.add_item(
                title=f"Add as new web button: {query}",
                subtitle="⌘↵ to add this URL as a new web button",
                arg=f"add {query}",
                valid=True,
                icon=ICON_WEB
            )
            item.add_modifier('cmd', subtitle='Add this URL as a new web button')
        else:
            wf.add_item(
                title="No matching web buttons found",
                subtitle="Try 'wb add <url>' to create one",
                valid=False,
                icon=ICON_ERROR
            )
    
    # Add command suggestions if query matches command prefixes
    if query:
        command_matches = get_command_suggestions(query)
        if command_matches:
            # Add a separator if we have other results
            if found_items:
                wf.add_item(
                    title="──────────── Commands ────────────",
                    subtitle="Available commands matching your search",
                    valid=False,
                    icon=ICON_INFO
                )
            # Add matching commands
            for cmd, desc in command_matches:
                wf.add_item(
                    title=f"Command: {cmd}",
                    subtitle=desc,
                    autocomplete=f"{cmd} ",
                    valid=False,
                    icon=ICON_INFO
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
    
    if not query:
        show_help(wf)
        wf.send_feedback()
        return 0
    
    try:
        args = split_args_with_quotes(query)
    except:
        args = query.split()
    
    command = args[0].lower()
    
    # List of valid commands that should not trigger button search
    commands = ['add', 'adh', 'adc', 'adb', 'remove', 'mode']
    
    if command in commands:
        if command == 'add':
            show_add_command(wf, args[1:])
        elif command == 'adh':
            show_adh_command(wf, args[1:])
        elif command == 'adc':
            show_adc_command(wf, args[1:])
        elif command == 'adb':
            show_adb_command(wf, args[1:])
        elif command == 'remove':
            show_remove_command(wf, args[1:])
        elif command == 'mode':
            show_mode_command(wf, args)
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