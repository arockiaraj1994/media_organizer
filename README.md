# Media Organizer

Media Organizer is a desktop application that helps you organize your photos and videos into folders by date. It features a user-friendly graphical interface and supports organizing files by year, month, or day. The app can also help you find duplicate media files.

## Features

- Organize photos and videos by date (year, month, day)
- Choose custom source and destination folders
- Dry run mode to preview changes without moving files
- Find duplicate files
- Simple and intuitive GUI

## Installation

1. Clone this repository:

   ```sh
   git clone <repo-url>
   cd media_organizer
   ```

2. Install the required dependencies:

   ```sh
   pip install -r requirements.txt
   ```

## Usage

1. Run the application:

   ```sh
   python src/main.py
   ```

2. Use the GUI to select the source and destination folders, choose the folder structure, and start organizing your media files.
3. Use the duplicate finder to locate duplicate files in your collection.

## Requirements

- Python 3.7+
- PySide6
- Pillow
- scipy

## License

This project is licensed under the MIT License.
