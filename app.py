import os
import secrets
from datetime import datetime, date
from flask import Flask, render_template_string, request, redirect, url_for, flash, send_from_directory, abort
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from markupsafe import escape

app = Flask(__name__, static_folder='.', static_url_path='/static')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or secrets.token_hex(32)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///dvora.db'
app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024  # 50 MB for audio/MP4 uploads
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

IMAGE_EXTS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
AUDIO_EXTS = {'mp3', 'wav', 'mp4'}
ALLOWED = IMAGE_EXTS | AUDIO_EXTS

# --- 150+ BADGES DICTIONARY ---
BADGES_LIST = [
    {'name': 'Developer', 'icon': 'fa-code'}, {'name': 'Staff', 'icon': 'fa-shield-halved'},
    {'name': 'Content Creator', 'icon': 'fa-video'}, {'name': 'Verified', 'icon': 'fa-circle-check'},
    {'name': 'Premium', 'icon': 'fa-gem'}, {'name': 'OG', 'icon': 'fa-crown'},
    {'name': 'Donor', 'icon': 'fa-heart'}, {'name': 'Bug Hunter', 'icon': 'fa-bug'},
    {'name': 'Gamer', 'icon': 'fa-gamepad'}, {'name': 'Artist', 'icon': 'fa-palette'},
    {'name': 'Music', 'icon': 'fa-music'}, {'name': 'VIP', 'icon': 'fa-star'},
    {'name': 'Early Supporter', 'icon': 'fa-clock'}, {'name': 'Booster', 'icon': 'fa-rocket'},
    {'name': 'Hacker', 'icon': 'fa-terminal'}, {'name': 'Moderator', 'icon': 'fa-gavel'},
    {'name': 'Admin', 'icon': 'fa-user-shield'}, {'name': 'Owner', 'icon': 'fa-crown'},
    {'name': 'Partner', 'icon': 'fa-handshake'}, {'name': 'Legend', 'icon': 'fa-dragon'},
    {'name': 'Pro', 'icon': 'fa-trophy'}, {'name': 'Elite', 'icon': 'fa-medal'},
    {'name': 'God', 'icon': 'fa-bolt'}, {'name': 'King', 'icon': 'fa-chess-king'},
    {'name': 'Queen', 'icon': 'fa-chess-queen'}, {'name': 'Ninja', 'icon': 'fa-user-ninja'},
    {'name': 'Pirate', 'icon': 'fa-skull'}, {'name': 'Wizard', 'icon': 'fa-hat-wizard'},
    {'name': 'Knight', 'icon': 'fa-chess-knight'}, {'name': 'Sniper', 'icon': 'fa-crosshairs'},
    {'name': 'Ghost', 'icon': 'fa-ghost'}, {'name': 'Alien', 'icon': 'fa-user-astronaut'},
    {'name': 'Robot', 'icon': 'fa-robot'}, {'name': 'Cyborg', 'icon': 'fa-microchip'},
    {'name': 'Angel', 'icon': 'fa-halo'}, {'name': 'Demon', 'icon': 'fa-fire'},
    {'name': 'Vampire', 'icon': 'fa-bat'}, {'name': 'Werewolf', 'icon': 'fa-paw'},
    {'name': 'Zombie', 'icon': 'fa-biohazard'}, {'name': 'Dragon', 'icon': 'fa-dragon'},
    {'name': 'Unicorn', 'icon': 'fa-unicorn'}, {'name': 'Phoenix', 'icon': 'fa-fire-flame-curved'},
    {'name': 'Griffin', 'icon': 'fa-feather'}, {'name': 'Mermaid', 'icon': 'fa-fish'},
    {'name': 'Centaur', 'icon': 'fa-horse'}, {'name': 'Titan', 'icon': 'fa-mountain'},
    {'name': 'Giant', 'icon': 'fa-person'}, {'name': 'Dwarf', 'icon': 'fa-person-hiking'},
    {'name': 'Elf', 'icon': 'fa-leaf'}, {'name': 'Orc', 'icon': 'fa-axe'},
    {'name': 'Goblin', 'icon': 'fa-coins'}, {'name': 'Troll', 'icon': 'fa-bridge'},
    {'name': 'Ogre', 'icon': 'fa-tree'}, {'name': 'Fairy', 'icon': 'fa-sparkles'},
    {'name': 'Pixie', 'icon': 'fa-wand-magic-sparkles'}, {'name': 'Sprite', 'icon': 'fa-wind'},
    {'name': 'Nymph', 'icon': 'fa-water'}, {'name': 'Siren', 'icon': 'fa-microphone'},
    {'name': 'Harpy', 'icon': 'fa-dove'}, {'name': 'Minotaur', 'icon': 'fa-bullhorn'},
    {'name': 'Cyclops', 'icon': 'fa-eye'}, {'name': 'Medusa', 'icon': 'fa-snake'},
    {'name': 'Kraken', 'icon': 'fa-octopus'}, {'name': 'Leviathan', 'icon': 'fa-water'},
    {'name': 'Behemoth', 'icon': 'fa-elephant'}, {'name': 'Ziz', 'icon': 'fa-feather-pointed'},
    {'name': 'Chimera', 'icon': 'fa-paw'}, {'name': 'Hydra', 'icon': 'fa-dragon'},
    {'name': 'Cerberus', 'icon': 'fa-dog'}, {'name': 'Pegasus', 'icon': 'fa-horse-head'},
    {'name': 'Sleipnir', 'icon': 'fa-horse'}, {'name': 'Fenrir', 'icon': 'fa-wolf'},
    {'name': 'Jormungandr', 'icon': 'fa-snake'}, {'name': 'Hel', 'icon': 'fa-skull-crossbones'},
    {'name': 'Loki', 'icon': 'fa-mask'}, {'name': 'Thor', 'icon': 'fa-hammer'},
    {'name': 'Odin', 'icon': 'fa-eye'}, {'name': 'Zeus', 'icon': 'fa-bolt'},
    {'name': 'Poseidon', 'icon': 'fa-trident'}, {'name': 'Hades', 'icon': 'fa-fire'},
    {'name': 'Athena', 'icon': 'fa-owl'}, {'name': 'Apollo', 'icon': 'fa-sun'},
    {'name': 'Artemis', 'icon': 'fa-moon'}, {'name': 'Ares', 'icon': 'fa-swords'},
    {'name': 'Aphrodite', 'icon': 'fa-heart'}, {'name': 'Hermes', 'icon': 'fa-shoe-prints'},
    {'name': 'Dionysus', 'icon': 'fa-wine-glass'}, {'name': 'Demeter', 'icon': 'fa-wheat-awn'},
    {'name': 'Hephaestus', 'icon': 'fa-anvil'}, {'name': 'Hera', 'icon': 'fa-peacock'},
    {'name': 'Persephone', 'icon': 'fa-seedling'}, {'name': 'Ra', 'icon': 'fa-sun'},
    {'name': 'Anubis', 'icon': 'fa-dog'}, {'name': 'Osiris', 'icon': 'fa-crown'},
    {'name': 'Isis', 'icon': 'fa-feather'}, {'name': 'Horus', 'icon': 'fa-eye'},
    {'name': 'Set', 'icon': 'fa-desert'}, {'name': 'Sobek', 'icon': 'fa-crocodile'},
    {'name': 'Bastet', 'icon': 'fa-cat'}, {'name': 'Thoth', 'icon': 'fa-book'},
    {'name': 'Sekhmet', 'icon': 'fa-lion'}, {'name': 'Ptah', 'icon': 'fa-hammer'},
    {'name': 'Amun', 'icon': 'fa-wind'}, {'name': 'Shiva', 'icon': 'fa-om'},
    {'name': 'Vishnu', 'icon': 'fa-eye'}, {'name': 'Brahma', 'icon': 'fa-lotus'},
    {'name': 'Indra', 'icon': 'fa-bolt'}, {'name': 'Agni', 'icon': 'fa-fire'},
    {'name': 'Vayu', 'icon': 'fa-wind'}, {'name': 'Varuna', 'icon': 'fa-water'},
    {'name': 'Yama', 'icon': 'fa-skull'}, {'name': 'Kali', 'icon': 'fa-sword'},
    {'name': 'Durga', 'icon': 'fa-shield'}, {'name': 'Ganesha', 'icon': 'fa-elephant'},
    {'name': 'Hanuman', 'icon': 'fa-monkey'}, {'name': 'Lakshmi', 'icon': 'fa-coins'},
    {'name': 'Saraswati', 'icon': 'fa-music'}, {'name': 'Amaterasu', 'icon': 'fa-sun'},
    {'name': 'Susanoo', 'icon': 'fa-storm'}, {'name': 'Tsukuyomi', 'icon': 'fa-moon'},
    {'name': 'Izanagi', 'icon': 'fa-male'}, {'name': 'Izanami', 'icon': 'fa-female'},
    {'name': 'Raijin', 'icon': 'fa-drum'}, {'name': 'Fujin', 'icon': 'fa-wind'},
    {'name': 'Inari', 'icon': 'fa-fox'}, {'name': 'Benzaiten', 'icon': 'fa-music'},
    {'name': 'Bishamonten', 'icon': 'fa-shield'}, {'name': 'Daikokuten', 'icon': 'fa-hammer'},
    {'name': 'Ebisu', 'icon': 'fa-fish'}, {'name': 'Fukurokuju', 'icon': 'fa-cane'},
    {'name': 'Hotei', 'icon': 'fa-bag'}, {'name': 'Jurojin', 'icon': 'fa-book'},
    {'name': 'Sun Wukong', 'icon': 'fa-monkey'}, {'name': 'Zhu Bajie', 'icon': 'fa-piggy-bank'},
    {'name': 'Sha Wujing', 'icon': 'fa-water'}, {'name': 'Erlang Shen', 'icon': 'fa-eye'},
    {'name': 'Nezha', 'icon': 'fa-fire'}, {'name': 'Ao Guang', 'icon': 'fa-dragon'},
    {'name': 'Yu Huang', 'icon': 'fa-crown'}, {'name': 'Xi Wangmu', 'icon': 'fa-peach'},
    {'name': "Chang'e", 'icon': 'fa-moon'}, {'name': 'Hou Yi', 'icon': 'fa-bow-arrow'},
    {'name': 'Jade Emperor', 'icon': 'fa-gem'}, {'name': 'Cthulhu', 'icon': 'fa-octopus'},
    {'name': 'Dagon', 'icon': 'fa-fish'}, {'name': 'Yog-Sothoth', 'icon': 'fa-key'},
    {'name': 'Nyarlathotep', 'icon': 'fa-mask'}, {'name': 'Azathoth', 'icon': 'fa-sun'},
    {'name': 'Shub-Niggurath', 'icon': 'fa-tree'}, {'name': 'Hastur', 'icon': 'fa-wind'},
    {'name': 'Tsathoggua', 'icon': 'fa-toad'}, {'name': 'Yig', 'icon': 'fa-snake'},
    {'name': 'Atlach-Nacha', 'icon': 'fa-spider'}
]

