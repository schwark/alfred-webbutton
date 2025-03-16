# Alfred Web Button Workflow

An Alfred workflow that allows you to create and activate custom web URLs with optional headers and cookies.

## Installation

1. Make sure you have [Alfred](https://www.alfredapp.com/) installed with the Powerpack license
2. Download the latest release of this workflow
3. Double-click the `.alfredworkflow` file to install it

## Usage

The workflow provides the following commands:

### Adding a Web Button

```
wb add <url> [name]
```

If name is not provided, it will be automatically generated from the URL's domain.

Example:
```
wb add https://github.com github
```
or simply:
```
wb add https://github.com
```

### Adding Headers to a Web Button

```
wb adh <button-name> <header-name> <header-value>
```

Example:
```
wb adh github User-Agent "Mozilla/5.0"
```

### Adding Cookies to a Web Button

```
wb adc <button-name> <cookie-name>=<cookie-value>
```

Example:
```
wb adc github session=abc123
```

### Removing a Web Button

```
wb remove <name>
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

You can also search through your web buttons by typing part of their name after `wb`.

## Features

- Create custom web buttons with specific URLs
- Add custom headers for each web button
- Add cookies for each web button
- Automatic button name generation from URL
- Quick access through Alfred's interface
- Search through your web buttons
- Notification when a web button is activated

## Requirements

- Alfred Powerpack
- Python 3
- Alfred-Workflow Python package (automatically installed)
- Requests Python package (automatically installed)

## License

MIT License - see LICENSE file for details
