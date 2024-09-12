from flask import Flask, request, jsonify
from flask_cors import CORS
import instaloader 
from instaloader import StoryItem
import os
import base64
import time

app = Flask(__name__)
CORS(app)  # This will enable CORS for all routes

sessionid ='8534509620%3ApeugccYhQFl9ml%3A17%3AAYf3iBwTVa1UvvPwxy-EDnKB0aBQJUnI_wqM01WqVw'
L = instaloader.Instaloader()

# # Define your Instagram credentials
username =  os.environ.get('username')
password =  os.environ.get('password')
L.context.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
L.context.max_connection_attempts = 1
L.context._session.cookies.update({
    'sessionid': sessionid,
    'csrftoken': 'qym9N3yK0JaprEtYVG78l8JAJCj2nWyU',  # Replace with your actual csrftoken
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
        if len(url)>1:
         urldetail = post_url.split("/")[-3]
         check = post_url.split("/")[3]
         if check=='p' or check=='reel' or check=='tv':
           urls = post_url.split("/")[-2]
         elif len(url)>6:
            urls = post_url.split("/")[5]
         else:
            urls = post_url.split("/")[4]  
        else: 
            urls = url[0]  
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
        else:
           try:
            #  L.close()
             L.load_session
             L.load_session_from_file(username,session_file_path)
           except FileNotFoundError:
             print("Session file not found. Please log in first.")
             L.login(username, password)
             L.save_session_to_file(session_file_path) 
           
           if urls.isnumeric():
            #   print('hi')
              media_id = int(urls)
              story_item = StoryItem.from_mediaid(L.context,media_id )
              L.download_storyitem(story_item, target=story_item.mediaid)
              time.sleep(2)
           else: 
             profile = instaloader.Profile.from_username(L.context, urls)
             for story in L.get_stories(userids=[profile.userid]):
                for story_item in story.get_items():
                  L.download_storyitem(story_item, target=profile.username)
                  time.sleep(2)  # Longer delay to avoid rate limit
                        
           has_video = any(filename.endswith('.mp4') for filename in os.listdir(urls))

           for filename in os.listdir(urls):
               file_paths = os.path.join(urls, filename)
               if filename.endswith('.mp4'):
                  mimetype = "video/mp4"
               elif not has_video and filename.endswith('.jpg') or filename.endswith('.png'):
                  mimetype = "image/jpeg" if filename.endswith('.jpg') else "image/png"  
               else:
                  continue  # Skip non-media files

               with open(file_paths, "rb") as file:
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
