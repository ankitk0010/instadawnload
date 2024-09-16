from flask import Flask, request, jsonify
from flask_cors import CORS
import instaloader 
from instaloader import StoryItem
import os
import base64
import time
from moviepy.editor import VideoFileClip

app = Flask(__name__)
CORS(app)  # This will enable CORS for all routes

sessionid ='8534509620%3AIYDomkgLdVgUcj%3A11%3AAYeQG8Y3M8iGiirkKl5NcX8stVyF2NeA3KblXH0XXg'
L = instaloader.Instaloader()
L.context.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
L.context.max_connection_attempts = 1
L.context._session.cookies.update({
    'sessionid': sessionid,
    'csrftoken': 'B2JDDVO1HIft8GHxSh0IIVxiOWb86CcD',  # Replace with your actual csrftoken
    'ds_user_id': '8534509620'    # Replace with your actual user ID
})

 # Save the session for future use
@app.route('/download', methods=['POST'])
def download_media():
    try:
        # Get the Instagram post URL from the request
        data = request.get_json()
        post_url = data.get('url')
        
        if not post_url:
            return jsonify({"error": "No URL provided"}), 400

        url = post_url.split("/")
        urls = None
        check = None
        urldetail = post_url.split("/")[-3]
        check = post_url.split("/")[3]
        if check=='p' or check=='reel' or check=='tv':
           urls = post_url.split("/")[-2]
       
        print(urls)

        
        # Find the media file (image or video)
        media_files = []
        # Download the post using Instaloader
        if len(url)>1 and check!="stories": 
            post = instaloader.Post.from_shortcode(L.context, urls)
            L.download_post(post, target=urls)
            time.sleep(2)
            for filename in os.listdir(urls):
              file_path = os.path.join(urls, filename)
              if urldetail!='reel' and filename.endswith('.jpg') or filename.endswith('.png'):
                mimetype = "image/jpeg" if filename.endswith('.jpg') else "image/png"
              elif filename.endswith('.mp4'):
                mimetype = "video/mp4"
              else:
                continue  # Skip non-media files

              with open(file_path, "rb") as file:
                encoded_media = base64.b64encode(file.read()).decode('utf-8')
                media_files.append({
                    "filename": filename,
                    "media": encoded_media,
                    "mimetype": mimetype
                 })
                
           
          
        if not media_files:
            return jsonify({"error": "No media found"}), 404

        return jsonify(media_files)
    except Exception as e:
        app.logger.error(f"Exception occurred: {e}")
        # os.remove(os.path.join(os.path.dirname(__file__), 'instaloader_session'))
        return jsonify({"error": str(e)}), 500
    finally:
        # Clean up downloaded files
        if os.path.exists(urls):
            for file in os.listdir(urls):
                os.remove(os.path.join(urls, file))
            os.rmdir(urls)

@app.route('/download-audio', methods=['POST'])
def download_audio():
    try:
        # Get the Instagram reel URL from the request
        data = request.get_json()
        post_url = data.get('url')

        if not post_url:
            return jsonify({"error": "No URL provided"}), 400

        url = post_url.split("/")
        urls = post_url.split("/")[-2]
        check = post_url.split("/")[3]
        if check != 'reels' and check != 'reel':
            return jsonify({"error": "URL is not a reel"}), 400

        # Download the reel video using Instaloader
        post = instaloader.Post.from_shortcode(L.context, urls)
        L.download_post(post, target=urls)
        time.sleep(2)

        # Extract the audio from the video file
        audio_files = []
        for filename in os.listdir(urls):
            file_path = os.path.join(urls, filename)
            if filename.endswith('.mp4'):
                audio_filename = f"{urls}_audio.mp3"
                audio_path = os.path.join(urls, audio_filename)
                # Use moviepy to extract the audio
                video_clip = VideoFileClip(file_path)
                video_clip.audio.write_audiofile(audio_path)
                video_clip.close()

                # Read the audio file and encode it
                with open(audio_path, "rb") as audio_file:
                    encoded_audio = base64.b64encode(audio_file.read()).decode('utf-8')
                    audio_files.append({
                        "filename": audio_filename,
                        "media": encoded_audio,
                        "mimetype": "audio/mpeg"
                    })

                os.remove(audio_path)  # Clean up the audio file after encoding
            else:
                continue  # Skip non-media files

        if not audio_files:
            return jsonify({"error": "No audio found"}), 404

        return jsonify(audio_files)

    except Exception as e:
        app.logger.error(f"Exception occurred: {e}")
        return jsonify({"error": str(e)}), 500
    finally:
        # Clean up downloaded files
        if os.path.exists(urls):
            for file in os.listdir(urls):
                os.remove(os.path.join(urls, file))
            os.rmdir(urls)

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  # Use the port provided by Render, or default to 5000 locally
    app.run(host='0.0.0.0', port=port, debug=True)
