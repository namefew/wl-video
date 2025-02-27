import json
from video_ui import VideoUI

def load_config(config_path):
    with open(config_path, 'r', encoding='utf-8') as file:
        config = json.load(file)
    return config['tables']

def main():
    config_path = 'config.json'
    tables = load_config(config_path)
    app = VideoUI(tables=tables)
    app.run()

if __name__ == "__main__":
    main()