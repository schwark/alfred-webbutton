# Alfred Web Button Workflow v1.0.3

An Alfred workflow that allows you to create and activate custom web URLs with optional headers and cookies.

## Installation

1. Make sure you have [Alfred](https://www.alfredapp.com/) installed with the Powerpack license
2. Download the [latest release](https://github.com/schwark/alfred-webbutton/releases/latest) of this workflow
3. Double-click the `.alfredworkflow` file to install it

## Usage

The workflow provides the following commands:

### Viewing Web Buttons

Simply type `wb` followed by one or two spaces to see all your web buttons, sorted by most recently used. Sometimes you may need to type two spaces to see the full list. You can also:
- Search through your web buttons by typing part of their name
- Open URLs directly by typing them after `wb`
- See button details including headers, cookies, and mode
- Access button options by selecting a single button

Each button shows its website's favicon and is sorted by last use, with most recently used buttons appearing first.

### Adding a Web Button

```
wb add <url> [name]
```

If name is not provided, it will be automatically generated from the URL's domain. You can also add a URL directly from the search results if it looks like a valid URL.

To capture the current URL from Safari's active tab, use `:cap`:
```
wb add :cap [name]
```
The URL will be automatically captured from Safari's frontmost tab, and if no name is provided, it will be generated from the URL's domain. The current Safari URL is also shown as an autocomplete option when using the add command.

Example:
```
wb add https://github.com github
```
or simply:
```
wb add https://github.com
```
or capture from Safari:
```
wb add :cap
```

### Adding Headers to a Web Button

```
wb adh <button-name> "<header-name>" "<header-value>"
```

Example:
```
wb adh github "User-Agent" "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7)"
```

Note: Use quotes around header names and values, especially if they contain spaces or special characters.

### Adding Cookies to a Web Button

```
wb adc <button-name> "<cookie-name>=<cookie-value>"
```

Example:
```
wb adc github "session=abc123"
```

You can also add multiple cookies at once by separating them with semicolons:
```
wb adc github "session=abc123; user=john; theme=dark"
```

### Adding POST Body to a Web Button

```
wb adb <button-name> "<body>"
```

Example:
```
wb adb myapi '{"key": "value"}'
```

Note: Use quotes around the body, especially for JSON data.

### Setting Button Mode

```
wb mode <button-name> <browser|quiet>
```

Modes:
- `browser`: Opens the URL in your default browser (default)
- `quiet`: Makes the request without opening the browser, showing response in notification

Example:
```
wb mode github browser
wb mode webhook quiet
```

### Removing a Web Button

```
wb remove <button-name>
```

Example:
```
wb remove github
```

### Opening a Web Button

Simply type `wb` followed by the name of your web button:

```
wb github
```

You can also:
- Search through your web buttons by typing part of their name
- Open URLs directly by typing them after `wb`
- See button details including headers, cookies, and mode
- Access button options by selecting a single button

### Updating the Workflow

The workflow can automatically check for updates from GitHub. You can use these commands:

```
wb workflow:update          # Check for updates manually
wb workflow:autoupdate     # Enable automatic updates
wb workflow:noautoupdate   # Disable automatic updates
wb workflow:prereleases    # Include pre-release versions
wb workflow:noprereleases  # Exclude pre-release versions
```

## Features

- Create custom web buttons with specific URLs
- Capture URLs directly from Safari's active tab
- Smart sorting of buttons by last use
- Add custom headers for each web button
- Add cookies for each web button (single or multiple)
- Add POST bodies for API requests
- Set browser or quiet mode per button
- Automatic button name generation from URL
- Direct URL opening without saving
- Quick access through Alfred's interface
- Search through your web buttons
- Notification when a web button is activated
- Proper handling of spaces and special characters in values
- Automatic updates from GitHub

## Requirements

- Alfred Powerpack
- Python 3
- Alfred-Workflow Python package (automatically installed)
- Requests Python package (automatically installed)

## License

MIT License - see LICENSE file for details
