import os
import sys
import subprocess
import openai
import re


# Your transcribe.py code
openai.api_key = os.getenv("OPENAI_API_KEY")

# Read an SRT file and return its content as a string
def read_srt(fname):
     with open(fname) as infile:
         return infile.read().strip()


def transcribe_audio_segment(segment_path, prompt):
     audio_file = open(segment_path, "rb")
     transcript = openai.Audio.transcribe(
         file=audio_file,
         model="whisper-1",
         response_format="srt",
         prompt=prompt,
     )
     return transcript

def segment_audio_file(video_id, segment_duration='0:01:00'):
     audio_file_path = os.path.join(os.getcwd(), "tmp", f"{video_id}.m4a")
     output_dir = os.path.join(os.getcwd(), "tmp", "segments")

     if not os.path.exists(output_dir):
         os.makedirs(output_dir)

     subprocess.run(
         [
             "ffmpeg",
             "-hide_banner",
             "-i",
             audio_file_path,
             "-c",
             "copy",
             "-map",
             "0",
             "-segment_time",
             segment_duration,
             "-f",
             "segment",
             os.path.join(output_dir, "segment_%03d.m4a"),
         ]
     )

     segment_files = [
         os.path.join(output_dir, f)
         for f in os.listdir(output_dir)
         if f.startswith("segment_") and f.endswith(".m4a")
     ]

     return sorted(segment_files)



# Merge multiple SRT files adjusting timecodes and index numbers
def merge_srt(filenames):
     merged_content = []
     counter = 1
     time_offset = 0

     for fname in filenames:
         content = read_srt(fname)
         segments = content.split('\n\n')
         for segment in segments:
             lines = segment.split('\n')
             idx = counter
             start_time, end_time = re.findall(r'(\d\d:\d\d:\d\d,\d\d\d)', lines[1])
             start_time = adjust_time(start_time, time_offset)
             end_time = adjust_time(end_time, time_offset)
             text = '\n'.join(lines[2:])
             merged_content.append(f"{idx}\n{start_time} --> {end_time}\n{text}")
             counter += 1
         last_end_time = re.findall(r'(\d\d:\d\d:\d\d,\d\d\d)', lines[1])[-1]
         time_offset = time_to_milliseconds(last_end_time)

     return "\n\n".join(merged_content)

# Adjust the time string with the given offset in milliseconds
def adjust_time(time_str, offset):
     time_parts = list(map(int, re.split(r'[:,]', time_str)))
     total_ms = (time_parts[0] * 3600000 + time_parts[1] * 60000 + time_parts[2] * 1000 + time_parts[3]) + offset
     hours, remainder = divmod(total_ms, 3600000)
     minutes, remainder = divmod(remainder, 60000)
     seconds, milliseconds = divmod(remainder, 1000)
     return f"{hours:02d}:{minutes:02d}:{seconds:02d},{milliseconds:03d}"

# Convert a time string to milliseconds
def time_to_milliseconds(time_str):
     time_parts = list(map(int, re.split(r'[:,]', time_str)))
     return time_parts[0] * 3600000 + time_parts[1] * 60000 + time_parts[2] * 1000 + time_parts[3]



def process(video_id):
     prompt = (
         "I am a programmer. My name is Takuya. "
         "This is a vlog about my app development, tech review, lifehacks, etc. "
         "I have my own product called Inkdrop."
         "My YouTube channel is called devaslife. "
     )

     # Step 1: Segment the audio file
     audio_segments = segment_audio_file(video_id)

     # Step 2: Transcribe each segment and save the SRT files
     srt_files = []
     for i, segment in enumerate(audio_segments):
         srt_filename = f"tmp/segment_{i:03d}.srt"
         srt_files.append(srt_filename)
         transcript = transcribe_audio_segment(segment, prompt)
         with open(srt_filename, "w") as f:
             f.write(transcript)

     # Step 3: Merge the SRT files
     merged_content = merge_srt(srt_files)

     with open(f"tmp/{video_id}_transcript.srt", "w") as outfile:
         outfile.write(merged_content)


     # Cleanup: Remove the temporary SRT files
     for srt_file in srt_files:
         os.remove(srt_file)

     return merged_content


if __name__ == "__main__":
     video_id = sys.argv[1]
     content =process(video_id)
     print(content)
