

from flask import Flask,render_template ,send_from_directory,jsonify,request
from pymongo import MongoClient
import subprocess
import os
from flask_cors import CORS
import threading
app = Flask(__name__)
CORS(app)
# Directory to store HLS files
HLS_DIRECTORY = 'hls_output'

client = MongoClient('mongodb://localhost:27017/')
db = client['VideoStreaming']
collection = db['overlay_options']
# @app.route('/')
# def index():
#     return render_template('index.html')

@app.route('/overlay_settings', methods=['GET'])
def get_overlay_settings():
    # collection.insert_one({"content" :"rittik" , "align" : "center" , "color" : "red"})
    overlay_settings = list(collection.find())
    for overlay in overlay_settings:
        overlay['_id'] = str(overlay['_id'])

    return jsonify({"data" : overlay_settings})


@app.route('/create', methods=['POST'])
def create_overlay_setting():
    data = request.json  # Assume the request body contains JSON data
    print(data)
    # Insert the new entry into the collection
    result = collection.insert_one(data)
    # result.inserted_id = str(result.inserted_id)
    # Return the inserted document ID
    return jsonify({"data" : "done"})


@app.route('/delete', methods=['POST'])
def delete_overlay():
    # Get content from request body
    content = request.json.get('content')
    query = {'content': content}

    # Find existing overlay
    existing_overlay = collection.find_one(query)
    print(existing_overlay)
    # Check if overlay exists
    if existing_overlay:
        # Delete document based on content
        result = collection.delete_one({'_id': existing_overlay['_id']})

        # Check if deletion was successful
        if result.deleted_count:
            return jsonify({'message': 'Overlay deleted successfully'}), 200
        else:
            return jsonify({'error': 'Failed to delete overlay'}), 500
    else:
        return jsonify({'error': 'Overlay not found'}), 404

@app.route('/edit/<content>', methods=['PUT'])
def edit_overlay(content):
    # Get the new values from the request JSON
    new_content = request.json.get('new_content', {})
    
    # Find the document with the specified content
    query = {'content': content}
    existing_overlay = collection.find_one(query)

    if existing_overlay:
        # Update the document with new values
        update_values = {
            '$set': {
                'content': new_content.get('content', existing_overlay['content']),
                'color': new_content.get('color', existing_overlay['color']),
                'align': new_content.get('align', existing_overlay['align'])
            }
        }

        collection.update_one(query, update_values)
        return jsonify({'message': 'Overlay updated successfully'})
    else:
        return jsonify({'error': 'Overlay not found'}), 404


@app.route('/hls/<path:filename>')
def hls(filename):
    return send_from_directory(HLS_DIRECTORY, filename)

def video_stream():
    # Ensure HLS output directory exists
    os.makedirs(HLS_DIRECTORY, exist_ok=True)

    # ffmpeg command to convert RTSP stream to HLS format
    #rtsp://b03773d78e34.entrypoint.cloud.wowza.com:1935/app-4065XT4Z/80c76e59_stream1
    #rtsp://rtspstream:861947b6ef0945e05e0c38b83cef4365@zephyr.rtsp.stream/pattern
    ffmpeg_command = [
        'ffmpeg', '-i', 'rtsp://rtspstream:bff3e735c5257f7904e8b94f3ecc79e9@zephyr.rtsp.stream/movie',
        '-c:v', 'copy', '-c:a', 'aac', '-hls_time', '10', '-hls_list_size', '6', '-f', 'hls',
        os.path.join(HLS_DIRECTORY, 'stream.m3u8')
    ]
    subprocess.Popen(ffmpeg_command)

    # Serve HLS files from the HLS_DIRECTORY
    # return send_from_directory(HLS_DIRECTORY, 'stream.m3u8')

thread = threading.Thread(target=video_stream)
thread.start()


if __name__ == '__main__':
    app.run(debug=True)