# --- DATABASE MODELS ---
class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    created = db.Column(db.DateTime, default=datetime.utcnow)
    profile = db.relationship('Profile', backref='user', uselist=False, cascade='all, delete-orphan')
    links = db.relationship('Link', backref='user', cascade='all, delete-orphan', order_by='Link.position')
    badges = db.relationship('Badge', backref='user', cascade='all, delete-orphan')

    @property
    def is_admin(self):
        return self.username == 'dvora'


class Profile(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), unique=True, nullable=False)
    display_name = db.Column(db.String(64), default='')
    bio = db.Column(db.Text, default='')
    avatar = db.Column(db.String(128), default='')
    banner = db.Column(db.String(128), default='')
    background = db.Column(db.String(128), default='')
    music_url = db.Column(db.String(512), default='')
    audio_file = db.Column(db.String(128), default='')
    audio_icon = db.Column(db.String(128), default='')
    discord_user = db.Column(db.String(64), default='')
    discord_status = db.Column(db.String(128), default='Online')
    accent = db.Column(db.String(7), default='#8b5cf6')
    text_color = db.Column(db.String(7), default='#ffffff')
    card_opacity = db.Column(db.Float, default=0.4)
    card_blur = db.Column(db.Integer, default=25)
    enable_animations = db.Column(db.Boolean, default=True)
    theme = db.Column(db.String(32), default='default')
    page_title = db.Column(db.String(128), default='')
    views = db.Column(db.Integer, default=0)


