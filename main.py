from flask import Flask, request, jsonify
from flask_cors import CORS
import instaloader 
from instaloader import StoryItem
import os
import base64
import time
app = Flask(__name__)
CORS(app)  # This will enable CORS for all routes

# sessionid ='8534509620%3AMcoENP0db3GVh5%3A6%3AAYeIrJjCraSOiDJNlhqDtRH5F3ol9YlkRkaPeewutw'
L = instaloader.Instaloader()

# # Define your Instagram credentials
username = 'softypatel97@gmail.com' | os.environ.get('token')
password = 'Vinaykr@45' | os.environ.get('token')
L.context.user_agent = "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36"
L.context.max_connection_attempts = 1
# L.context._session.cookies.update({
#     'sessionid': sessionid,
#     'csrftoken': 'h0g4ZNuaLtZtpgsc3FYVA2Te1wHTl3Y8',  # Replace with your actual csrftoken
#     'ds_user_id': '8534509620'    # Replace with your actual user ID
# })

 # Save the session for future use

@app.route('/download', methods=['POST'])
def download_media():
    try:
        # Get the Instagram post URL from the request
        data = request.get_json()
        post_url = data.get('url')
        
        if not post_url:
            return jsonify({"error": "No URL provided"}), 400

        # Extract the shortcode from the URL
        shortcode = post_url.split("/")[-2]
        urldetail = post_url.split("/")[-3]
        check = post_url.split("/")[3]
        url = post_url.split("/")
        urls = None
        if len(url)>6:
            urls = post_url.split("/")[5]
        else:
            urls = post_url.split("/")[4]    
        print(urls)

        
        # Find the media file (image or video)
        media_files = []
        # Download the post using Instaloader
        if check!="stories": 
            post = instaloader.Post.from_shortcode(L.context, shortcode)
            L.download_post(post, target=shortcode)
            time.sleep(2)
            for filename in os.listdir(shortcode):
              file_path = os.path.join(shortcode, filename)
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
             L.load_session
             L.load_session_from_file(username)
           except FileNotFoundError:
             print("Session file not found. Please log in first.")
             L.login(username, password)
             L.save_session_to_file() 
           
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
                  L.download_storyitem(story_item, target=urls)
                  time.sleep(2)
                  print(f"Downloaded story item {story_item.date_utc}")
                 
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
        if os.path.exists(shortcode or urls):
            for file in os.listdir(shortcode or urls):
                os.remove(os.path.join(shortcode or urls, file))
            os.rmdir(shortcode or urls)

if __name__ == '__main__':
    app.run(debug=True)
