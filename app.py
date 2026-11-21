import os
import secrets
from datetime import datetime, date
from flask import Flask, render_template_string, request, redirect, url_for, flash, send_from_directory, abort, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from markupsafe import escape

app = Flask(__name__, static_folder='.', static_url_path='/static')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or secrets.token_hex(32)

os.makedirs(app.instance_path, exist_ok=True)
db_path = os.path.join(app.instance_path, 'dvora.db')
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

app.config['UPLOAD_FOLDER'] = os.path.join(app.root_path, 'uploads')
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

IMAGE_EXTS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
AUDIO_EXTS = {'mp3', 'wav', 'mp4'}
ALLOWED = IMAGE_EXTS | AUDIO_EXTS

ADMIN_BADGES = {'Developer', 'Owner', 'Moderator', 'Admin', 'Staff'}

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
    is_banned = db.Column(db.Boolean, default=False)
    ban_reason = db.Column(db.String(256), default='')
    created = db.Column(db.DateTime, default=datetime.utcnow)

    profile = db.relationship('Profile', backref='user', uselist=False, cascade='all, delete-orphan')
    links = db.relationship('Link', backref='user', cascade='all, delete-orphan', order_by='Link.position')
    badges = db.relationship('Badge', backref='user', cascade='all, delete-orphan')
    warnings = db.relationship('Warning', backref='user', cascade='all, delete-orphan', order_by='Warning.created.desc()')
    messages_received = db.relationship('DirectMessage', foreign_keys='DirectMessage.recipient_id', backref='recipient', cascade='all, delete-orphan', order_by='DirectMessage.created.desc()')

    @property
    def is_admin(self):
        if self.username == 'dvora':
            return True
        return any(b.name in ADMIN_BADGES and b.visible for b in self.badges)


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
    audio_title = db.Column(db.String(128), default='')
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


