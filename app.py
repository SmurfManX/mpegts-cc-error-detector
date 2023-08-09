from flask import Flask, render_template, request, redirect, url_for, flash, jsonify
import json
import os
import subprocess

app = Flask(__name__)
app.config.from_mapping(
    SECRET_KEY='some_secret_key',
    UPLOAD_FOLDER='logs',
    CONFIG_FILE='config.json',
)

ccdetect_process = {}

def load_channels():
    """Load channel configurations from a file."""
    if not os.path.exists(app.config['CONFIG_FILE']):
        return []
    with open(app.config['CONFIG_FILE'], 'r') as f:
        return json.load(f)

def save_channels(channels):
    """Save channel configurations to a file."""
    with open(app.config['CONFIG_FILE'], 'w') as f:
        json.dump(channels, f, indent=4)

@app.route('/')
def index():
    """Display the main dashboard."""
    channels = load_channels()
    return render_template('index.html', channels=channels)

@app.route('/add', methods=['POST'])
def add_channel():
    """Add a new channel configuration."""
    channels = load_channels()
    name = request.form.get('name')
    address = request.form.get('address')
    channels.append({'name': name, 'address': address})
    save_channels(channels)
    flash(f'Channel {name} added.')
    return redirect(url_for('index'))

@app.route('/delete/<int:index>', methods=['GET'])
def delete_channel(index):
    """Delete a specific channel configuration."""
    channels = load_channels()
    if 0 <= index < len(channels):
        deleted_channel = channels.pop(index)
        save_channels(channels)
        flash(f'Channel {deleted_channel["name"]} deleted.')
    else:
        flash('Invalid channel index.')
    return redirect(url_for('index'))

@app.route('/toggle/<int:index>', methods=['POST'])
def toggle_monitoring(index):
    """Toggle monitoring for a specific channel."""
    channels = load_channels()
    if index < len(channels):
        channel_name = channels[index]['name']
        channel_address = channels[index]['address']
        log_file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{channel_name}.log")
        
        # Start monitoring
        if not channels[index].get('running', False):
            with open(log_file_path, 'a', buffering=1) as log_file:
                ccdetect_process[channel_name] = subprocess.Popen(
                    ['python3', '-u', 'ccdetect', channel_address], 
                    stdout=log_file, 
                    stderr=subprocess.STDOUT
                )
                channels[index]['running'] = True
                flash(f'Monitoring started for channel: {channel_name}')
        # Stop monitoring
        else:
            if channel_name in ccdetect_process:
                ccdetect_process[channel_name].terminate()
                del ccdetect_process[channel_name]
            channels[index]['running'] = False
            flash(f'Monitoring stopped for channel: {channel_name}')
        save_channels(channels)
    else:
        flash('Invalid channel index.')
    return redirect(url_for('index'))

@app.route('/data/<string:channel_name>')
def get_data(channel_name):
    """Retrieve data for a specific channel."""
    log_file_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{channel_name}.log")
    packet_losses = []
    if os.path.exists(log_file_path):
        with open(log_file_path, 'r') as log_file:
            for line in log_file.readlines()[-100:]:
                try:
                    _, loss_percentage = line.split()
                    packet_losses.append(float(loss_percentage.rstrip('%')))
                except (ValueError, IndexError):
                    pass
    return jsonify(packet_losses)

if __name__ == '__main__':
    if not os.path.exists(app.config['UPLOAD_FOLDER']):
        os.makedirs(app.config['UPLOAD_FOLDER'])
    app.run(host='0.0.0.0', port=5000)