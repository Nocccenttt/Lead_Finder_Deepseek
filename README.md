# LeadFinder

## Website imagery

Landing pages now ask the AI for two niche-specific image search queries and use relevant stock photography in the generated hero and feature sections. The current no-key fallback uses LoremFlickr/Flickr-style stock imagery. For production use, verify the image licensing/attribution requirements for the chosen source.

## DeepSeek API

The generator reads `DEEPSEEK_API_KEY` from the local `.env`. The API key is intentionally NOT included in this distribution ZIP. On first run, `START_LEADFINDER.bat` asks for the key and stores it locally.