class Warning(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    issued_by = db.Column(db.String(32), nullable=False)
    reason = db.Column(db.String(512), nullable=False)
    created = db.Column(db.DateTime, default=datetime.utcnow)


class DirectMessage(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    sender_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    recipient_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    body = db.Column(db.Text, nullable=False)
    created = db.Column(db.DateTime, default=datetime.utcnow)
    sender = db.relationship('User', foreign_keys=[sender_id])


class Announcement(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(128), nullable=False)
    body = db.Column(db.Text, nullable=False)
    author = db.Column(db.String(32), nullable=False)
    active = db.Column(db.Boolean, default=True)
    created = db.Column(db.DateTime, default=datetime.utcnow)


@login_manager.user_loader
def load_user(uid):
    user = db.session.get(User, int(uid))
    if user and not user.profile:
        user.profile = Profile(display_name=user.username, page_title=f'{user.username} | Dvora.lol')
        db.session.commit()
    return user


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
    if fname:
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
</head>
<body>
<canvas id="particles" style="position:fixed;top:0;left:0;width:100%;height:100%;z-index:-1;pointer-events:none;"></canvas>
<nav><a href="/" class="brand">Dvora<span>.lol</span></a><div>
{% if session.get('impersonator_id') %}
<a href="/admin/stop-impersonate" style="color: #fbbf24; font-weight: bold;"><i class="fa-solid fa-user-secret"></i> Exit Impersonation</a>
{% endif %}
{% if current_user.is_authenticated %}
{% if current_user.is_admin %}<a href="/admin" style="color: #ff4b4b; font-weight: bold;"><i class="fa-solid fa-shield-halved"></i> Admin</a>{% endif %}
<a href="/dashboard"><i class="fa-solid fa-gauge"></i> Dashboard</a><a href="/logout"><i class="fa-solid fa-arrow-right-from-bracket"></i> Logout</a>
{% else %}<a href="/login">Login</a><a href="/register">Register</a>{% endif %}
</div></nav><main>
{% if announcements %}
  {% for ann in announcements %}
    <div class="flash" style="border-color:#38bdf8;background:rgba(56,189,248,0.12);color:#e0f2fe;">
      <b><i class="fa-solid fa-bullhorn"></i> {{ ann.title }}</b> ({{ ann.author }}): {{ ann.body }}
    </div>
  {% endfor %}
{% endif %}
{% with m = get_flashed_messages() %}{% for x in m %}<div class="flash">{{ x }}</div>{% endfor %}{% endwith %}
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
    active_anns = Announcement.query.filter_by(active=True).order_by(Announcement.created.desc()).limit(3).all()
    return render_template_string(BASE, body=body, title=title, announcements=active_anns)


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
            if user.is_banned:
                flash(f"Your account is banned. Reason: {user.ban_reason or 'Violation of terms.'}")
                return redirect('/login')
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
    session.pop('impersonator_id', None)
    logout_user()
    return redirect('/')


@app.route('/admin/stop-impersonate')
@login_required
def stop_impersonate():
    admin_id = session.pop('impersonator_id', None)
    if admin_id:
        admin_user = db.session.get(User, int(admin_id))
        if admin_user:
            login_user(admin_user)
            flash('Returned to your staff session.')
            return redirect('/admin')
    return redirect('/dashboard')


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
    warn_html = ''
    if current_user.warnings:
        items = ''.join(f'<div class="row"><span><b>{escape(w.reason)}</b> <small style="opacity:0.7;">by @{escape(w.issued_by)}</small></span><small>{w.created.strftime("%Y-%m-%d")}</small></div>' for w in current_user.warnings)
        warn_html = f'<div class="card" style="border-color:rgba(245,158,11,0.4);"><h3><i class="fa-solid fa-triangle-exclamation" style="color:#f59e0b;"></i> Warnings ({len(current_user.warnings)})</h3>{items}</div>'

    msg_html = ''
    if current_user.messages_received:
        m_items = ''.join(f'<div class="row"><span><b>@{escape(m.sender.username if m.sender else "Staff")}:</b> {escape(m.body)}</span><small>{m.created.strftime("%Y-%m-%d %H:%M")}</small></div>' for m in current_user.messages_received)
        msg_html = f'<div class="card"><h3><i class="fa-solid fa-envelope" style="color:#8b5cf6;"></i> Messages ({len(current_user.messages_received)})</h3>{m_items}</div>'

    return dash(f"""<h2>Welcome, {escape(p.display_name)}</h2>
<div class="stats"><div class="stat"><i class="fa-solid fa-eye" style="color:#3b82f6;"></i><span>{p.views}</span>Profile views</div>
<div class="stat"><i class="fa-solid fa-link" style="color:#8b5cf6;"></i><span>{len(current_user.links)}</span>Links</div>
<div class="stat"><i class="fa-solid fa-arrow-pointer" style="color:#10b981;"></i><span>{sum(l.clicks for l in current_user.links)}</span>Total clicks</div></div>
<div class="card"><p>Your public page is live at: <a href="/{current_user.username}" target="_blank" style="color:#8b5cf6;font-weight:bold;">/{current_user.username}</a></p></div>
{warn_html}
{msg_html}""", 'overview')


@app.route('/dashboard/profile', methods=['GET', 'POST'])
@login_required
def edit_profile():
    p = current_user.profile
    if request.method == 'POST':
        p.display_name = request.form.get('display_name', '')[:64]
        p.bio = request.form.get('bio', '')[:500]
        p.music_url = request.form.get('music_url', '')[:512]
        p.audio_title = request.form.get('audio_title', '')[:128]
        p.discord_user = request.form.get('discord_user', '')[:64]
        p.discord_status = request.form.get('discord_status', '')[:128]
        p.page_title = request.form.get('page_title', '')[:128]

        if request.form.get('remove_audio'):
            delete_upload(p.audio_file)
            p.audio_file = ''

        a = save_upload(request.files.get('avatar'), IMAGE_EXTS)
        b = save_upload(request.files.get('banner'), IMAGE_EXTS)
        bg = save_upload(request.files.get('background'), IMAGE_EXTS)
        audio_upload = request.files.get('audio')
        au = save_upload(audio_upload, AUDIO_EXTS)

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
            if not p.audio_title and audio_upload and audio_upload.filename:
                p.audio_title = os.path.splitext(audio_upload.filename)[0][:128]

        db.session.commit()
        flash('Profile saved successfully!')
        return redirect('/dashboard/profile')

    current_audio_html = ''
    if p.audio_file:
        label = escape(p.audio_title or p.audio_file)
        current_audio_html = f"""
        <div style="margin:0.75rem 0;padding:0.85rem;border-radius:10px;background:rgba(255,255,255,0.04);border:1px solid rgba(255,255,255,0.08);">
            <div style="font-size:0.9rem;margin-bottom:0.5rem;"><i class="fa-solid fa-music" style="color:#8b5cf6;"></i> Current Audio: <b>{label}</b></div>
            <audio controls preload="metadata" src="/uploads/{p.audio_file}" style="width:100%;"></audio>
            <label style="display:flex;align-items:center;gap:8px;margin-top:0.5rem;font-size:0.85rem;cursor:pointer;">
                <input type="checkbox" name="remove_audio" value="1" style="width:auto;margin:0;"> Remove uploaded audio
            </label>
        </div>"""

    return dash(f"""<form method="post" enctype="multipart/form-data" class="card"><h2>Edit Profile</h2>
<div class="grid-2"><label>Display name<input name="display_name" value="{escape(p.display_name)}"></label>
<label>Page title<input name="page_title" value="{escape(p.page_title)}"></label></div>
<label>Bio<textarea name="bio" rows="3">{escape(p.bio)}</textarea></label>
<div class="grid-2"><label>Discord User<input name="discord_user" value="{escape(p.discord_user)}" placeholder="e.g. dvora"></label>
<label>Discord Status<input name="discord_status" value="{escape(p.discord_status)}"></label></div>
<div class="grid-2">
  <label>Upload Audio (MP3, WAV, MP4)<input type="file" name="audio" accept=".mp3,.wav,.mp4,audio/mpeg,audio/wav,video/mp4"></label>
  <label>Audio Track Title<input name="audio_title" value="{escape(p.audio_title)}" placeholder="e.g. Midnight Vibes"></label>
</div>
{current_audio_html}
<label>Or External Music URL (MP3/WAV)<input name="music_url" value="{escape(p.music_url)}" placeholder="https://..."></label>
<div class="grid-2"><label>Avatar<input type="file" name="avatar" accept="image/*"></label>
<label>Banner<input type="file" name="banner" accept="image/*"></label></div>
<label>Custom Background Image<input type="file" name="background" accept="image/*"></label>
<button class="btn"><i class="fa-solid fa-floppy-disk"></i> Save Changes</button></form>""", 'profile')


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
                db.session.add(Badge(user_id=current_user.id, name=name, icon=icon, visible=True))
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
        title = "Manage Your Badges (Staff)"
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
        subtitle = "These are the badges you have earned. Only staff can grant new ones."

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
    if link.user and link.user.is_banned:
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
        q_val = request.form.get('q', '')

        if action == 'create_announcement':
            title = request.form.get('ann_title', '').strip()[:128]
            body = request.form.get('ann_body', '').strip()
            if title and body:
                db.session.add(Announcement(title=title, body=body, author=current_user.username, active=True))
                db.session.commit()
                flash('Global announcement published.')
            else:
                flash('Announcement title and message are required.')
            return redirect(url_for('admin', q=q_val))

        if action == 'toggle_announcement':
            ann = db.session.get(Announcement, int(request.form.get('ann_id', 0)))
            if ann:
                ann.active = not ann.active
                db.session.commit()
                flash('Announcement status updated.')
            return redirect(url_for('admin', q=q_val))

        if action == 'delete_announcement':
            ann = db.session.get(Announcement, int(request.form.get('ann_id', 0)))
            if ann:
                db.session.delete(ann)
                db.session.commit()
                flash('Announcement deleted.')
            return redirect(url_for('admin', q=q_val))

        target_user = User.query.filter_by(username=request.form.get('username', '').strip().lower()).first()
        if not target_user:
            flash('Target user not found.')
            return redirect(url_for('admin', q=q_val))

        if action in ['give', 'remove']:
            badge_name = request.form.get('badge_name')
            badge_info = next((b for b in BADGES_LIST if b['name'] == badge_name), None)
            if badge_info:
                if action == 'give':
                    existing = Badge.query.filter_by(user_id=target_user.id, name=badge_name).first()
                    if not existing:
                        db.session.add(Badge(user_id=target_user.id, name=badge_name, icon=badge_info['icon'], visible=True))
                elif action == 'remove':
                    Badge.query.filter_by(user_id=target_user.id, name=badge_name).delete()
                db.session.commit()
                flash(f'Updated badges for @{target_user.username}')

        elif action == 'give_views':
            amount = int(request.form.get('view_amount', 0))
            if not target_user.profile:
                target_user.profile = Profile(user_id=target_user.id, display_name=target_user.username)
            target_user.profile.views = max(0, target_user.profile.views + amount)
            db.session.commit()
            flash(f'Adjusted views by {amount} for @{target_user.username}')

        elif action == 'ban':
            if target_user.id == current_user.id:
                flash('You cannot ban yourself.')
            else:
                target_user.is_banned = True
                target_user.ban_reason = request.form.get('ban_reason', '').strip()[:256] or 'Banned by staff'
                db.session.commit()
                flash(f'Banned @{target_user.username}')

        elif action == 'unban':
            target_user.is_banned = False
            target_user.ban_reason = ''
            db.session.commit()
            flash(f'Unbanned @{target_user.username}')

        elif action == 'warn':
            reason = request.form.get('warn_reason', '').strip()[:512]
            if reason:
                db.session.add(Warning(user_id=target_user.id, issued_by=current_user.username, reason=reason))
                db.session.commit()
                flash(f'Warned @{target_user.username}')
            else:
                flash('Please enter a warning reason.')

        elif action == 'message':
            msg_body = request.form.get('dm_body', '').strip()
            if msg_body:
                db.session.add(DirectMessage(sender_id=current_user.id, recipient_id=target_user.id, body=msg_body))
                db.session.commit()
                flash(f'Message sent to @{target_user.username}')
            else:
                flash('Message cannot be empty.')

        elif action == 'impersonate':
            if target_user.id == current_user.id:
                flash('Already logged in as this user.')
            else:
                session['impersonator_id'] = current_user.id
                login_user(target_user)
                flash(f'Now logged in as @{target_user.username}')
                return redirect('/dashboard')

        return redirect(url_for('admin', q=q_val))

    query = request.args.get('q', '').strip().lower()
    users = User.query.filter(User.username.ilike(f'%{query}%')).all() if query else User.query.order_by(User.created.desc()).all()
    badge_options_html = ''.join(f'<option value="{b["name"]}">{b["name"]}</option>' for b in BADGES_LIST)

    all_anns = Announcement.query.order_by(Announcement.created.desc()).all()
    ann_rows = ''.join(
        f"""<div class="row">
            <span><b>{escape(a.title)}</b> — {escape(a.body)} <small style="opacity:0.65;">({'Active' if a.active else 'Hidden'})</small></span>
            <div style="display:flex;gap:5px;">
                <form method="post"><input type="hidden" name="action" value="toggle_announcement"><input type="hidden" name="ann_id" value="{a.id}"><button class="mini">{'Hide' if a.active else 'Show'}</button></form>
                <form method="post"><input type="hidden" name="action" value="delete_announcement"><input type="hidden" name="ann_id" value="{a.id}"><button class="mini"><i class="fa-solid fa-trash"></i></button></form>
            </div>
        </div>"""
        for a in all_anns
    ) or '<p style="opacity:0.7;">No announcements yet.</p>'

    user_rows = ''
    for u in users:
        u_badges = ', '.join(b.name for b in u.badges) or 'None'
        status_tag = f'<span style="color:#ef4444;font-weight:700;">BANNED ({escape(u.ban_reason)})</span>' if u.is_banned else '<span style="color:#10b981;">Active</span>'
        user_rows += f"""<div class="row" style="flex-direction: column; align-items: flex-start; gap: 0.65rem; padding: 1.1rem 0;">
            <div style="display:flex; justify-content:space-between; width:100%; flex-wrap:wrap; gap:8px;">
                <div><b style="font-size:1.1rem;">@{u.username}</b> <span style="margin-left:8px;font-size:0.85rem;">{status_tag}</span></div>
                <span style="font-size: 0.9rem; color: #a1a1aa;">{escape(u.email)} • Warnings: {len(u.warnings)}</span>
            </div>
            <div style="font-size: 0.9rem; color:#8b5cf6;">Badges: {u_badges}</div>

            <div style="display:flex; gap: 0.5rem; width:100%; flex-wrap: wrap;">
                <form method="post" style="display:flex; gap:5px; align-items:center;">
                    <input type="hidden" name="username" value="{u.username}"><input type="hidden" name="q" value="{escape(query)}">
                    <select name="badge_name" style="margin:0; padding:0.4rem; width:auto;">{badge_options_html}</select>
                    <button name="action" value="give" class="btn" style="padding:0.4rem 0.8rem;">Give</button>
                    <button name="action" value="remove" class="mini" style="padding:0.4rem 0.8rem;">Remove</button>
                </form>

                <form method="post" style="display:flex; gap:5px; align-items:center;">
                    <input type="hidden" name="username" value="{u.username}"><input type="hidden" name="q" value="{escape(query)}">
                    <input type="hidden" name="action" value="give_views">
                    <input type="number" name="view_amount" placeholder="Views" style="width:90px; margin:0; padding:0.4rem;" required>
                    <button class="mini" style="padding:0.4rem 0.8rem;">+ Views</button>
                </form>

                <form method="post" style="display:flex; gap:5px; align-items:center;">
                    <input type="hidden" name="username" value="{u.username}"><input type="hidden" name="q" value="{escape(query)}">
                    <input type="hidden" name="action" value="impersonate">
                    <button class="mini" style="padding:0.4rem 0.8rem;border-color:#fbbf24;color:#fbbf24;"><i class="fa-solid fa-right-to-bracket"></i> Login As</button>
                </form>
            </div>

            <div style="display:flex; gap: 0.5rem; width:100%; flex-wrap: wrap;">
                <form method="post" style="display:flex; gap:5px; align-items:center; flex:1; min-width:240px;">
                    <input type="hidden" name="username" value="{u.username}"><input type="hidden" name="q" value="{escape(query)}">
                    <input name="ban_reason" placeholder="Ban reason..." style="margin:0; padding:0.4rem;">
                    {% if False %}{% endif %}
                    {'<button name="action" value="unban" class="btn" style="padding:0.4rem 0.8rem;background:#10b981;color:#000;">Unban</button>' if u.is_banned else '<button name="action" value="ban" class="mini" style="padding:0.4rem 0.8rem;border-color:#ef4444;color:#ef4444;">Ban</button>'}
                </form>

                <form method="post" style="display:flex; gap:5px; align-items:center; flex:1; min-width:240px;">
                    <input type="hidden" name="username" value="{u.username}"><input type="hidden" name="q" value="{escape(query)}">
                    <input type="hidden" name="action" value="warn">
                    <input name="warn_reason" placeholder="Warning reason..." style="margin:0; padding:0.4rem;" required>
                    <button class="mini" style="padding:0.4rem 0.8rem;border-color:#f59e0b;color:#f59e0b;">Warn</button>
                </form>

                <form method="post" style="display:flex; gap:5px; align-items:center; flex:1; min-width:260px;">
                    <input type="hidden" name="username" value="{u.username}"><input type="hidden" name="q" value="{escape(query)}">
                    <input type="hidden" name="action" value="message">
                    <input name="dm_body" placeholder="Send direct message..." style="margin:0; padding:0.4rem;" required>
                    <button class="btn" style="padding:0.4rem 0.8rem;">Message</button>
                </form>
            </div>
        </div>"""

    return page(f"""
    <div class="card">
        <h2><i class="fa-solid fa-bullhorn" style="color:#38bdf8;"></i> Host Global Announcement</h2>
        <form method="post" class="grid-2" style="margin-top:0.75rem;">
            <input type="hidden" name="action" value="create_announcement">
            <input name="ann_title" placeholder="Announcement Title" required>
            <input name="ann_body" placeholder="Announcement Message" required>
        </form>
        <form method="post" style="margin-top:0.5rem;">
            <input type="hidden" name="action" value="create_announcement">
            <div class="grid-2">
                <input name="ann_title" placeholder="Title (e.g. Server Maintenance)" required>
                <input name="ann_body" placeholder="Message shown to users..." required>
            </div>
            <button class="btn" style="margin-top:0.5rem;">Publish Announcement</button>
        </form>
        <div style="margin-top:1rem;">{ann_rows}</div>
    </div>

    <div class="card">
        <h2><i class="fa-solid fa-shield-halved" style="color:#ff4b4b;"></i> Staff Admin Panel</h2>
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
<style>
  * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }
  body {
    min-height: 100vh;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 2rem 1rem;
    color: {{ p.text_color }};
    background: {{ bg_style }};
    background-size: cover;
    background-position: center;
    background-attachment: fixed;
    overflow-x: hidden;
  }
  .profile-card {
    width: 100%;
    max-width: 520px;
    border-radius: 22px;
    overflow: hidden;
    background: rgba(15, 15, 22, {{ p.card_opacity }});
    backdrop-filter: blur({{ p.card_blur }}px);
    -webkit-backdrop-filter: blur({{ p.card_blur }}px);
    border: 1px solid rgba(255, 255, 255, 0.12);
    box-shadow: 0 25px 60px rgba(0, 0, 0, 0.55);
    {% if p.enable_animations %}
    animation: fadeUp 0.6s ease-out;
    {% endif %}
  }
  @keyframes fadeUp {
    from { opacity: 0; transform: translateY(18px); }
    to { opacity: 1; transform: translateY(0); }
  }
  .banner {
    height: 145px;
    width: 100%;
    background: linear-gradient(135deg, {{ p.accent }}, #111827);
    {% if p.banner %}
    background-image: url('/uploads/{{ p.banner }}');
    background-size: cover;
    background-position: center;
    {% endif %}
  }
  .card-inner { padding: 0 1.75rem 1.75rem; text-align: center; }
  .avatar-wrap { margin-top: -54px; display: flex; justify-content: center; }
  .avatar {
    width: 108px; height: 108px; border-radius: 50%; object-fit: cover;
    border: 4px solid {{ p.accent }};
    background: #18181b;
    box-shadow: 0 8px 25px rgba(0,0,0,0.45);
  }
  .display-name {
    font-size: 1.65rem; font-weight: 800; margin-top: 0.75rem;
    {% if p.enable_animations %}
    background: linear-gradient(90deg, {{ p.text_color }}, {{ p.accent }}, {{ p.text_color }});
    background-size: 200% auto;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: shine 4s linear infinite;
    {% endif %}
  }
  @keyframes shine { to { background-position: 200% center; } }
  .username { font-size: 0.9rem; opacity: 0.65; margin-top: 2px; }
  .badges {
    display: flex; flex-wrap: wrap; justify-content: center; gap: 8px;
    margin-top: 0.85rem;
  }
  .badge {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 4px 10px; border-radius: 999px; font-size: 0.78rem; font-weight: 600;
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.12);
  }
  .badge i { color: {{ p.accent }}; }
  .bio {
    margin-top: 0.9rem; font-size: 0.95rem; line-height: 1.5; opacity: 0.9;
    white-space: pre-line;
  }
  .discord-box {
    margin-top: 1rem; padding: 0.75rem 1rem; border-radius: 14px;
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.08);
    display: flex; align-items: center; justify-content: space-between; text-align: left;
  }
  .audio-player {
    margin-top: 1rem; padding: 0.9rem 1rem; border-radius: 14px;
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.1);
    text-align: left;
  }
  .audio-header {
    display: flex; align-items: center; justify-content: space-between;
    margin-bottom: 0.55rem; font-size: 0.88rem; font-weight: 600;
  }
  .audio-player audio {
    width: 100%;
    height: 36px;
    border-radius: 8px;
  }
  .links { display: flex; flex-direction: column; gap: 0.65rem; margin-top: 1.15rem; }
  .link-btn {
    display: flex; align-items: center; justify-content: space-between;
    padding: 0.85rem 1.1rem; border-radius: 14px;
    text-decoration: none; color: {{ p.text_color }}; font-weight: 600;
    background: rgba(255, 255, 255, 0.07);
    border: 1px solid rgba(255, 255, 255, 0.1);
    transition: transform 0.18s ease, background 0.18s ease, border-color 0.18s ease;
  }
  .link-btn:hover {
    transform: translateY(-2px);
    background: rgba(255, 255, 255, 0.13);
    border-color: {{ p.accent }};
  }
  .footer-meta {
    margin-top: 1.35rem; display: flex; justify-content: space-between; align-items: center;
    font-size: 0.8rem; opacity: 0.65;
  }
  .footer-meta a { color: inherit; text-decoration: none; }
</style>
</head>
<body>
  <div class="profile-card">
    <div class="banner"></div>
    <div class="card-inner">
      <div class="avatar-wrap">
        {% if p.avatar %}
          <img class="avatar" src="/uploads/{{ p.avatar }}" alt="{{ p.display_name }}">
        {% else %}
          <div class="avatar" style="display:flex;align-items:center;justify-content:center;font-size:2.2rem;font-weight:800;color:{{ p.accent }};">
            {{ user.username[0]|upper }}
          </div>
        {% endif %}
      </div>

      <h1 class="display-name">{{ p.display_name or user.username }}</h1>
      <div class="username">@{{ user.username }}</div>

      {% if badges %}
      <div class="badges">
        {% for b in badges %}
          <span class="badge"><i class="fa-solid {{ b.icon }}"></i> {{ b.name }}</span>
        {% endfor %}
      </div>
      {% endif %}

      {% if p.bio %}
        <p class="bio">{{ p.bio }}</p>
      {% endif %}

      {% if p.discord_user %}
      <div class="discord-box">
        <div style="display:flex;align-items:center;gap:10px;">
          <i class="fa-brands fa-discord" style="font-size:1.5rem;color:#5865F2;"></i>
          <div>
            <div style="font-weight:700;font-size:0.92rem;">{{ p.discord_user }}</div>
            <div style="font-size:0.8rem;opacity:0.75;">{{ p.discord_status or 'Online' }}</div>
          </div>
        </div>
        <span style="width:10px;height:10px;border-radius:50%;background:#10b981;display:inline-block;"></span>
      </div>
      {% endif %}

      {% if audio_src %}
      <div class="audio-player">
        <div class="audio-header">
          <span><i class="fa-solid fa-music" style="color:{{ p.accent }};margin-right:6px;"></i>{{ p.audio_title or 'Profile Audio' }}</span>
          {% if audio_ext %}<span style="font-size:0.72rem;opacity:0.65;text-transform:uppercase;">{{ audio_ext }}</span>{% endif %}
        </div>
        <audio controls preload="metadata" src="{{ audio_src }}"></audio>
      </div>
      {% endif %}

      {% if visible_links %}
      <div class="links">
        {% for l in visible_links %}
        <a class="link-btn" href="/go/{{ l.id }}" target="_blank" rel="noopener">
          <span style="display:flex;align-items:center;gap:10px;">
            {% if l.platform == 'website' %}
              <i class="fa-solid fa-globe" style="color:{{ p.accent }};width:20px;"></i>
            {% else %}
              <i class="fa-brands fa-{{ l.platform }}" style="color:{{ p.accent }};width:20px;"></i>
            {% endif %}
            <span>{{ l.label or l.platform|capitalize }}</span>
          </span>
          <i class="fa-solid fa-arrow-up-right-from-square" style="font-size:0.8rem;opacity:0.6;"></i>
        </a>
        {% endfor %}
      </div>
      {% endif %}

      <div class="footer-meta">
        <span><i class="fa-solid fa-eye"></i> {{ p.views }} views</span>
        <a href="/">Dvora.lol</a>
      </div>
    </div>
  </div>
</body>
</html>
"""


@app.route('/<username>')
def public_profile(username):
    user = User.query.filter_by(username=username.lower()).first_or_404()
    if user.is_banned:
        abort(404)
    p = user.profile
    if not p:
        p = Profile(user_id=user.id, display_name=user.username, page_title=f'{user.username} | Dvora.lol')
        db.session.add(p)
        db.session.commit()
    p.views += 1
    db.session.commit()

    themes = {
        'default': 'radial-gradient(circle at top, #1e1b4b, #09090b 70%)',
        'midnight': 'radial-gradient(circle at top, #0f172a, #020617 70%)',
        'crimson': 'radial-gradient(circle at top, #450a0a, #09090b 70%)',
        'emerald': 'radial-gradient(circle at top, #064e3b, #09090b 70%)',
    }
    bg_style = f"url('/uploads/{p.background}')" if p.background else themes.get(p.theme, themes['default'])

    audio_src = ''
    audio_ext = ''
    if p.audio_file:
        audio_src = f"/uploads/{p.audio_file}"
        audio_ext = p.audio_file.rsplit('.', 1)[-1].lower()
    elif p.music_url:
        audio_src = p.music_url

    visible_links = [l for l in user.links if l.visible]
    visible_badges = [b for b in user.badges if b.visible]

    return render_template_string(
        PUBLIC_PROFILE_HTML,
        user=user,
        p=p,
        bg_style=bg_style,
        audio_src=audio_src,
        audio_ext=audio_ext,
        visible_links=visible_links,
        badges=visible_badges,
    )


if __name__ == '__main__':
    app.run(debug=False)