class Link(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    platform = db.Column(db.String(32), default='website')
    label = db.Column(db.String(64), default='')
    url = db.Column(db.String(512), nullable=False)
    visible = db.Column(db.Boolean, default=True)
    position = db.Column(db.Integer, default=0)
    clicks = db.Column(db.Integer, default=0)
    click_events = db.relationship('Click', backref='link', cascade='all, delete-orphan')


class Click(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    link_id = db.Column(db.Integer, db.ForeignKey('link.id'), nullable=False)
    day = db.Column(db.Date, default=date.today)


class Badge(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    name = db.Column(db.String(32), nullable=False)
    icon = db.Column(db.String(32), nullable=False)
    visible = db.Column(db.Boolean, default=True)


@login_manager.user_loader
def load_user(uid):
    return db.session.get(User, int(uid))


def allowed_file(name, allowed_set=ALLOWED):
    return '.' in name and name.rsplit('.', 1)[1].lower() in allowed_set


def save_upload(file, allowed_set=ALLOWED):
    if not file or file.filename == '':
        return None
    if not allowed_file(file.filename, allowed_set):
        flash(f'Invalid file type. Allowed: {", ".join(sorted(allowed_set))}')
        return None
    ext = file.filename.rsplit('.', 1)[1].lower()
    fname = secrets.token_hex(16) + '.' + ext
    file.save(os.path.join(app.config['UPLOAD_FOLDER'], fname))
    return fname


def delete_upload(fname):
    if fname and not fname.startswith('fa-'):
        path = os.path.join(app.config['UPLOAD_FOLDER'], fname)
        if os.path.exists(path):
            os.remove(path)


with app.app_context():
    db.create_all()

# --- BASE HTML WITH PARTICLES ---
BASE = """
<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{ title or 'Dvora.lol' }}</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<link rel="stylesheet" href="/static/style.css">
<script>
    document.addEventListener('contextmenu', event => event.preventDefault());
    document.addEventListener('keydown', function(event) {
      if (event.key === 'F12' || (event.ctrlKey && event.shiftKey && (event.key === 'I' || event.key === 'J' || event.key === 'C')) || (event.ctrlKey && (event.key === 'u' || event.key === 'U'))) {
        event.preventDefault(); return false;
      }
    });
</script>
</head>
<body>
<canvas id="particles" style="position:fixed;top:0;left:0;width:100%;height:100%;z-index:-1;pointer-events:none;"></canvas>
<nav><a href="/" class="brand">Dvora<span>.lol</span></a><div>
{% if current_user.is_authenticated %}
{% if current_user.is_admin %}<a href="/admin" style="color: #ff4b4b; font-weight: bold;"><i class="fa-solid fa-shield-halved"></i> Admin</a>{% endif %}
<a href="/dashboard"><i class="fa-solid fa-gauge"></i> Dashboard</a><a href="/logout"><i class="fa-solid fa-arrow-right-from-bracket"></i> Logout</a>
{% else %}<a href="/login">Login</a><a href="/register">Register</a>{% endif %}
</div></nav><main>{% with m = get_flashed_messages() %}{% for x in m %}<div class="flash">{{ x }}</div>{% endfor %}{% endwith %}
{{ body|safe }}</main>
<script>
    const canvas = document.getElementById('particles');
    const ctx = canvas.getContext('2d');
    canvas.width = window.innerWidth;
    canvas.height = window.innerHeight;
    let particles = [];
    for (let i = 0; i < 50; i++) {
        particles.push({
            x: Math.random() * canvas.width, y: Math.random() * canvas.height,
            radius: Math.random() * 1.5 + 0.5, speedX: Math.random() * 0.5 - 0.25, speedY: Math.random() * 0.5 - 0.25
        });
    }
    function animate() {
        requestAnimationFrame(animate);
        ctx.clearRect(0, 0, canvas.width, canvas.height);
        ctx.fillStyle = 'rgba(139, 92, 246, 0.4)';
        particles.forEach(p => {
            p.x += p.speedX; p.y += p.speedY;
            if (p.x < 0 || p.x > canvas.width) p.speedX *= -1;
            if (p.y < 0 || p.y > canvas.height) p.speedY *= -1;
            ctx.beginPath(); ctx.arc(p.x, p.y, p.radius, 0, Math.PI * 2); ctx.fill();
        });
    }
    animate();
    window.addEventListener('resize', () => { canvas.width = window.innerWidth; canvas.height = window.innerHeight; });
</script>
</body></html>
"""


def page(body, title='Dvora.lol'):
    return render_template_string(BASE, body=body, title=title)


@app.route('/')
def index():
    return page("""<section class="hero">
    <h1>Your identity, one link.</h1>
    <p>Build a premium, fully customizable creator profile at Dvora.lol/yourname.</p>
    <a class="btn" href="/register"><i class="fa-solid fa-rocket"></i> Claim your link</a></section>""")


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        u = request.form['username'].strip().lower()
        e = request.form['email'].strip().lower()
        p = request.form['password']

        if u in ['admin', 'root', 'system', 'dashboard', 'login', 'register', 'logout', 'uploads', 'static', 'go']:
            flash('This username is reserved.')
            return redirect('/register')

        if not (3 <= len(u) <= 32) or not u.replace('_', '').isalnum():
            flash('Username must be 3-32 chars, letters/numbers/underscore.')
            return redirect('/register')
        if User.query.filter_by(username=u).first():
            flash('Username taken')
            return redirect('/register')
        if User.query.filter_by(email=e).first():
            flash('Email already registered')
            return redirect('/register')

        user = User(username=u, email=e, password_hash=generate_password_hash(p))
        user.profile = Profile(display_name=u, page_title=f'{u} | Dvora.lol')
        db.session.add(user)
        db.session.commit()
        login_user(user)
        return redirect('/dashboard')
    return page("""<form method="post" class="card auth-card"><h2>Create Account</h2>
<input name="username" placeholder="Username" required><input name="email" type="email" placeholder="Email" required>
<input name="password" type="password" placeholder="Password" required minlength="6">
<button class="btn w-100">Register</button>
<p style="text-align:center;margin-top:1rem;font-size:0.9rem;">Already have an account? <a href="/login" style="color:#8b5cf6;">Login</a></p></form>""", 'Register')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        u = request.form['username'].strip().lower()
        user = User.query.filter_by(username=u).first()
        if user and check_password_hash(user.password_hash, request.form['password']):
            login_user(user)
            return redirect('/dashboard')
        flash('Invalid credentials')
    return page("""<form method="post" class="card auth-card"><h2>Welcome Back</h2>
<input name="username" placeholder="Username" required><input name="password" type="password" placeholder="Password" required>
<button class="btn w-100">Login</button>
<p style="text-align:center;margin-top:1rem;font-size:0.9rem;">Don't have an account? <a href="/register" style="color:#8b5cf6;">Register</a></p></form>""", 'Login')


@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect('/')


def dash(body, active):
    nav = ''.join(f'<a class="{"active" if k==active else ""}" href="/dashboard{s}"><i class="fa-solid {i}"></i> {n}</a>'
                  for k, s, n, i in [('overview', '', 'Overview', 'fa-chart-pie'), ('profile', '/profile', 'Profile', 'fa-user'),
                  ('links', '/links', 'Links', 'fa-link'), ('badges', '/badges', 'Badges', 'fa-medal'),
                  ('appearance', '/appearance', 'Appearance', 'fa-palette'), ('analytics', '/analytics', 'Analytics', 'fa-chart-line'),
                  ('settings', '/settings', 'Settings', 'fa-gear')])
    return page(f'<div class="dash"><aside>{nav}<hr style="border-color:rgba(255,255,255,0.05);margin:1rem 0;"><a href="/{current_user.username}" target="_blank"><i class="fa-solid fa-eye"></i> View public</a></aside><section class="dash-body">{body}</section></div>')


@app.route('/dashboard')
@login_required
def dashboard():
    p = current_user.profile
    return dash(f"""<h2>Welcome, {escape(p.display_name)}</h2>
<div class="stats"><div class="stat"><i class="fa-solid fa-eye" style="color:#3b82f6;"></i><span>{p.views}</span>Profile views</div>
<div class="stat"><i class="fa-solid fa-link" style="color:#8b5cf6;"></i><span>{len(current_user.links)}</span>Links</div>
<div class="stat"><i class="fa-solid fa-arrow-pointer" style="color:#10b981;"></i><span>{sum(l.clicks for l in current_user.links)}</span>Total clicks</div></div>
<div class="card"><p>Your public page is live at: <a href="/{current_user.username}" target="_blank" style="color:#8b5cf6;font-weight:bold;">/{current_user.username}</a></p></div>""", 'overview')


@app.route('/dashboard/profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    p = current_user.profile
    if request.method == 'POST':
        p.display_name = request.form.get('display_name', '')[:64]
        p.bio = request.form.get('bio', '')[:500]
        p.music_url = request.form.get('music_url', '')[:512]
        p.discord_user = request.form.get('discord_user', '')[:64]
        p.discord_status = request.form.get('discord_status', '')[:128]
        p.page_title = request.form.get('page_title', '')[:128]

        if request.form.get('remove_audio'):
            delete_upload(p.audio_file)
            p.audio_file = ''

        if request.form.get('reset_audio_icon'):
            delete_upload(p.audio_icon)
            p.audio_icon = ''

        a = save_upload(request.files.get('avatar'), IMAGE_EXTS)
        b = save_upload(request.files.get('banner'), IMAGE_EXTS)
        bg = save_upload(request.files.get('background'), IMAGE_EXTS)
        au = save_upload(request.files.get('audio'), AUDIO_EXTS)
        icon_img = save_upload(request.files.get('audio_icon_file'), IMAGE_EXTS)
        icon_fa = request.form.get('audio_icon_fa', '').strip()[:64]

        if a:
            delete_upload(p.avatar)
            p.avatar = a
        if b:
            delete_upload(p.banner)
            p.banner = b
        if bg:
            delete_upload(p.background)
            p.background = bg
        if au:
            delete_upload(p.audio_file)
            p.audio_file = au
        if icon_img:
            delete_upload(p.audio_icon)
            p.audio_icon = icon_img
        elif icon_fa:
            delete_upload(p.audio_icon)
            p.audio_icon = icon_fa if icon_fa.startswith('fa-') else f'fa-{icon_fa}'

        db.session.commit()
        flash('Profile saved successfully!')
        return redirect('/dashboard/profile')

    audio_status_html = ''
    if p.audio_file:
        audio_status_html = f"""
        <div style="margin:0.5rem 0 0.9rem;padding:0.75rem 1rem;border-radius:10px;background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:0.5rem;">
            <span style="font-size:0.88rem;"><i class="fa-solid fa-music" style="color:#8b5cf6;"></i> Uploaded: <b>{escape(p.audio_file)}</b></span>
            <label style="display:inline-flex;align-items:center;gap:6px;margin:0;font-size:0.85rem;cursor:pointer;">
                <input type="checkbox" name="remove_audio" value="1" style="width:auto;margin:0;"> Remove audio
            </label>
        </div>"""

    icon_status_html = ''
    if p.audio_icon:
        icon_status_html = f"""
        <label style="display:inline-flex;align-items:center;gap:6px;margin-top:0.35rem;font-size:0.82rem;cursor:pointer;">
            <input type="checkbox" name="reset_audio_icon" value="1" style="width:auto;margin:0;"> Reset custom icon ({escape(p.audio_icon)})
        </label>"""

    fa_val = p.audio_icon if p.audio_icon.startswith('fa-') else ''

    return dash(f"""<form method="post" enctype="multipart/form-data" class="card"><h2>Edit Profile</h2>
<div class="grid-2"><label>Display name<input name="display_name" value="{escape(p.display_name)}"></label>
<label>Page title<input name="page_title" value="{escape(p.page_title)}"></label></div>
<label>Bio<textarea name="bio" rows="3">{escape(p.bio)}</textarea></label>
<div class="grid-2"><label>Discord User<input name="discord_user" value="{escape(p.discord_user)}" placeholder="e.g. dvora"></label>
<label>Discord Status<input name="discord_status" value="{escape(p.discord_status)}"></label></div>
<div class="grid-2">
  <label>Audio File (MP3, WAV, MP4)<input type="file" name="audio" accept=".mp3,.wav,.mp4,audio/mpeg,audio/wav,video/mp4"></label>
  <label>Or Direct Audio URL<input name="music_url" value="{escape(p.music_url)}" placeholder="https://..."></label>
</div>
{audio_status_html}
<div class="grid-2">
  <label>Custom Icon Image<input type="file" name="audio_icon_file" accept="image/*"></label>
  <label>Or Icon Class (e.g. fa-headphones, fa-compact-disc)<input name="audio_icon_fa" value="{escape(fa_val)}" placeholder="fa-compact-disc"></label>
</div>
{icon_status_html}
<div class="grid-2"><label>Avatar<input type="file" name="avatar" accept="image/*"></label>
<label>Banner<input type="file" name="banner" accept="image/*"></label></div>
<label>Custom Background Image<input type="file" name="background" accept="image/*"></label>
<button class="btn" style="margin-top:0.75rem;"><i class="fa-solid fa-floppy-disk"></i> Save Changes</button></form>""", 'profile')


@app.route('/dashboard/links', methods=['GET', 'POST'])
@login_required
def links():
    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'add':
            url = request.form.get('url', '').strip()
            if not url.startswith(('http://', 'https://')):
                flash('URL must start with http:// or https://')
                return redirect('/dashboard/links')
            pos = (max([l.position for l in current_user.links], default=0)) + 1
            db.session.add(Link(user_id=current_user.id, platform=request.form.get('platform', 'website')[:32],
                                label=request.form.get('label', '')[:64], url=url[:512], position=pos))
        elif action == 'delete':
            l = db.session.get(Link, int(request.form['id']))
            if l and l.user_id == current_user.id:
                db.session.delete(l)
        elif action == 'toggle':
            l = db.session.get(Link, int(request.form['id']))
            if l and l.user_id == current_user.id:
                l.visible = not l.visible
        elif action == 'up':
            l = db.session.get(Link, int(request.form['id']))
            if l and l.user_id == current_user.id:
                prev = Link.query.filter_by(user_id=current_user.id).filter(Link.position < l.position).order_by(Link.position.desc()).first()
                if prev:
                    l.position, prev.position = prev.position, l.position
        db.session.commit()
        return redirect('/dashboard/links')
    rows = ''.join(f"""<div class="row"><span><i class="fa-brands fa-{l.platform}"></i> {escape(l.label or l.url[:30])} {'(hidden)' if not l.visible else ''}</span>
    <div style="display:flex;gap:5px;">
    <form method="post"><input type="hidden" name="id" value="{l.id}"><input type="hidden" name="action" value="up"><button class="mini"><i class="fa-solid fa-arrow-up"></i></button></form>
    <form method="post"><input type="hidden" name="id" value="{l.id}"><input type="hidden" name="action" value="toggle"><button class="mini"><i class="fa-solid fa-eye"></i></button></form>
    <form method="post"><input type="hidden" name="id" value="{l.id}"><input type="hidden" name="action" value="delete"><button class="mini"><i class="fa-solid fa-trash"></i></button></form>
    </div></div>""" for l in current_user.links)
    return dash(f"""<h2>Links</h2><div class="card">{rows or '<p>No links yet.</p>'}</div>
<form method="post" class="card"><h3>Add link</h3>
<select name="platform">{''.join(f'<option>{x}</option>' for x in ['discord','youtube','tiktok','roblox','steam','github','instagram','website'])}</select>
<input name="label" placeholder="Label"><input name="url" placeholder="https://..." required>
<button class="btn"><i class="fa-solid fa-plus"></i> Add Link</button></form>""", 'links')


@app.route('/dashboard/badges', methods=['GET', 'POST'])
@login_required
def manage_badges():
    if request.method == 'POST' and current_user.is_admin:
        action = request.form.get('action')
        if action == 'toggle':
            name = request.form.get('name')
            icon = request.form.get('icon')
            existing = Badge.query.filter_by(user_id=current_user.id, name=name).first()
            if existing:
                db.session.delete(existing)
            else:
                db.session.add(Badge(user_id=current_user.id, name=name, icon=icon))
            db.session.commit()
            return redirect('/dashboard/badges')

    user_badges = {b.name for b in current_user.badges}
    rows = ''

    if current_user.is_admin:
        for b in BADGES_LIST:
            has_badge = b['name'] in user_badges
            btn_text = "Remove" if has_badge else "Unlock"
            btn_class = "mini" if has_badge else "btn"
            rows += f"""<div class="row" style="padding: 1rem 0;">
                <span style="font-size: 1.1rem; display:flex; align-items:center; gap:10px;">
                    <i class="fa-solid {b['icon']}" style="color:#8b5cf6; font-size:1.2rem; width:20px;"></i> <b>{b['name']}</b>
                </span>
                <form method="post">
                    <input type="hidden" name="action" value="toggle"><input type="hidden" name="name" value="{b['name']}"><input type="hidden" name="icon" value="{b['icon']}">
                    <button class="{btn_class}" style="padding: 0.4rem 1rem;">{btn_text}</button>
                </form>
            </div>"""
        title = "Manage Your Badges (Admin)"
        subtitle = "Toggle badges to display them on your own profile."
    else:
        if user_badges:
            for b in BADGES_LIST:
                if b['name'] in user_badges:
                    rows += f"""<div class="row" style="padding: 1rem 0;">
                        <span style="font-size: 1.1rem; display:flex; align-items:center; gap:10px;">
                            <i class="fa-solid {b['icon']}" style="color:#8b5cf6; font-size:1.2rem; width:20px;"></i> <b>{b['name']}</b>
                        </span>
                        <span style="color: #10b981; font-size: 0.9rem;">Unlocked</span>
                    </div>"""
        else:
            rows = "<p>You don't have any badges yet.</p>"
        title = "Your Badges"
        subtitle = "These are the badges you have earned. Only admins can grant new ones."

    return dash(f"""<div class="card"><h2>{title}</h2><p style="color:#a1a1aa; margin-bottom:1rem;">{subtitle}</p>{rows}</div>""", 'badges')


@app.route('/dashboard/appearance', methods=['GET', 'POST'])
@login_required
def appearance():
    p = current_user.profile
    if request.method == 'POST':
        p.accent = request.form.get('accent', '#8b5cf6')[:7]
        p.text_color = request.form.get('text_color', '#ffffff')[:7]
        p.card_opacity = float(request.form.get('card_opacity', 0.4))
        p.card_blur = int(request.form.get('card_blur', 25))
        p.theme = request.form.get('theme', 'default')
        p.enable_animations = 'enable_animations' in request.form
        db.session.commit()
        flash('Appearance saved')
        return redirect('/dashboard/appearance')
    return dash(f"""<form method="post" class="card"><h2>Appearance</h2>
<div class="grid-2"><label>Accent color<input type="color" name="accent" value="{p.accent}"></label>
<label>Text color<input type="color" name="text_color" value="{p.text_color}"></label></div>
<label>Card Opacity (0.1 - 1.0)<input type="number" name="card_opacity" step="0.1" min="0.1" max="1.0" value="{p.card_opacity}"></label>
<label>Card Blur (px)<input type="number" name="card_blur" min="0" max="50" value="{p.card_blur}"></label>
<label>Theme<select name="theme">
    <option value="default" {'selected' if p.theme=='default' else ''}>Dark (Default)</option>
    <option value="midnight" {'selected' if p.theme=='midnight' else ''}>Midnight Blue</option>
    <option value="crimson" {'selected' if p.theme=='crimson' else ''}>Crimson</option>
    <option value="emerald" {'selected' if p.theme=='emerald' else ''}>Emerald</option>
</select></label>
<label style="display:flex;align-items:center;gap:10px;margin-top:1rem;"><input type="checkbox" name="enable_animations" {'checked' if p.enable_animations else ''} style="width:auto;margin:0;"> Enable Animations (Gradient & Typing)</label>
<button class="btn" style="margin-top:1rem;"><i class="fa-solid fa-paint-brush"></i> Save Appearance</button></form>""", 'appearance')


@app.route('/dashboard/analytics')
@login_required
def analytics():
    user_links = current_user.links
    top = sorted(user_links, key=lambda l: l.clicks, reverse=True)[:5]
    rows = ''.join(f'<div class="row"><span>{escape(l.label or l.platform)}</span><span style="color:#8b5cf6;font-weight:bold;">{l.clicks} clicks</span></div>' for l in top) or '<p>No clicks yet.</p>'
    days = db.session.query(Click.day, db.func.count(Click.id)).join(Link).filter(Link.user_id == current_user.id).group_by(Click.day).all()
    bars = ''.join(f'<div class="bar"><div style="height:{min(c*10,100)}%"></div><small>{d.strftime("%m/%d")}</small></div>' for d, c in days) or '<p>No data.</p>'
    return dash(f"""<h2>Analytics</h2><div class="stats"><div class="stat"><i class="fa-solid fa-eye" style="color:#3b82f6;"></i><span>{current_user.profile.views}</span>Views</div>
<div class="stat"><i class="fa-solid fa-arrow-pointer" style="color:#10b981;"></i><span>{sum(l.clicks for l in user_links)}</span>Clicks</div></div>
<div class="card"><h3>Top links</h3>{rows}</div><div class="card"><h3>Daily clicks</h3><div class="chart">{bars}</div></div>""", 'analytics')


@app.route('/dashboard/settings', methods=['GET', 'POST'])
@login_required
def settings():
    if request.method == 'POST':
        new = request.form.get('new_password')
        if new and len(new) >= 6:
            current_user.password_hash = generate_password_hash(new)
            db.session.commit()
            flash('Password updated')
        else:
            flash('Password must be 6+ chars')
        return redirect('/dashboard/settings')
    return dash(f"""<form method="post" class="card"><h2>Account Settings</h2>
<p style="margin-bottom:1rem;">Username: <b style="color:#8b5cf6;">{current_user.username}</b></p><p style="margin-bottom:1rem;">Email: {escape(current_user.email)}</p>
<label>New password<input type="password" name="new_password" minlength="6"></label>
<button class="btn" style="margin-top:1rem;"><i class="fa-solid fa-key"></i> Update Password</button></form>""", 'settings')


@app.route('/uploads/<path:f>')
def uploaded(f):
    return send_from_directory(app.config['UPLOAD_FOLDER'], f)


@app.route('/go/<int:link_id>')
def track_link(link_id):
    link = db.session.get(Link, link_id)
    if not link or not link.visible:
        abort(404)
    link.clicks += 1
    db.session.add(Click(link_id=link.id))
    db.session.commit()
    return redirect(link.url)


@app.route('/admin', methods=['GET', 'POST'])
@login_required
def admin():
    if not current_user.is_admin:
        abort(403)
    if request.method == 'POST':
        action = request.form.get('action')
        target_user = User.query.filter_by(username=request.form.get('username', '').lower()).first()
        badge_name = request.form.get('badge_name')
        badge_info = next((b for b in BADGES_LIST if b['name'] == badge_name), None)

        if target_user:
            if action in ['give', 'remove'] and badge_info:
                if action == 'give':
                    existing = Badge.query.filter_by(user_id=target_user.id, name=badge_name).first()
                    if not existing:
                        db.session.add(Badge(user_id=target_user.id, name=badge_name, icon=badge_info['icon']))
                elif action == 'remove':
                    Badge.query.filter_by(user_id=target_user.id, name=badge_name).delete()
                flash(f'Updated badges for {target_user.username}')
            elif action == 'give_views':
                amount = int(request.form.get('view_amount', 0))
                if target_user.profile:
                    target_user.profile.views += amount
                    flash(f'Gave {amount} views to {target_user.username}')
            db.session.commit()
        return redirect(url_for('admin', q=request.form.get('q', '')))

    query = request.args.get('q', '').strip().lower()
    users = User.query.filter(User.username.ilike(f'%{query}%')).all() if query else User.query.order_by(User.created.desc()).all()
    badge_options_html = ''.join(f'<option value="{b["name"]}">{b["name"]}</option>' for b in BADGES_LIST)

    user_rows = ''
    for u in users:
        u_badges = ', '.join(b.name for b in u.badges) or 'None'
        user_rows += f"""<div class="row" style="flex-direction: column; align-items: flex-start; gap: 0.5rem; padding: 1rem 0;">
            <div style="display:flex; justify-content:space-between; width:100%;"><b style="font-size:1.1rem;">@{u.username}</b><span style="font-size: 0.9rem; color: #a1a1aa;">{escape(u.email)}</span></div>
            <div style="font-size: 0.9rem; margin-bottom: 0.5rem; color:#8b5cf6;">Badges: {u_badges}</div>
            <div style="display:flex; gap: 0.5rem; width:100%; flex-wrap: wrap; margin-top: 5px;">
                <form method="post" style="display:flex; gap:5px; align-items:center;">
                    <input type="hidden" name="username" value="{u.username}"><input type="hidden" name="q" value="{escape(query)}">
                    <select name="badge_name" style="margin:0; padding:0.4rem;">{badge_options_html}</select>
                    <button name="action" value="give" class="btn" style="padding:0.4rem 0.8rem;">Give</button>
                    <button name="action" value="remove" class="mini" style="padding:0.4rem 0.8rem;">Remove</button>
                </form>
                <form method="post" style="display:flex; gap:5px; align-items:center;">
                    <input type="hidden" name="username" value="{u.username}"><input type="hidden" name="q" value="{escape(query)}">
                    <input type="hidden" name="action" value="give_views">
                    <input type="number" name="view_amount" placeholder="Views" style="width:90px; margin:0; padding:0.4rem;" required>
                    <button class="mini" style="padding:0.4rem 0.8rem;">+ Views</button>
                </form>
            </div>
        </div>"""

    return page(f"""<div class="card"><h2>Admin Panel</h2>
        <form method="get" style="display:flex; gap:0.5rem; margin:1rem 0;">
            <input name="q" value="{escape(query)}" placeholder="Search username..." style="margin:0;">
            <button class="btn">Search</button>
        </form>
        {user_rows or '<p>No users found.</p>'}
    </div>""", 'Admin Panel')


# --- PUBLIC PROFILE PAGE ---
PUBLIC_PROFILE_HTML = """
<!doctype html>
<html>
<head>
<meta charset="utf-8">
<meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{ p.page_title or (p.display_name ~ ' | Dvora.lol') }}</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<link rel="stylesheet" href="/static/style.css">
<style>
  :root { --accent: {{ p.accent }}; }
  body { color: {{ p.text_color }}; }
  .profile {
    background: rgba(20, 20, 25, {{ p.card_opacity }});
    backdrop-filter: blur({{ p.card_blur }}px);
    -webkit-backdrop-filter: blur({{ p.card_blur }}px);
  }
</style>
</head>
<body class="theme-{{ p.theme }}">
{% if p.background %}
<div class="page-bg" style="background-image: url('/uploads/{{ p.background }}');"></div>
{% endif %}

{% if audio_src %}
<button type="button" id="audioToggleBtn" class="audio-glow-btn playing" title="Toggle Audio" aria-label="Toggle Audio">
  {% if p.audio_icon and p.audio_icon.startswith('fa-') %}
    <i class="{{ p.audio_icon }}"></i>
  {% elif p.audio_icon %}
    <img src="/uploads/{{ p.audio_icon }}" alt="Audio Icon">
  {% else %}
    <i class="fa-solid fa-compact-disc"></i>
  {% endif %}
</button>
<audio id="bgAudio" src="{{ audio_src }}" loop preload="auto" playsinline></audio>
{% endif %}

<div class="profile-container">
  <div class="profile">
    {% if p.banner %}
      <div class="banner" style="background-image: url('/uploads/{{ p.banner }}');"></div>
    {% else %}
      <div class="banner" style="background: linear-gradient(135deg, {{ p.accent }}, transparent);"></div>
    {% endif %}

    {% if p.avatar %}
      <img class="avatar" src="/uploads/{{ p.avatar }}" alt="{{ p.display_name }}">
    {% else %}
      <div class="avatar" style="margin: 0 auto 1rem; display:flex; align-items:center; justify-content:center; font-size:2rem; font-weight:800; color:{{ p.accent }};">
        {{ user.username[0]|upper }}
      </div>
    {% endif %}

    <h1 class="{% if p.enable_animations %}animated-name{% endif %}">{{ p.display_name or user.username }}</h1>

    {% if badges %}
    <div class="badges-container">
      {% for b in badges %}
        <span class="badge" data-name="{{ b.name }}"><i class="fa-solid {{ b.icon }}"></i></span>
      {% endfor %}
    </div>
    {% endif %}

    {% if p.bio %}
      <p>{{ p.bio }}</p>
    {% endif %}

    {% if p.discord_user %}
    <div class="discord-widget">
      <i class="fa-brands fa-discord" style="font-size:1.3rem;color:#5865F2;"></i>
      <span><b>{{ p.discord_user }}</b> · {{ p.discord_status or 'Online' }}</span>
    </div>
    {% endif %}

    {% if visible_links %}
    <div>
      {% for l in visible_links %}
      <a class="link" href="/go/{{ l.id }}" target="_blank" rel="noopener">
        <span style="display:flex;align-items:center;gap:10px;">
          {% if l.platform == 'website' %}
            <i class="fa-solid fa-globe" style="width:20px;"></i>
          {% else %}
            <i class="fa-brands fa-{{ l.platform }}" style="width:20px;"></i>
          {% endif %}
          <span>{{ l.label or l.platform|capitalize }}</span>
        </span>
        <i class="fa-solid fa-chevron-right link-arrow" style="font-size:0.85rem;"></i>
      </a>
      {% endfor %}
    </div>
    {% endif %}

    <div style="margin-top:1.5rem;font-size:0.85rem;">
      <span class="glow-text"><i class="fa-solid fa-eye"></i> {{ p.views }} views</span>
    </div>
  </div>
</div>

{% if audio_src %}
<script>
  (function() {
    const audio = document.getElementById('bgAudio');
    const btn = document.getElementById('audioToggleBtn');
    if (!audio || !btn) return;

    let userMuted = false;

    function syncState() {
      if (!audio.paused && !audio.muted) {
        btn.classList.add('playing');
        btn.classList.remove('muted');
      } else {
        btn.classList.remove('playing');
        btn.classList.add('muted');
      }
    }

    async function tryAutoplay() {
      if (userMuted) return;
      try {
        audio.muted = false;
        await audio.play();
        syncState();
      } catch (err) {
        syncState();
        const unlock = async () => {
          if (userMuted) return;
          try {
            audio.muted = false;
            await audio.play();
          } catch (_) {}
          syncState();
          document.removeEventListener('click', unlock);
          document.removeEventListener('keydown', unlock);
          document.removeEventListener('touchstart', unlock);
        };
        document.addEventListener('click', unlock, { once: true });
        document.addEventListener('keydown', unlock, { once: true });
        document.addEventListener('touchstart', unlock, { once: true });
      }
    }

    btn.addEventListener('click', async (e) => {
      e.stopPropagation();
      if (audio.paused) {
        userMuted = false;
        audio.muted = false;
        try { await audio.play(); } catch (_) {}
      } else {
        userMuted = true;
        audio.pause();
      }
      syncState();
    });

    audio.addEventListener('play', syncState);
    audio.addEventListener('pause', syncState);
    window.addEventListener('DOMContentLoaded', tryAutoplay);
    tryAutoplay();
  })();
</script>
{% endif %}
</body>
</html>
"""


@app.route('/<username>')
def public_profile(username):
    user = User.query.filter_by(username=username.lower()).first_or_404()
    p = user.profile
    p.views += 1
    db.session.commit()

    audio_src = f"/uploads/{p.audio_file}" if p.audio_file else (p.music_url or '')
    visible_links = [l for l in user.links if l.visible]
    visible_badges = [b for b in user.badges if b.visible]

    return render_template_string(
        PUBLIC_PROFILE_HTML,
        user=user,
        p=p,
        audio_src=audio_src,
        visible_links=visible_links,
        badges=visible_badges,
    )


if __name__ == '__main__':
    app.run(debug=True)
