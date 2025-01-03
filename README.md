# Stream Comparison Tool

Compares audio content of streaming media to determine if they're the same source. Supports HLS and Icecast/MP3 streams.

## Features

- Stream type auto-detection (HLS/Icecast/MP3)  
- Synchronized recording of live streams
- Smart audio alignment detection
- Configurable comparison duration 
- Detailed similarity scoring
- Verbose debugging output

## Installation

# Install required packages
pip install -r requirements.txt

# Required system dependencies
apt-get install ffmpeg

## Usage Examples 

Compare two Icecast streams:
./compare_streams.py https://stream1.example.com https://stream2.example.com

Compare with 60 second sample:
./compare_streams.py https://stream1.example.com https://stream2.example.com -d 60

Enable verbose output:
./compare_streams.py https://stream1.example.com https://stream2.example.com -v

## Options

-d, --duration    Duration in seconds to compare (default: 30)
-s, --segments    Number of segments for HLS comparison (default: 5) 
-v, --verbose     Increase output verbosity
--max-offset      Maximum time offset for alignment in seconds (default: 1.0)

## Requirements

- Python 3.7+
- ffmpeg 
- Required Python packages (see requirements.txt)

## How it Works

1. Auto-detects stream type (HLS/Icecast/MP3)
2. Records synchronized samples from both streams
3. Normalizes audio data
4. Finds optimal time alignment between samples
5. Calculates similarity score based on correlation
6. Reports match percentage

Similarity scores:
- 90%+ : Almost certainly same source
- 70-90%: Very likely same source
- 50-70%: Some similarities, possibly same source
- <50%: Different sources

## License

MIT License - see LICENSE file

## Contributing

Pull requests welcome! Please see CONTRIBUTING.md
