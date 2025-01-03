import m3u8
import concurrent.futures
import requests
import hashlib
import numpy as np
import tempfile
import os
import subprocess
import scipy.signal
from scipy.io import wavfile
import shutil
import argparse
import logging
import time
import threading

class StreamComparator:
    def __init__(self, url1, url2, duration=30, num_segments=5, window_size=0.5, verbose=0):
        self.url1 = url1
        self.url2 = url2
        self.duration = duration
        self.num_segments = num_segments
        self.window_size = window_size
        self.temp_dir = tempfile.mkdtemp()
        
        # Setup logging
        log_level = logging.WARNING
        if verbose == 1:
            log_level = logging.INFO
        elif verbose >= 2:
            log_level = logging.DEBUG
            
        logging.basicConfig(
            level=log_level,
            format='%(asctime)s - %(levelname)s - %(message)s'
        )
        self.logger = logging.getLogger(__name__)
        self.logger.debug(f"Initialized comparator with temp dir: {self.temp_dir}")

    def __del__(self):
        self.logger.debug(f"Cleaning up temp directory: {self.temp_dir}")
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def detect_stream_type(self, url):
        try:
            response = requests.head(url, timeout=5)
            content_type = response.headers.get('Content-Type', '').lower()
            
            if 'application/x-mpegurl' in content_type or 'm3u8' in content_type or url.endswith('.m3u8'):
                return 'hls'
            elif 'audio/mpeg' in content_type or 'audio/mp3' in content_type or 'icecast' in content_type:
                return 'mp3'
            else:
                try:
                    m3u8.load(url)
                    return 'hls'
                except:
                    return 'mp3'
        except:
            self.logger.warning(f"Could not detect stream type for {url}, assuming MP3")
            return 'mp3'

    def record_stream_synchronized(self, url, output_path, duration, start_event):
        """Record a stream with synchronized start"""
        cmd = [
            'ffmpeg',
            '-i', url,
            '-t', str(duration),
            '-ac', '1',  # Convert to mono
            '-ar', '44100',  # Sample rate
            '-y',  # Overwrite output
            output_path
        ]
        
        # Wait for the start signal
        start_event.wait()
        
        try:
            subprocess.run(cmd, capture_output=True, check=True)
            return True
        except subprocess.CalledProcessError as e:
            self.logger.error(f"Failed to record stream: {e}")
            return False

    def find_best_alignment(self, audio1, audio2, max_offset=44100):
        """Find the best alignment between two audio streams"""
        best_correlation = 0
        best_offset = 0
        
        for offset in range(0, max_offset, 1000):  # Step by 1000 samples for speed
            # Try positive offset
            if offset + len(audio2) <= len(audio1):
                correlation = np.corrcoef(audio1[offset:offset + len(audio2)], audio2)[0, 1]
                if correlation > best_correlation:
                    best_correlation = correlation
                    best_offset = offset
            
            # Try negative offset
            if offset + len(audio1) <= len(audio2):
                correlation = np.corrcoef(audio1, audio2[offset:offset + len(audio1)])[0, 1]
                if correlation > best_correlation:
                    best_correlation = correlation
                    best_offset = -offset
        
        return best_offset, best_correlation

    def compare_audio_data(self, audio1, audio2):
        """Compare two audio arrays with alignment"""
        if audio1 is None or audio2 is None:
            self.logger.warning("One or both audio segments are None")
            return 0.0
        
        # Normalize audio data
        audio1 = audio1.astype(float) / np.max(np.abs(audio1))
        audio2 = audio2.astype(float) / np.max(np.abs(audio2))
        
        # Find best alignment
        offset, correlation = self.find_best_alignment(audio1, audio2)
        self.logger.info(f"Best alignment found at offset: {offset} samples ({offset/44100:.3f} seconds)")
        
        # Align and trim the signals
        if offset > 0:
            audio1 = audio1[offset:]
            audio2 = audio2[:len(audio1)]
        elif offset < 0:
            audio2 = audio2[-offset:]
            audio1 = audio1[:len(audio2)]
        
        # Calculate final similarity
        similarity = correlation
        self.logger.debug(f"Audio similarity score after alignment: {similarity:.4f}")
        return max(0.0, min(1.0, similarity))

    def compare_streams(self):
        """Main comparison method"""
        self.logger.info("Starting stream comparison")
        
        # Detect stream types
        type1 = self.detect_stream_type(self.url1)
        type2 = self.detect_stream_type(self.url2)
        
        self.logger.info(f"Stream 1 type: {type1}")
        self.logger.info(f"Stream 2 type: {type2}")
        
        if type1 == 'mp3' or type2 == 'mp3':
            duration = self.duration or 30
            
            wav1_path = os.path.join(self.temp_dir, 'stream1.wav')
            wav2_path = os.path.join(self.temp_dir, 'stream2.wav')
            
            # Create synchronization event
            start_event = threading.Event()
            
            # Create recording threads
            thread1 = threading.Thread(
                target=self.record_stream_synchronized,
                args=(self.url1, wav1_path, duration, start_event)
            )
            thread2 = threading.Thread(
                target=self.record_stream_synchronized,
                args=(self.url2, wav2_path, duration, start_event)
            )
            
            # Start both threads
            thread1.start()
            thread2.start()
            
            # Signal both threads to start recording simultaneously
            self.logger.info("Starting synchronized recording")
            start_event.set()
            
            # Wait for both recordings to complete
            thread1.join()
            thread2.join()
            
            # Read recorded audio
            try:
                _, audio1 = wavfile.read(wav1_path)
                _, audio2 = wavfile.read(wav2_path)
                return self.compare_audio_data(audio1, audio2)
            except Exception as e:
                self.logger.error(f"Failed to read audio files: {e}")
                return 0.0
            
        else:
            # HLS comparison logic (unchanged)
            ...

def main():
    parser = argparse.ArgumentParser(description='Compare two audio streams (HLS or MP3/Icecast)')
    parser.add_argument('url1', help='First stream URL')
    parser.add_argument('url2', help='Second stream URL')
    parser.add_argument('-d', '--duration', type=float, default=30, help='Duration to compare in seconds (default: 30)')
    parser.add_argument('-s', '--segments', type=int, default=5, help='Number of segments to compare for HLS (default: 5)')
    parser.add_argument('-v', '--verbose', action='count', default=0, help='Increase verbosity')
    parser.add_argument('--max-offset', type=float, default=1.0, 
                       help='Maximum time offset to check for alignment in seconds (default: 1.0)')
    
    args = parser.parse_args()

    comparator = StreamComparator(
        args.url1,
        args.url2,
        duration=args.duration,
        num_segments=args.segments,
        verbose=args.verbose
    )
    
    similarity = comparator.compare_streams()
    print(f"\nFinal Stream Similarity Score: {similarity:.2%}")

if __name__ == "__main__":
    main()
