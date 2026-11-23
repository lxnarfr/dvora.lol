import os
import secrets
import tempfile
from datetime import datetime, date
from flask import Flask, render_template_string, request, redirect, url_for, flash, send_from_directory, abort, session
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager, UserMixin, login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash
from markupsafe import escape
from sqlalchemy import inspect, text

app = Flask(__name__, static_folder='.', static_url_path='/static')
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY') or 'dvora-lol-persistent-secret-key-2026'

DATA_DIR = os.environ.get('DATA_DIR', '').strip()
if not DATA_DIR:
    candidate_instance = app.instance_path
    try:
        os.makedirs(candidate_instance, exist_ok=True)
        test_file = os.path.join(candidate_instance, '.write_test')
        with open(test_file, 'w') as f:
            f.write('ok')
        os.remove(test_file)
        DATA_DIR = candidate_instance
    except OSError:
        DATA_DIR = os.path.join(tempfile.gettempdir(), 'dvora_data')
        os.makedirs(DATA_DIR, exist_ok=True)

database_url = os.environ.get('DATABASE_URL', '').strip()
if database_url.startswith('postgres://'):
    database_url = database_url.replace('postgres://', 'postgresql://', 1)

if database_url:
    app.config['SQLALCHEMY_DATABASE_URI'] = database_url
else:
    db_path = os.path.join(DATA_DIR, 'dvora.db')
    app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{db_path}'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

upload_folder = os.environ.get('UPLOAD_FOLDER', '').strip()
if not upload_folder:
    upload_folder = os.path.join(DATA_DIR, 'uploads')
app.config['UPLOAD_FOLDER'] = upload_folder
app.config['MAX_CONTENT_LENGTH'] = 50 * 1024 * 1024
os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)

db = SQLAlchemy(app)
login_manager = LoginManager(app)
login_manager.login_view = 'login'

IMAGE_EXTS = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
AUDIO_EXTS = {'mp3', 'wav', 'mp4'}
ALLOWED = IMAGE_EXTS | AUDIO_EXTS

ADMIN_BADGES = {'Developer', 'Owner', 'Moderator', 'Admin', 'Staff'}

BADGES_LIST = [
    {'name': 'Developer', 'icon': 'fa-code'}, {'name': 'Staff', 'icon': 'fa-shield-halved'},
    {'name': 'Beta Tester', 'icon': 'fa-flask'},
    {'name': 'Content Creator', 'icon': 'fa-video'}, {'name': 'Verified', 'icon': 'fa-circle-check'},
    {'name': 'Premium', 'icon': 'fa-gem'}, {'name': 'OG', 'icon': 'fa-crown'},
    {'name': 'Donor', 'icon': 'fa-heart'}, {'name': 'Bug Hunter', 'icon': 'fa-bug'},
    {'name': 'Early Supporter', 'icon': 'fa-clock'}, {'name': 'Booster', 'icon': 'fa-rocket'},
    {'name': 'Admin', 'icon': 'fa-user-shield'}, {'name': 'Owner', 'icon': 'fa-crown'},
    {'name': 'Partner', 'icon': 'fa-handshake'}, {'name': 'Legend', 'icon': 'fa-dragon'},
    {'name': 'Hacker', 'icon': 'fa-terminal'}, {'name': 'Moderator', 'icon': 'fa-gavel'},
    {'name': 'Gamer', 'icon': 'fa-gamepad'}, {'name': 'Artist', 'icon': 'fa-palette'},
    {'name': 'Music', 'icon': 'fa-music'}, {'name': 'VIP', 'icon': 'fa-star'},
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

BADGE_SHOP_ITEMS = [
    {'name': 'VIP', 'icon': 'fa-star', 'cost': 250, 'desc': 'Stand out with a VIP star badge on your profile.'},
    {'name': 'Gamer', 'icon': 'fa-gamepad', 'cost': 150, 'desc': 'Show off your gaming status.'},
    {'name': 'Music', 'icon': 'fa-music', 'cost': 150, 'desc': 'For music lovers and producers.'},
    {'name': 'Artist', 'icon': 'fa-palette', 'cost': 200, 'desc': 'Showcase your creative flair.'},
    {'name': 'Booster', 'icon': 'fa-rocket', 'cost': 350, 'desc': 'Rocket badge for top supporters.'},
    {'name': 'Elite', 'icon': 'fa-medal', 'cost': 500, 'desc': 'Reserved for dedicated Dvora members.'},
    {'name': 'Legend', 'icon': 'fa-dragon', 'cost': 1000, 'desc': 'Mythic dragon badge for true legends.'},
]


class User(UserMixin, db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(32), unique=True, nullable=False, index=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(256), nullable=False)
    credits = db.Column(db.Integer, default=100)
    last_daily_claim = db.Column(db.Date, nullable=True)
    is_banned = db.Column(db.Boolean, default=False)
    ban_reason = db.Column(db.String(256), default='')
    created = db.Column(db.DateTime, default=datetime.utcnow)

    profile = db.relationship('Profile', backref='user', uselist=False, cascade='all, delete-orphan')
    links = db.relationship('Link', backref='user', cascade='all, delete-orphan', order_by='Link.position')
    badges = db.relationship('Badge', backref='user', cascade='all, delete-orphan')
    warnings = db.relationship('Warning', backref='user', cascade='all, delete-orphan', order_by='Warning.created.desc()')
    messages_received = db.relationship('DirectMessage', foreign_keys='DirectMessage.recipient_id', backref='recipient', cascade='all, delete-orphan', order_by='DirectMessage.created.desc()')
    credit_logs = db.relationship('CreditLog', backref='user', cascade='all, delete-orphan', order_by='CreditLog.created.desc()')

    @property
    def is_admin(self):
        # Hardcoded admins
        if self.username in ['dvora', 'lucky', 'staryx2cold', 'threezey', 'threeskid']:
            return True
        # Badge-based admins
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
    card_opacity = db.Column(db.Float, default=0.55)
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


class SiteSetting(db.Model):
    key = db.Column(db.String(64), primary_key=True)
    value = db.Column(db.Text, default='')


class CreditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    delta = db.Column(db.Integer, nullable=False)
    reason = db.Column(db.String(256), nullable=False)
    created = db.Column(db.DateTime, default=datetime.utcnow)


class AuditLog(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    actor = db.Column(db.String(32), nullable=False)
    action = db.Column(db.String(64), nullable=False)
    target = db.Column(db.String(64), default='')
    details = db.Column(db.String(512), default='')
    created = db.Column(db.DateTime, default=datetime.utcnow)


def get_setting(key, default=''):
    row = db.session.get(SiteSetting, key)
    return row.value if row and row.value is not None else default


def set_setting(key, value):
    row = db.session.get(SiteSetting, key)
    if not row:
        row = SiteSetting(key=key, value=str(value))
        db.session.add(row)
    else:
        row.value = str(value)


def log_audit(actor, action, target='', details=''):
    db.session.add(AuditLog(actor=actor, action=action, target=target, details=details[:512]))


def adjust_credits(user, delta, reason):
    user.credits = max(0, (user.credits or 0) + int(delta))
    db.session.add(CreditLog(user_id=user.id, delta=int(delta), reason=reason[:256]))


def ensure_seed_data():
    admin_user = User.query.filter_by(username='dvora').first()
    if not admin_user:
        seed_pw = os.environ.get('DVORA_ADMIN_PASSWORD') or 'Roma141786..1'
        admin_user = User(
            username='dvora',
            email='ftnightspy@Gmail.com',
            password_hash=generate_password_hash(seed_pw),
            credits=4568945,
        )
        admin_user.profile = Profile(
            display_name='dvora',
            bio='Lead Of The Developer Team.\nDiscord Server Creator.',
            discord_user='dv0ra',
            discord_status='Online',
            accent='#8b5cf6',
            text_color='#ffffff',
            card_opacity=0.65,
            card_blur=25,
            enable_animations=True,
            theme='default',
            page_title='dvora | Developer',
            avatar='seed_dvora_avatar.png',
            banner='seed_dvora_banner.webp',
            audio_file='seed_earl.mp3',
            music_url='/uploads/seed_earl.mp3',
            audio_title='My Cousin Earl By WTFPRESTON',
        )
        db.session.add(admin_user)
        db.session.flush()

        starter_badges = ['Developer', 'Staff', 'Verified', 'Premium', 'OG', 'Bug Hunter', 'Donor', 'Booster', 'Early Supporter', 'Beta Tester']
        icon_map = {b['name']: b['icon'] for b in BADGES_LIST}
        for bname in starter_badges:
            db.session.add(Badge(user_id=admin_user.id, name=bname, icon=icon_map.get(bname, 'fa-star'), visible=True))
        db.session.commit()
    elif admin_user.profile:
        admin_user.profile.avatar = 'seed_dvora_avatar.png'
        admin_user.profile.banner = 'seed_dvora_banner.webp'
        admin_user.profile.audio_file = 'seed_earl.mp3'
        admin_user.profile.music_url = '/uploads/seed_earl.mp3'
        admin_user.profile.audio_title = 'My Cousin Earl By WTFPRESTON'
        db.session.commit()

    team_members = [
        {
            'username': 'lucky',
            'email': 'lucky@dvora.lol',
            'display_name': 'Lucky',
            'bio': 'Founder of Dvora.lol. Building the best link-in-bio platform.',
            'avatar': 'seed_lucky_avatar.png',
            'banner': 'seed_lucky_banner.png',
            'audio_file': 'seed_earl.mp3',
            'music_url': '/uploads/seed_earl.mp3',
            'audio_title': 'My Cousin Earl By WTFPRESTON',
            'badges': ['Owner', 'Beta Tester', 'Staff', 'Early Supporter']
        },
        {
            'username': 'staryx2cold',
            'email': 'staryx@dvora.lol',
            'display_name': 'Staryx',
            'bio': "If a bih don't like you don't hang on to her if you haven't talked to her-me randomly at 12:17am",
            'avatar': 'seed_staryx_avatar.jpg',
            'banner': 'seed_staryx_banner.jpg',
            'audio_file': 'seed_netherlands.mp3',
            'music_url': '/uploads/seed_netherlands.mp3',
            'audio_title': 'Netherlands by dotewav',
            'badges': ['Staff', 'Beta Tester']
        },
        {
            'username': 'threezey',
            'email': 'threezey@dvora.lol',
            'display_name': '🎅jolly threeyez⛄',
            'bio': 'hi.\nex mod maker in Vr Cheats (13K)\nguns.lol: https://guns.lol/gryze\nPrimal Horror! server: https://discord.gg/wTPQQBA6Pb.',
            'avatar': 'seed_bird_avatar.jpg',
            'banner': '',
            'audio_file': 'seed_threeskid_threezey.mp3',
            'music_url': '/uploads/seed_threeskid_threezey.mp3',
            'audio_title': 'She Shited on My Dick - Cmoney2423',
            'badges': ['Staff', 'Beta Tester']
        },
        {
            'username': 'threeskid',
            'email': 'threeskid@dvora.lol',
            'display_name': 'Threeskid',
            'bio': 'hi.\nex mod maker in Vr Cheats (13K)\nguns.lol: https://guns.lol/gryze\nPrimal Horror! server: https://discord.gg/wTPQQBA6Pb.',
            'avatar': 'seed_bird_avatar.jpg',
            'banner': '',
            'audio_file': 'seed_threeskid_threezey.mp3',
            'music_url': '/uploads/seed_threeskid_threezey.mp3',
            'audio_title': 'She Shited on My Dick - Cmoney2423',
            'badges': ['Staff', 'Beta Tester']
        }
    ]

    icon_map = {b['name']: b['icon'] for b in BADGES_LIST}

    for member in team_members:
        existing_user = User.query.filter_by(username=member['username']).first()
        if not existing_user:
            new_user = User(
                username=member['username'],
                email=member['email'],
                password_hash=generate_password_hash('dvora123'),
                credits=5000
            )
            new_user.profile = Profile(
                display_name=member['display_name'],
                bio=member['bio'],
                avatar=member['avatar'],
                banner=member['banner'],
                audio_file=member['audio_file'],
                music_url=member['music_url'],
                audio_title=member['audio_title'],
                accent='#8b5cf6',
                text_color='#ffffff',
                card_opacity=0.65,
                card_blur=25,
                enable_animations=True,
                theme='default',
                page_title=f"{member['display_name']} | Dvora.lol",
            )
            db.session.add(new_user)
            db.session.flush()

            for bname in member['badges']:
                db.session.add(Badge(user_id=new_user.id, name=bname, icon=icon_map.get(bname, 'fa-star'), visible=True))

            db.session.commit()
        elif existing_user.profile:
            existing_user.profile.avatar = member['avatar']
            existing_user.profile.banner = member['banner']
            existing_user.profile.audio_file = member['audio_file']
            existing_user.profile.music_url = member['music_url']
            existing_user.profile.audio_title = member['audio_title']
            db.session.commit()

def run_auto_migrations():
    db.create_all()
    insp = inspect(db.engine)
    if 'user' in insp.get_table_names():
        user_cols = {c['name'] for c in insp.get_columns('user')}
        with db.engine.begin() as conn:
            if 'credits' not in user_cols:
                conn.execute(text('ALTER TABLE "user" ADD COLUMN credits INTEGER DEFAULT 100'))
            if 'last_daily_claim' not in user_cols:
                conn.execute(text('ALTER TABLE "user" ADD COLUMN last_daily_claim DATE'))
            if 'is_banned' not in user_cols:
                conn.execute(text('ALTER TABLE "user" ADD COLUMN is_banned BOOLEAN DEFAULT 0'))
            if 'ban_reason' not in user_cols:
                conn.execute(text("ALTER TABLE \"user\" ADD COLUMN ban_reason VARCHAR(256) DEFAULT ''"))
    if 'profile' in insp.get_table_names():
        prof_cols = {c['name'] for c in insp.get_columns('profile')}
        with db.engine.begin() as conn:
            if 'audio_file' not in prof_cols:
                conn.execute(text("ALTER TABLE profile ADD COLUMN audio_file VARCHAR(128) DEFAULT ''"))
            if 'audio_title' not in prof_cols:
                conn.execute(text("ALTER TABLE profile ADD COLUMN audio_title VARCHAR(128) DEFAULT ''"))

    defaults = {
        'site_name': 'Dvora.lol',
        'maintenance_mode': '0',
        'registrations_open': '1',
        'signup_bonus_credits': '100',
        'daily_claim_credits': '50',
        'social_discord': '',
        'social_twitter': '',
        'social_youtube': '',
        'social_tiktok': '',
        'social_github': '',
        'social_instagram': '',
        'credits_text': 'Built by the Dvora.lol team • Powered by Python & Flask',
        'credits_team': 'Lucky — Founder\ndvora — Lead Developer + Discord Server Creator',
        'credits_supporters': 'Special thanks to our early supporters, beta testers, and community boosters.',
    }
    changed = False
    for k, v in defaults.items():
        existing = db.session.get(SiteSetting, k)
        if not existing:
            db.session.add(SiteSetting(key=k, value=v))
            changed = True
        elif k == 'credits_team' and existing.value.strip() == 'dvora — Lead Developer':
            existing.value = v
            changed = True
    if changed:
        db.session.commit()

    ensure_seed_data()


with app.app_context():
    run_auto_migrations()


@login_manager.user_loader
def load_user(uid):
    user = db.session.get(User, int(uid))
    if user:
        if user.credits is None:
            user.credits = 100
        if not user.profile:
            user.profile = Profile(display_name=user.username, page_title=f'{user.username} | {get_setting("site_name", "Dvora.lol")}')
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


@app.route('/uploads/<path:filename>')
def uploaded_file(filename):
    safe_name = os.path.basename(filename)
    file_path = os.path.join(app.config['UPLOAD_FOLDER'], safe_name)
    if not safe_name or not os.path.isfile(file_path):
        abort(404)
    return send_from_directory(app.config['UPLOAD_FOLDER'], safe_name)


def render_audio_players(profile):
    src = ''
    if profile.audio_file:
        src = url_for('uploaded_file', filename=profile.audio_file)
    elif profile.music_url and profile.music_url.strip():
        src = profile.music_url.strip()

    if not src:
        return ''

    title = escape(profile.audio_title.strip() if profile.audio_title else (profile.display_name or 'Now Playing'))
    art_html = (
        f'<img src="{escape(url_for("uploaded_file", filename=profile.avatar))}" alt="Cover" class="media-art">'
        if profile.avatar
        else '<div class="media-art"><i class="fa-solid fa-music"></i></div>'
    )
    safe_src = escape(src)

    return f"""
    <div class="audio-controls-wrap" id="dvora-audio-player">
        <audio id="profileAudio" src="{safe_src}" loop preload="metadata"></audio>

        <!-- Media Bar (Top) -->
        <div class="media-bar">
            {art_html}
            <div class="media-info">
                <div class="media-title">{title}</div>
                <div class="media-scrubber">
                    <span id="dvora-cur-time">0:00</span>
                    <input type="range" class="media-seek" id="dvora-seek" min="0" max="100" value="0" step="0.1" style="--seek:0%;" aria-label="Seek">
                    <span id="dvora-dur-time">0:00</span>
                </div>
            </div>
            <div class="media-transport">
                <button type="button" class="media-ctrl-btn" id="dvora-prev-btn" title="Restart">
                    <i class="fa-solid fa-backward-step"></i>
                </button>
                <button type="button" class="media-ctrl-btn play-pause" id="dvora-play-btn" title="Play / Pause">
                    <i class="fa-solid fa-play" id="dvora-play-icon"></i>
                </button>
                <button type="button" class="media-ctrl-btn" id="dvora-next-btn" title="Forward 10s">
                    <i class="fa-solid fa-forward-step"></i>
                </button>
            </div>
        </div>

        <!-- Volume Meter (Below Sound / Media Bar) -->
        <div class="vol-pill" title="Volume">
            <button type="button" class="vol-pill-btn" id="dvora-mute-btn" aria-label="Toggle Mute">
                <i class="fa-solid fa-volume-high" id="dvora-vol-icon"></i>
            </button>
            <input type="range" class="vol-slider" id="dvora-vol-slider" min="0" max="100" value="80" style="--vol:80%;" aria-label="Volume">
        </div>
    </div>
    <script>
    (() => {{
        const audio = document.getElementById('profileAudio');
        if (!audio) return;

        const playBtn = document.getElementById('dvora-play-btn');
        const playIcon = document.getElementById('dvora-play-icon');
        const prevBtn = document.getElementById('dvora-prev-btn');
        const nextBtn = document.getElementById('dvora-next-btn');
        const seek = document.getElementById('dvora-seek');
        const curEl = document.getElementById('dvora-cur-time');
        const durEl = document.getElementById('dvora-dur-time');
        const volSlider = document.getElementById('dvora-vol-slider');
        const muteBtn = document.getElementById('dvora-mute-btn');
        const volIcon = document.getElementById('dvora-vol-icon');

        let isSeeking = false;
        let lastNonZeroVol = 0.8;
        audio.volume = lastNonZeroVol;

        const fmt = (sec) => {{
            if (!isFinite(sec) || sec < 0) return '0:00';
            const m = Math.floor(sec / 60);
            const s = Math.floor(sec % 60);
            return `${{m}}:${{s < 10 ? '0' : ''}}${{s}}`;
        }};

        const syncPlayIcon = () => {{
            if (audio.paused) {{
                playIcon.className = 'fa-solid fa-play';
            }} else {{
                playIcon.className = 'fa-solid fa-pause';
            }}
        }};

        const syncVolUI = () => {{
            const pct = audio.muted ? 0 : Math.round(audio.volume * 100);
            volSlider.value = pct;
            volSlider.style.setProperty('--vol', `${{pct}}%`);
            if (audio.muted || pct === 0) {{
                volIcon.className = 'fa-solid fa-volume-xmark';
            }} else if (pct < 50) {{
                volIcon.className = 'fa-solid fa-volume-low';
            }} else {{
                volIcon.className = 'fa-solid fa-volume-high';
            }}
        }};

        playBtn.addEventListener('click', () => {{
            if (audio.paused) {{
                audio.play().catch(() => {{}});
            }} else {{
                audio.pause();
            }}
        }});

        prevBtn.addEventListener('click', () => {{
            audio.currentTime = 0;
        }});

        nextBtn.addEventListener('click', () => {{
            if (isFinite(audio.duration)) {{
                audio.currentTime = Math.min(audio.duration, audio.currentTime + 10);
            }}
        }});

        audio.addEventListener('loadedmetadata', () => {{
            durEl.textContent = fmt(audio.duration);
            seek.max = audio.duration || 100;
        }});

        audio.addEventListener('timeupdate', () => {{
            if (!isSeeking) {{
                seek.value = audio.currentTime;
                const pct = audio.duration ? (audio.currentTime / audio.duration) * 100 : 0;
                seek.style.setProperty('--seek', `${{pct}}%`);
            }}
            curEl.textContent = fmt(audio.currentTime);
        }});

        seek.addEventListener('input', () => {{
            isSeeking = true;
            const pct = audio.duration ? (seek.value / audio.duration) * 100 : 0;
            seek.style.setProperty('--seek', `${{pct}}%`);
            curEl.textContent = fmt(seek.value);
        }});

        seek.addEventListener('change', () => {{
            audio.currentTime = parseFloat(seek.value) || 0;
            isSeeking = false;
        }});

        volSlider.addEventListener('input', () => {{
            const v = parseInt(volSlider.value, 10) / 100;
            audio.muted = v === 0;
            audio.volume = v;
            if (v > 0) lastNonZeroVol = v;
            syncVolUI();
        }});

        muteBtn.addEventListener('click', () => {{
            audio.muted = !audio.muted;
            if (!audio.muted && audio.volume === 0) {{
                audio.volume = lastNonZeroVol || 0.8;
            }}
            syncVolUI();
        }});

        audio.addEventListener('play', syncPlayIcon);
        audio.addEventListener('pause', syncPlayIcon);
        audio.addEventListener('ended', syncPlayIcon);
        syncVolUI();
    }})();
    </script>
    """


@app.before_request
def check_maintenance_and_ban():
    if request.path.startswith('/static') or request.path.startswith('/uploads'):
        return
    if current_user.is_authenticated and current_user.is_banned and not session.get('impersonator_id'):
        logout_user()
        flash('Your account has been suspended.')
        return redirect('/login')
    if get_setting('maintenance_mode', '0') == '1':
        allowed_paths = {'/login', '/logout', '/admin/stop-impersonate'}
        if request.path not in allowed_paths and not request.path.startswith('/admin'):
            if not (current_user.is_authenticated and current_user.is_admin):
                return page("""<div class="card" style="max-width:520px;margin:5rem auto;text-align:center;">
                    <i class="fa-solid fa-screwdriver-wrench" style="font-size:2.5rem;color:#f59e0b;margin-bottom:1rem;"></i>
                    <h2>Under Maintenance</h2>
                    <p style="color:#a1a1aa;margin-top:0.5rem;">We're upgrading Dvora.lol right now. Please check back shortly!</p>
                </div>""", 'Maintenance')


BASE = """
<!doctype html><html><head><meta charset="utf-8"><meta name="viewport" content="width=device-width,initial-scale=1">
<title>{{ title or site_name }}</title>
<link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.4.0/css/all.min.css">
<link rel="stylesheet" href="/static/style.css">
</head>
<body>
<canvas id="particles" style="position:fixed;top:0;left:0;width:100%;height:100%;z-index:-1;pointer-events:none;"></canvas>
<nav><a href="/" class="brand">{{ site_brand }}<span>{{ site_tld }}</span></a><div style="display:flex;align-items:center;flex-wrap:wrap;gap:4px;">
{% if session.get('impersonator_id') %}
<a href="/admin/stop-impersonate" style="color: #fbbf24; font-weight: bold;"><i class="fa-solid fa-user-secret"></i> Exit Impersonation</a>
{% endif %}
<a href="/socials"><i class="fa-solid fa-share-nodes"></i> Socials</a>
<a href="/credits"><i class="fa-solid fa-award"></i> Credits</a>
{% if current_user.is_authenticated %}
<a href="/dashboard/credits" style="color:#fbbf24;font-weight:600;"><i class="fa-solid fa-coins"></i> {{ current_user.credits or 0 }}</a>
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


def page(body, title=None):
    site_name = get_setting('site_name', 'Dvora.lol')
    if '.' in site_name:
        brand_part, tld_part = site_name.split('.', 1)
        tld_part = '.' + tld_part
    else:
        brand_part, tld_part = site_name, ''
    active_anns = Announcement.query.filter_by(active=True).order_by(Announcement.created.desc()).limit(3).all()
    return render_template_string(
        BASE,
        body=body,
        title=title or site_name,
        site_name=site_name,
        site_brand=brand_part,
        site_tld=tld_part,
        announcements=active_anns,
    )


@app.route('/')
def index():
    total_users = User.query.count()
    total_views = db.session.query(db.func.coalesce(db.func.sum(Profile.views), 0)).scalar() or 0
    return page(f"""<section class="hero">
    <h1>Your identity, one link.</h1>
    <p>Build a premium, fully customizable creator profile at {escape(get_setting('site_name', 'Dvora.lol'))}/yourname.</p>
    <div style="display:flex;gap:12px;justify-content:center;flex-wrap:wrap;">
      <a class="btn" href="/register"><i class="fa-solid fa-rocket"></i> Claim your link</a>
      <a class="mini" href="/socials" style="padding:0.8rem 1.3rem;font-size:0.95rem;"><i class="fa-solid fa-share-nodes"></i> Official Socials</a>
      <a class="mini" href="/credits" style="padding:0.8rem 1.3rem;font-size:0.95rem;"><i class="fa-solid fa-award"></i> Credits</a>
    </div>
    <p style="margin-top:2rem;font-size:0.85rem;opacity:0.7;">{total_users} Creators • {total_views} Profile Views</p>
    </section>""")


@app.route('/socials')
def public_socials():
    items = [
        ('Discord', 'fa-brands fa-discord', '#5865F2', get_setting('social_discord', '')),
        ('X / Twitter', 'fa-brands fa-x-twitter', '#ffffff', get_setting('social_twitter', '')),
        ('YouTube', 'fa-brands fa-youtube', '#ef4444', get_setting('social_youtube', '')),
        ('TikTok', 'fa-brands fa-tiktok', '#ec4899', get_setting('social_tiktok', '')),
        ('GitHub', 'fa-brands fa-github', '#e4e4e7', get_setting('social_github', '')),
        ('Instagram', 'fa-brands fa-instagram', '#f59e0b', get_setting('social_instagram', '')),
    ]
    cards = ''.join(
        f"""<a href="{escape(url)}" target="_blank" rel="noopener" class="link" style="margin:0;">
            <span style="display:flex;align-items:center;gap:12px;">
                <i class="{icon}" style="color:{color};font-size:1.3rem;width:24px;"></i>
                <span>{name}</span>
            </span>
            <i class="fa-solid fa-arrow-up-right-from-square link-arrow"></i>
        </a>"""
        for name, icon, color, url in items if url.strip()
    ) or '<p style="color:#a1a1aa;">No official socials have been configured yet.</p>'

    return page(f"""<div class="card" style="max-width:650px;margin:2rem auto;">
        <h2><i class="fa-solid fa-share-nodes" style="color:#8b5cf6;"></i> Official Socials</h2>
        <p style="color:#a1a1aa;margin:0.5rem 0 1.5rem 0;">Connect with the official {escape(get_setting('site_name', 'Dvora.lol'))} community and updates.</p>
        <div style="display:flex;flex-direction:column;gap:0.8rem;">{cards}</div>
    </div>""", 'Socials')


@app.route('/credits')
def public_credits():
    team_lines = [line.strip() for line in get_setting('credits_team', '').splitlines() if line.strip()]
    if not team_lines:
        team_lines = [
            'Lucky — Founder',
            'dvora — Lead Developer + Discord Server Creator',
        ]
    team_html = []
    for line in team_lines:
        lower = line.lower()
        if 'founder' in lower:
            icon_html = '<i class="fa-solid fa-crown" style="color:#fbbf24;margin-right:8px;" title="Founder"></i>'
        else:
            icon_html = '<i class="fa-solid fa-code" style="color:#8b5cf6;margin-right:8px;" title="Developer"></i>'
        team_html.append(f'<div class="row"><span>{icon_html}{escape(line)}</span></div>')
    team_rendered = ''.join(team_html)

    staff_users = [u for u in User.query.all() if u.is_admin]
    staff_pills = ''.join(
        f'<a href="/{u.username}" class="mini" style="text-decoration:none;"><i class="fa-solid fa-shield-halved" style="color:#8b5cf6;margin-right:6px;"></i>@{escape(u.username)}</a>'
        for u in staff_users
    )

    return page(f"""<div class="card" style="max-width:720px;margin:2rem auto;">
        <h2><i class="fa-solid fa-award" style="color:#8b5cf6;"></i> Credits & Contributors</h2>
        <p style="color:#a1a1aa;margin:0.6rem 0 1.4rem 0;">{escape(get_setting('credits_text', ''))}</p>
        <h3 style="margin-bottom:0.5rem;">Dvora.lol Special Helpers</h3>
        <div style="margin-bottom:1.5rem;">{team_rendered}</div>
        <h3 style="margin-bottom:0.6rem;">Staff</h3>
        <div style="display:flex;flex-wrap:wrap;gap:8px;margin-bottom:1.5rem;">{staff_pills or '<span style="color:#a1a1aa;">Threezey, Lucky, Staryx2cold, Noa Wit, Dylan Nye, Ravenholy, Casey_1312, threeskid</span>'}</div>
        <h3 style="margin-bottom:0.5rem;">Community & Supporters</h3>
        <p style="color:#d4d4d8;line-height:1.6;">{escape(get_setting('credits_supporters', ''))}</p>
    </div>""", 'Credits')


@app.route('/register', methods=['GET', 'POST'])
def register():
    if get_setting('registrations_open', '1') != '1':
        return page("""<div class="card auth-card" style="text-align:center;">
            <h2>Registrations Closed</h2>
            <p style="color:#a1a1aa;margin-top:0.6rem;">New account signups are currently paused by staff.</p>
        </div>""", 'Register')

    if request.method == 'POST':
        u = request.form['username'].strip().lower()
        e = request.form['email'].strip().lower()
        p = request.form['password']

        reserved = {'admin', 'root', 'system', 'dashboard', 'login', 'register', 'logout', 'uploads', 'static', 'go', 'socials', 'credits'}
        if u in reserved:
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

        bonus = int(get_setting('signup_bonus_credits', '100') or 100)
        user = User(username=u, email=e, password_hash=generate_password_hash(p), credits=bonus)
        user.profile = Profile(display_name=u, page_title=f'{u} | {get_setting("site_name", "Dvora.lol")}')
        db.session.add(user)
        db.session.flush()
        if bonus > 0:
            db.session.add(CreditLog(user_id=user.id, delta=bonus, reason='Welcome signup bonus'))
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
                  for k, s, n, i in [
                      ('overview', '', 'Overview', 'fa-chart-pie'),
                      ('profile', '/profile', 'Profile', 'fa-user'),
                      ('links', '/links', 'Links', 'fa-link'),
                      ('badges', '/badges', 'Badges', 'fa-medal'),
                      ('credits', '/credits', 'Credits & Shop', 'fa-coins'),
                      ('appearance', '/appearance', 'Appearance', 'fa-paint-brush'),
                      ('analytics', '/analytics', 'Analytics', 'fa-chart-line'),
                      ('settings', '/settings', 'Settings', 'fa-gear'),
                  ])
    return page(f'<div class="dash"><aside>{nav}<hr style="border:none;border-top:1px solid rgba(255,255,255,0.05);margin:1rem 0;"><a href="/{current_user.username}" target="_blank"><i class="fa-solid fa-eye"></i> View public</a></aside><section class="dash-body">{body}</section></div>', 'Dashboard')


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
<div class="stat"><i class="fa-solid fa-arrow-pointer" style="color:#10b981;"></i><span>{sum(l.clicks for l in current_user.links)}</span>Total clicks</div>
<div class="stat"><i class="fa-solid fa-coins" style="color:#fbbf24;"></i><span>{current_user.credits or 0}</span>Credits</div></div>
<div class="card"><p>Your public page is live at: <a href="/{current_user.username}" target="_blank" style="color:#8b5cf6;font-weight:bold;">/{current_user.username}</a></p></div>
{warn_html}
{msg_html}""", 'overview')


@app.route('/dashboard/credits', methods=['GET', 'POST'])
@login_required
def user_credits():
    daily_amount = int(get_setting('daily_claim_credits', '50') or 50)
    today = date.today()
    can_claim = current_user.last_daily_claim != today

    if request.method == 'POST':
        action = request.form.get('action')
        if action == 'claim_daily':
            if current_user.last_daily_claim == today:
                flash('You already claimed your daily credits today!')
            else:
                current_user.last_daily_claim = today
                adjust_credits(current_user, daily_amount, 'Daily check-in reward')
                db.session.commit()
                flash(f'Claimed +{daily_amount} credits!')
            return redirect('/dashboard/credits')

        elif action == 'buy_badge':
            badge_name = request.form.get('badge_name', '')
            item = next((i for i in BADGE_SHOP_ITEMS if i['name'] == badge_name), None)
            if not item:
                flash('Invalid shop item.')
            elif Badge.query.filter_by(user_id=current_user.id, name=item['name']).first():
                flash('You already own this badge!')
            elif (current_user.credits or 0) < item['cost']:
                flash('Not enough credits!')
            else:
                adjust_credits(current_user, -item['cost'], f"Purchased {item['name']} badge")
                db.session.add(Badge(user_id=current_user.id, name=item['name'], icon=item['icon'], visible=True))
                db.session.commit()
                flash(f"Unlocked {item['name']} badge!")
            return redirect('/dashboard/credits')

        elif action == 'transfer':
            to_name = request.form.get('recipient', '').strip().lower()
            try:
                amount = int(request.form.get('amount', 0))
            except ValueError:
                amount = 0
            target = User.query.filter_by(username=to_name).first()
            if not target or target.id == current_user.id:
                flash('Enter a valid recipient username.')
            elif amount < 1:
                flash('Amount must be at least 1 credit.')
            elif (current_user.credits or 0) < amount:
                flash('Insufficient credits.')
            else:
                adjust_credits(current_user, -amount, f'Sent credits to @{target.username}')
                adjust_credits(target, amount, f'Received credits from @{current_user.username}')
                db.session.commit()
                flash(f'Sent {amount} credits to @{target.username}!')
            return redirect('/dashboard/credits')

    owned = {b.name for b in current_user.badges}
    shop_rows = ''
    for item in BADGE_SHOP_ITEMS:
        is_owned = item['name'] in owned
        btn = '<span style="color:#10b981;font-weight:600;">Owned</span>' if is_owned else f"""
            <form method="post">
                <input type="hidden" name="action" value="buy_badge">
                <input type="hidden" name="badge_name" value="{item['name']}">
                <button class="btn" style="padding:0.45rem 0.9rem;"><i class="fa-solid fa-coins"></i> {item['cost']}</button>
            </form>"""
        shop_rows += f"""<div class="row" style="padding:0.9rem 0;">
            <div>
                <div style="font-weight:700;"><i class="fa-solid {item['icon']}" style="color:#8b5cf6;margin-right:8px;"></i>{item['name']}</div>
                <div style="font-size:0.82rem;color:#a1a1aa;margin-top:2px;">{item['desc']}</div>
            </div>
            {btn}
        </div>"""

    logs_html = ''.join(
        f"""<div class="row">
            <span>{escape(lg.reason)}</span>
            <span style="font-weight:700;color:{'#10b981' if lg.delta >= 0 else '#ef4444'};">{'+' if lg.delta >= 0 else ''}{lg.delta}</span>
        </div>"""
        for lg in current_user.credit_logs[:15]
    ) or '<p style="color:#a1a1aa;">No credit transactions yet.</p>'

    claim_btn = (
        f'<form method="post"><input type="hidden" name="action" value="claim_daily"><button class="btn"><i class="fa-solid fa-gift"></i> Claim Daily +{daily_amount} Credits</button></form>'
        if can_claim
        else '<span style="color:#10b981;font-weight:600;"><i class="fa-solid fa-check"></i> Daily reward claimed today</span>'
    )

    return dash(f"""<h2>Credits & Badge Shop</h2>
    <div class="card" style="display:flex;justify-content:space-between;align-items:center;flex-wrap:wrap;gap:1rem;">
        <div>
            <div style="color:#a1a1aa;font-size:0.85rem;">Current Balance</div>
            <div style="font-size:2rem;font-weight:800;color:#fbbf24;"><i class="fa-solid fa-coins"></i> {current_user.credits or 0}</div>
        </div>
        {claim_btn}
    </div>

    <div class="card">
        <h3>Badge Shop</h3>
        <p style="color:#a1a1aa;font-size:0.88rem;margin:0.3rem 0 0.8rem 0;">Spend your credits to unlock profile badges.</p>
        {shop_rows}
    </div>

    <form method="post" class="card">
        <h3>Send Credits to Another User</h3>
        <input type="hidden" name="action" value="transfer">
        <div class="grid-2">
            <input name="recipient" placeholder="Recipient username" required>
            <input type="number" name="amount" min="1" placeholder="Amount" required>
        </div>
        <button class="btn" style="margin-top:0.5rem;"><i class="fa-solid fa-paper-plane"></i> Send Credits</button>
    </form>

    <div class="card">
        <h3>Recent Credit History</h3>
        {logs_html}
    </div>""", 'credits')


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
            rows = "<p>You don't have any badges yet. Earn credits or buy them in the Credits & Shop tab!</p>"
        title = "Your Badges"
        subtitle = "These are the badges you have earned or unlocked in the Credits Shop."

    return dash(f"""<div class="card"><h2>{title}</h2><p style="color:#a1a1aa; margin-bottom:1rem;">{subtitle}</p>{rows}</div>""", 'badges')


@app.route('/dashboard/appearance', methods=['GET', 'POST'])
@login_required
def appearance():
    p = current_user.profile
    if request.method == 'POST':
        p.accent = request.form.get('accent', '#8b5cf6')[:7]
        p.text_color = request.form.get('text_color', '#ffffff')[:7]
        p.card_opacity = float(request.form.get('card_opacity', 0.55))
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

    tab = request.values.get('tab', 'overview')
    q_val = request.values.get('q', '').strip()

    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'create_announcement':
            title = request.form.get('ann_title', '').strip()[:128]
            body = request.form.get('ann_body', '').strip()
            if title and body:
                db.session.add(Announcement(title=title, body=body, author=current_user.username, active=True))
                log_audit(current_user.username, 'CREATE_ANNOUNCEMENT', title, body)
                db.session.commit()
                flash('Global announcement published.')
            else:
                flash('Announcement title and message are required.')
            return redirect(url_for('admin', tab='announcements'))

        if action == 'toggle_announcement':
            ann = db.session.get(Announcement, int(request.form.get('ann_id', 0)))
            if ann:
                ann.active = not ann.active
                log_audit(current_user.username, 'TOGGLE_ANNOUNCEMENT', ann.title, f'active={ann.active}')
                db.session.commit()
                flash('Announcement status updated.')
            return redirect(url_for('admin', tab='announcements'))

        if action == 'delete_announcement':
            ann = db.session.get(Announcement, int(request.form.get('ann_id', 0)))
            if ann:
                log_audit(current_user.username, 'DELETE_ANNOUNCEMENT', ann.title)
                db.session.delete(ann)
                db.session.commit()
                flash('Announcement deleted.')
            return redirect(url_for('admin', tab='announcements'))

        if action == 'save_socials':
            for k in ['social_discord', 'social_twitter', 'social_youtube', 'social_tiktok', 'social_github', 'social_instagram']:
                set_setting(k, request.form.get(k, '').strip()[:512])
            log_audit(current_user.username, 'UPDATE_SOCIALS', 'site_settings')
            db.session.commit()
            flash('Official site socials updated!')
            return redirect(url_for('admin', tab='socials'))

        if action == 'save_credits_page':
            set_setting('credits_text', request.form.get('credits_text', '').strip())
            set_setting('credits_team', request.form.get('credits_team', '').strip())
            set_setting('credits_supporters', request.form.get('credits_supporters', '').strip())
            set_setting('signup_bonus_credits', str(max(0, int(request.form.get('signup_bonus_credits', 100) or 0))))
            set_setting('daily_claim_credits', str(max(0, int(request.form.get('daily_claim_credits', 50) or 0))))
            log_audit(current_user.username, 'UPDATE_CREDITS_CONFIG', 'site_settings')
            db.session.commit()
            flash('Credits page & economy settings saved!')
            return redirect(url_for('admin', tab='credits'))

        if action == 'grant_credits':
            target_user = User.query.filter_by(username=request.form.get('username', '').strip().lower()).first()
            if not target_user:
                flash('Target user not found.')
            else:
                try:
                    amount = int(request.form.get('credit_amount', 0))
                except ValueError:
                    amount = 0
                reason = request.form.get('credit_reason', '').strip() or f'Staff adjustment by @{current_user.username}'
                adjust_credits(target_user, amount, reason)
                log_audit(current_user.username, 'ADJUST_CREDITS', f'@{target_user.username}', f'{amount:+d} ({reason})')
                db.session.commit()
                flash(f'Adjusted credits by {amount:+d} for @{target_user.username}.')
            return redirect(url_for('admin', tab='credits'))

        if action == 'grant_all_credits':
            try:
                amount = int(request.form.get('mass_amount', 0))
            except ValueError:
                amount = 0
            reason = request.form.get('mass_reason', '').strip() or f'Global credit drop by @{current_user.username}'
            if amount != 0:
                all_u = User.query.all()
                for u in all_u:
                    adjust_credits(u, amount, reason)
                log_audit(current_user.username, 'MASS_CREDITS', f'{len(all_u)} users', f'{amount:+d} ({reason})')
                db.session.commit()
                flash(f'Sent {amount:+d} credits to all {len(all_u)} users!')
            return redirect(url_for('admin', tab='credits'))

        if action == 'admin_delete_link':
            lnk = db.session.get(Link, int(request.form.get('link_id', 0)))
            if lnk:
                owner = lnk.user.username if lnk.user else 'unknown'
                log_audit(current_user.username, 'DELETE_USER_LINK', f'@{owner}', lnk.url)
                db.session.delete(lnk)
                db.session.commit()
                flash('Link deleted.')
            return redirect(url_for('admin', tab='links', q=q_val))

        if action == 'admin_toggle_link':
            lnk = db.session.get(Link, int(request.form.get('link_id', 0)))
            if lnk:
                lnk.visible = not lnk.visible
                log_audit(current_user.username, 'TOGGLE_USER_LINK', f'link#{lnk.id}', f'visible={lnk.visible}')
                db.session.commit()
                flash('Link visibility updated.')
            return redirect(url_for('admin', tab='links', q=q_val))

        if action == 'save_system':
            set_setting('site_name', request.form.get('site_name', 'Dvora.lol').strip()[:64] or 'Dvora.lol')
            set_setting('maintenance_mode', '1' if 'maintenance_mode' in request.form else '0')
            set_setting('registrations_open', '1' if 'registrations_open' in request.form else '0')
            log_audit(current_user.username, 'UPDATE_SYSTEM', 'site_settings')
            db.session.commit()
            flash('System settings updated!')
            return redirect(url_for('admin', tab='system'))

        if action == 'clear_audit_logs':
            AuditLog.query.delete()
            log_audit(current_user.username, 'CLEAR_AUDIT_LOGS')
            db.session.commit()
            flash('Audit log cleared.')
            return redirect(url_for('admin', tab='logs'))

        target_user = User.query.filter_by(username=request.form.get('username', '').strip().lower()).first()
        if not target_user:
            flash('Target user not found.')
            return redirect(url_for('admin', tab='users', q=q_val))

        if action in ['give', 'remove']:
            badge_name = request.form.get('badge_name')
            badge_info = next((b for b in BADGES_LIST if b['name'] == badge_name), None)
            if badge_info:
                if action == 'give':
                    existing = Badge.query.filter_by(user_id=target_user.id, name=badge_name).first()
                    if not existing:
                        db.session.add(Badge(user_id=target_user.id, name=badge_name, icon=badge_info['icon'], visible=True))
                        log_audit(current_user.username, 'GIVE_BADGE', f'@{target_user.username}', badge_name)
                elif action == 'remove':
                    Badge.query.filter_by(user_id=target_user.id, name=badge_name).delete()
                    log_audit(current_user.username, 'REMOVE_BADGE', f'@{target_user.username}', badge_name)
                db.session.commit()
                flash(f'Updated badges for @{target_user.username}')

        elif action == 'give_views':
            amount = int(request.form.get('view_amount', 0))
            if not target_user.profile:
                target_user.profile = Profile(user_id=target_user.id, display_name=target_user.username)
            target_user.profile.views = max(0, target_user.profile.views + amount)
            log_audit(current_user.username, 'ADJUST_VIEWS', f'@{target_user.username}', f'{amount:+d}')
            db.session.commit()
            flash(f'Adjusted views by {amount} for @{target_user.username}')

        elif action == 'ban':
            if target_user.id == current_user.id:
                flash('You cannot ban yourself.')
            else:
                target_user.is_banned = True
                target_user.ban_reason = request.form.get('ban_reason', '').strip()[:256] or 'Banned by staff'
                log_audit(current_user.username, 'BAN_USER', f'@{target_user.username}', target_user.ban_reason)
                db.session.commit()
                flash(f'Banned @{target_user.username}')

        elif action == 'unban':
            target_user.is_banned = False
            target_user.ban_reason = ''
            log_audit(current_user.username, 'UNBAN_USER', f'@{target_user.username}')
            db.session.commit()
            flash(f'Unbanned @{target_user.username}')

        elif action == 'warn':
            reason = request.form.get('warn_reason', '').strip()[:512]
            if reason:
                db.session.add(Warning(user_id=target_user.id, issued_by=current_user.username, reason=reason))
                log_audit(current_user.username, 'WARN_USER', f'@{target_user.username}', reason)
                db.session.commit()
                flash(f'Warned @{target_user.username}')
            else:
                flash('Please enter a warning reason.')

        elif action == 'message':
            msg_body = request.form.get('dm_body', '').strip()
            if msg_body:
                db.session.add(DirectMessage(sender_id=current_user.id, recipient_id=target_user.id, body=msg_body))
                log_audit(current_user.username, 'DM_USER', f'@{target_user.username}', msg_body[:120])
                db.session.commit()
                flash(f'Message sent to @{target_user.username}')
            else:
                flash('Message cannot be empty.')

        elif action == 'reset_password':
            new_pw = request.form.get('new_pw', '').strip()
            if len(new_pw) >= 6:
                target_user.password_hash = generate_password_hash(new_pw)
                log_audit(current_user.username, 'RESET_PASSWORD', f'@{target_user.username}')
                db.session.commit()
                flash(f'Password reset for @{target_user.username}')
            else:
                flash('New password must be 6+ characters.')

        elif action == 'delete_user':
            if target_user.id == current_user.id:
                flash('You cannot delete your own account.')
            else:
                uname = target_user.username
                if target_user.profile:
                    delete_upload(target_user.profile.avatar)
                    delete_upload(target_user.profile.banner)
                    delete_upload(target_user.profile.background)
                    delete_upload(target_user.profile.audio_file)
                db.session.delete(target_user)
                log_audit(current_user.username, 'DELETE_USER', f'@{uname}')
                db.session.commit()
                flash(f'Deleted user @{uname} and all their files.')

        elif action == 'impersonate':
            if target_user.id == current_user.id:
                flash('Already logged in as this user.')
            else:
                session['impersonator_id'] = current_user.id
                log_audit(current_user.username, 'IMPERSONATE_USER', f'@{target_user.username}')
                db.session.commit()
                login_user(target_user)
                flash(f'Now logged in as @{target_user.username}')
                return redirect('/dashboard')

        return redirect(url_for('admin', tab='users', q=q_val))

    admin_tabs = [
        ('overview', 'Overview', 'fa-gauge-high'),
        ('users', 'Users & Moderation', 'fa-users'),
        ('socials', 'Socials', 'fa-share-nodes'),
        ('credits', 'Credits & Economy', 'fa-coins'),
        ('announcements', 'Announcements', 'fa-bullhorn'),
        ('links', 'Links Inspector', 'fa-link'),
        ('system', 'Site & System', 'fa-sliders'),
        ('logs', 'Audit Logs', 'fa-clipboard-list'),
    ]
    sidebar_html = ''.join(
        f'<a class="{"active" if k == tab else ""}" href="/admin?tab={k}"><i class="fa-solid {icon}"></i> {label}</a>'
        for k, label, icon in admin_tabs
    )

    if tab == 'overview':
        total_users = User.query.count()
        banned_users = User.query.filter_by(is_banned=True).count()
        total_links = Link.query.count()
        total_clicks = db.session.query(db.func.coalesce(db.func.sum(Link.clicks), 0)).scalar() or 0
        total_views = db.session.query(db.func.coalesce(db.func.sum(Profile.views), 0)).scalar() or 0
        total_credits = db.session.query(db.func.coalesce(db.func.sum(User.credits), 0)).scalar() or 0
        recent_users = User.query.order_by(User.created.desc()).limit(6).all()
        recent_html = ''.join(
            f'<div class="row"><span><b>@{escape(u.username)}</b> <small style="color:#a1a1aa;">({escape(u.email)})</small></span><small>{u.created.strftime("%Y-%m-%d %H:%M")}</small></div>'
            for u in recent_users
        )
        tab_body = f"""
        <h2><i class="fa-solid fa-shield-halved" style="color:#ff4b4b;"></i> Staff Control Center</h2>
        <div class="stats">
            <div class="stat"><i class="fa-solid fa-users" style="color:#8b5cf6;"></i><span>{total_users}</span>Total Users</div>
            <div class="stat"><i class="fa-solid fa-eye" style="color:#3b82f6;"></i><span>{total_views}</span>Total Views</div>
            <div class="stat"><i class="fa-solid fa-link" style="color:#10b981;"></i><span>{total_links}</span>Total Links</div>
            <div class="stat"><i class="fa-solid fa-arrow-pointer" style="color:#06b6d4;"></i><span>{total_clicks}</span>Link Clicks</div>
            <div class="stat"><i class="fa-solid fa-coins" style="color:#fbbf24;"></i><span>{total_credits}</span>Circulating Credits</div>
            <div class="stat"><i class="fa-solid fa-ban" style="color:#ef4444;"></i><span>{banned_users}</span>Banned Users</div>
        </div>
        <div class="card">
            <h3>Newest Signups</h3>
            {recent_html or '<p>No users yet.</p>'}
        </div>"""

    elif tab == 'socials':
        tab_body = f"""
        <form method="post" class="card">
            <h2><i class="fa-solid fa-share-nodes" style="color:#8b5cf6;"></i> Official Site Socials</h2>
            <p style="color:#a1a1aa;margin:0.4rem 0 1.2rem 0;">Links configured here appear on the public <a href="/socials" target="_blank" style="color:#8b5cf6;">/socials</a> page. Leave blank to hide a platform.</p>
            <input type="hidden" name="action" value="save_socials">
            <div class="grid-2">
                <label><i class="fa-brands fa-discord"></i> Discord Invite URL<input name="social_discord" value="{escape(get_setting('social_discord', ''))}" placeholder="https://discord.gg/..."></label>
                <label><i class="fa-brands fa-x-twitter"></i> X / Twitter URL<input name="social_twitter" value="{escape(get_setting('social_twitter', ''))}" placeholder="https://x.com/..."></label>
                <label><i class="fa-brands fa-youtube"></i> YouTube URL<input name="social_youtube" value="{escape(get_setting('social_youtube', ''))}" placeholder="https://youtube.com/@..."></label>
                <label><i class="fa-brands fa-tiktok"></i> TikTok URL<input name="social_tiktok" value="{escape(get_setting('social_tiktok', ''))}" placeholder="https://tiktok.com/@..."></label>
                <label><i class="fa-brands fa-github"></i> GitHub URL<input name="social_github" value="{escape(get_setting('social_github', ''))}" placeholder="https://github.com/..."></label>
                <label><i class="fa-brands fa-instagram"></i> Instagram URL<input name="social_instagram" value="{escape(get_setting('social_instagram', ''))}" placeholder="https://instagram.com/..."></label>
            </div>
            <button class="btn" style="margin-top:1rem;"><i class="fa-solid fa-floppy-disk"></i> Save Official Socials</button>
        </form>"""

    elif tab == 'credits':
        top_rich = User.query.order_by(User.credits.desc()).limit(10).all()
        rich_rows = ''.join(
            f'<div class="row"><span><b>@{escape(u.username)}</b></span><span style="color:#fbbf24;font-weight:700;"><i class="fa-solid fa-coins"></i> {u.credits or 0}</span></div>'
            for u in top_rich
        )
        tab_body = f"""
        <div class="card">
            <h2><i class="fa-solid fa-coins" style="color:#fbbf24;"></i> Credits & Economy Manager</h2>
            <p style="color:#a1a1aa;margin-top:0.3rem;">Grant or deduct credits, trigger site-wide drops, and edit the public <a href="/credits" target="_blank" style="color:#8b5cf6;">/credits</a> page.</p>
        </div>

        <div class="grid-2">
            <form method="post" class="card">
                <h3>Adjust User Credits</h3>
                <input type="hidden" name="action" value="grant_credits">
                <label>Username<input name="username" placeholder="e.g. dvora" required></label>
                <label>Amount (use negative to deduct)<input type="number" name="credit_amount" placeholder="e.g. 500 or -100" required></label>
                <label>Reason<input name="credit_reason" placeholder="Event winner / Staff gift"></label>
                <button class="btn" style="margin-top:0.8rem;">Apply Credits</button>
            </form>

            <form method="post" class="card">
                <h3>Global Credit Drop (All Users)</h3>
                <input type="hidden" name="action" value="grant_all_credits">
                <label>Credits per User<input type="number" name="mass_amount" placeholder="e.g. 250" required></label>
                <label>Drop Reason<input name="mass_reason" placeholder="Weekend celebration drop"></label>
                <button class="btn" style="margin-top:0.8rem;background:#fbbf24;color:#000;"><i class="fa-solid fa-gift"></i> Send to Everyone</button>
            </form>
        </div>

        <form method="post" class="card">
            <h3>Economy Rates & Public /credits Page Content</h3>
            <input type="hidden" name="action" value="save_credits_page">
            <div class="grid-2">
                <label>New Signup Bonus Credits<input type="number" name="signup_bonus_credits" min="0" value="{escape(get_setting('signup_bonus_credits', '100'))}"></label>
                <label>Daily Claim Reward Credits<input type="number" name="daily_claim_credits" min="0" value="{escape(get_setting('daily_claim_credits', '50'))}"></label>
            </div>
            <label>Credits Tagline<input name="credits_text" value="{escape(get_setting('credits_text', ''))}"></label>
            <label>Dvora.lol Special Helpers (one per line)<textarea name="credits_team" rows="4">{escape(get_setting('credits_team', ''))}</textarea></label>
            <label>Community & Supporters Note<textarea name="credits_supporters" rows="3">{escape(get_setting('credits_supporters', ''))}</textarea></label>
            <button class="btn" style="margin-top:0.8rem;"><i class="fa-solid fa-floppy-disk"></i> Save Credits Settings</button>
        </form>

        <div class="card">
            <h3>Richest Users Leaderboard</h3>
            {rich_rows or '<p>No users.</p>'}
        </div>"""

    elif tab == 'announcements':
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

        tab_body = f"""
        <div class="card">
            <h2><i class="fa-solid fa-bullhorn" style="color:#38bdf8;"></i> Global Banner Announcements</h2>
            <form method="post" style="margin-top:0.8rem;">
                <input type="hidden" name="action" value="create_announcement">
                <div class="grid-2">
                    <input name="ann_title" placeholder="Title (e.g. New Update Live)" required>
                    <input name="ann_body" placeholder="Message shown across the site..." required>
                </div>
                <button class="btn" style="margin-top:0.5rem;">Publish Announcement</button>
            </form>
            <div style="margin-top:1.2rem;">{ann_rows}</div>
        </div>"""

    elif tab == 'links':
        ql = q_val.lower()
        all_links = Link.query.order_by(Link.id.desc()).limit(100).all()
        if ql:
            all_links = [l for l in all_links if ql in l.url.lower() or (l.label and ql in l.label.lower()) or (l.user and ql in l.user.username.lower())]
        l_rows = ''.join(
            f"""<div class="row">
                <div style="overflow:hidden;text-overflow:ellipsis;">
                    <b>@{escape(l.user.username if l.user else 'unknown')}</b> • <span style="color:#8b5cf6;">{escape(l.platform)}</span> ({l.clicks} clicks) {'<small style="color:#f59e0b;">[Hidden]</small>' if not l.visible else ''}
                    <div style="font-size:0.82rem;color:#a1a1aa;word-break:break-all;">{escape(l.url)}</div>
                </div>
                <div style="display:flex;gap:5px;flex-shrink:0;">
                    <form method="post"><input type="hidden" name="action" value="admin_toggle_link"><input type="hidden" name="link_id" value="{l.id}"><input type="hidden" name="q" value="{escape(q_val)}"><button class="mini"><i class="fa-solid fa-eye"></i></button></form>
                    <form method="post"><input type="hidden" name="action" value="admin_delete_link"><input type="hidden" name="link_id" value="{l.id}"><input type="hidden" name="q" value="{escape(q_val)}"><button class="mini" style="border-color:#ef4444;color:#ef4444;"><i class="fa-solid fa-trash"></i></button></form>
                </div>
            </div>"""
            for l in all_links
        ) or '<p style="color:#a1a1aa;">No matching links found.</p>'

        tab_body = f"""
        <div class="card">
            <h2><i class="fa-solid fa-link" style="color:#8b5cf6;"></i> Links Inspector</h2>
            <form method="get" style="display:flex;gap:0.5rem;margin:1rem 0;">
                <input type="hidden" name="tab" value="links">
                <input name="q" value="{escape(q_val)}" placeholder="Filter by username, label, or URL..." style="margin:0;">
                <button class="btn">Filter</button>
            </form>
            {l_rows}
        </div>"""

    elif tab == 'system':
        maint_checked = 'checked' if get_setting('maintenance_mode', '0') == '1' else ''
        reg_checked = 'checked' if get_setting('registrations_open', '1') == '1' else ''
        tab_body = f"""
        <form method="post" class="card">
            <h2><i class="fa-solid fa-sliders" style="color:#8b5cf6;"></i> Site & System Controls</h2>
            <input type="hidden" name="action" value="save_system">
            <label>Site Name / Domain Branding<input name="site_name" value="{escape(get_setting('site_name', 'Dvora.lol'))}"></label>
            <label style="display:flex;align-items:center;gap:10px;margin-top:1rem;cursor:pointer;">
                <input type="checkbox" name="registrations_open" {reg_checked} style="width:auto;margin:0;"> Allow New User Registrations
            </label>
            <label style="display:flex;align-items:center;gap:10px;margin-top:0.8rem;cursor:pointer;color:#f59e0b;">
                <input type="checkbox" name="maintenance_mode" {maint_checked} style="width:auto;margin:0;"> Enable Maintenance Mode (Staff can still access /admin)
            </label>
            <button class="btn" style="margin-top:1.2rem;"><i class="fa-solid fa-floppy-disk"></i> Save System Settings</button>
        </form>"""

    elif tab == 'logs':
        logs = AuditLog.query.order_by(AuditLog.created.desc()).limit(100).all()
        log_rows = ''.join(
            f"""<div class="row">
                <span><b style="color:#8b5cf6;">@{escape(lg.actor)}</b> • <b>{escape(lg.action)}</b> {escape(lg.target)} <small style="color:#a1a1aa;">{escape(lg.details)}</small></span>
                <small style="flex-shrink:0;">{lg.created.strftime('%Y-%m-%d %H:%M')}</small>
            </div>"""
            for lg in logs
        ) or '<p style="color:#a1a1aa;">No staff audit logs recorded yet.</p>'

        tab_body = f"""
        <div class="card">
            <div style="display:flex;justify-content:space-between;align-items:center;margin-bottom:1rem;">
                <h2><i class="fa-solid fa-clipboard-list" style="color:#8b5cf6;"></i> Staff Audit Logs</h2>
                <form method="post"><input type="hidden" name="action" value="clear_audit_logs"><button class="mini">Clear Logs</button></form>
            </div>
            {log_rows}
        </div>"""

    else:
        ql = q_val.lower()
        users = User.query.filter(User.username.ilike(f'%{ql}%')).all() if ql else User.query.order_by(User.created.desc()).all()
        badge_options_html = ''.join(f'<option value="{b["name"]}">{b["name"]}</option>' for b in BADGES_LIST)
        user_rows = ''
        for u in users:
            u_badges = ', '.join(b.name for b in u.badges) or 'None'
            status_tag = f'<span style="color:#ef4444;font-weight:700;">BANNED ({escape(u.ban_reason)})</span>' if u.is_banned else '<span style="color:#10b981;">Active</span>'
            views_count = u.profile.views if u.profile else 0
            user_rows += f"""<div class="row" style="flex-direction: column; align-items: flex-start; gap: 0.65rem; padding: 1.2rem 0;">
                <div style="display:flex; justify-content:space-between; width:100%; flex-wrap:wrap; gap:8px;">
                    <div>
                        <a href="/{u.username}" target="_blank" style="font-size:1.1rem;font-weight:700;color:#fff;text-decoration:none;">@{u.username}</a>
                        <span style="margin-left:8px;font-size:0.85rem;">{status_tag}</span>
                    </div>
                    <span style="font-size: 0.88rem; color: #a1a1aa;">{escape(u.email)} • Views: {views_count} • Credits: <b style="color:#fbbf24;">{u.credits or 0}</b> • Warnings: {len(u.warnings)}</span>
                </div>
                <div style="font-size: 0.88rem; color:#8b5cf6;">Badges: {u_badges}</div>

                <div style="display:flex; gap: 0.5rem; width:100%; flex-wrap: wrap;">
                    <form method="post" style="display:flex; gap:5px; align-items:center;">
                        <input type="hidden" name="tab" value="users"><input type="hidden" name="username" value="{u.username}"><input type="hidden" name="q" value="{escape(q_val)}">
                        <select name="badge_name" style="margin:0; padding:0.4rem; width:auto;">{badge_options_html}</select>
                        <button name="action" value="give" class="btn" style="padding:0.4rem 0.8rem;">Give</button>
                        <button name="action" value="remove" class="mini" style="padding:0.4rem 0.8rem;">Remove</button>
                    </form>

                    <form method="post" style="display:flex; gap:5px; align-items:center;">
                        <input type="hidden" name="tab" value="users"><input type="hidden" name="username" value="{u.username}"><input type="hidden" name="q" value="{escape(q_val)}">
                        <input type="hidden" name="action" value="give_views">
                        <input type="number" name="view_amount" placeholder="Views" style="width:90px; margin:0; padding:0.4rem;" required>
                        <button class="mini" style="padding:0.4rem 0.8rem;">+ Views</button>
                    </form>

                    <form method="post" style="display:flex; gap:5px; align-items:center;">
                        <input type="hidden" name="tab" value="users"><input type="hidden" name="username" value="{u.username}"><input type="hidden" name="q" value="{escape(q_val)}">
                        <input type="hidden" name="action" value="impersonate">
                        <button class="mini" style="padding:0.4rem 0.8rem;border-color:#fbbf24;color:#fbbf24;"><i class="fa-solid fa-right-to-bracket"></i> Login As</button>
                    </form>
                </div>

                <div style="display:flex; gap: 0.5rem; width:100%; flex-wrap: wrap;">
                    <form method="post" style="display:flex; gap:5px; align-items:center; flex:1; min-width:220px;">
                        <input type="hidden" name="tab" value="users"><input type="hidden" name="username" value="{u.username}"><input type="hidden" name="q" value="{escape(q_val)}">
                        <input name="ban_reason" placeholder="Ban reason..." style="margin:0; padding:0.4rem;">
                        {'<button name="action" value="unban" class="btn" style="padding:0.4rem 0.8rem;background:#10b981;color:#000;">Unban</button>' if u.is_banned else '<button name="action" value="ban" class="mini" style="padding:0.4rem 0.8rem;border-color:#ef4444;color:#ef4444;">Ban</button>'}
                    </form>

                    <form method="post" style="display:flex; gap:5px; align-items:center; flex:1; min-width:220px;">
                        <input type="hidden" name="tab" value="users"><input type="hidden" name="username" value="{u.username}"><input type="hidden" name="q" value="{escape(q_val)}">
                        <input type="hidden" name="action" value="warn">
                        <input name="warn_reason" placeholder="Warning reason..." style="margin:0; padding:0.4rem;" required>
                        <button class="mini" style="padding:0.4rem 0.8rem;border-color:#f59e0b;color:#f59e0b;">Warn</button>
                    </form>

                    <form method="post" style="display:flex; gap:5px; align-items:center; flex:1; min-width:240px;">
                        <input type="hidden" name="tab" value="users"><input type="hidden" name="username" value="{u.username}"><input type="hidden" name="q" value="{escape(q_val)}">
                        <input type="hidden" name="action" value="message">
                        <input name="dm_body" placeholder="Direct message..." style="margin:0; padding:0.4rem;" required>
                        <button class="btn" style="padding:0.4rem 0.8rem;">Message</button>
                    </form>
                </div>

                <div style="display:flex; gap: 0.5rem; width:100%; flex-wrap: wrap;">
                    <form method="post" style="display:flex; gap:5px; align-items:center;">
                        <input type="hidden" name="tab" value="users"><input type="hidden" name="username" value="{u.username}"><input type="hidden" name="q" value="{escape(q_val)}">
                        <input type="hidden" name="action" value="reset_password">
                        <input type="password" name="new_pw" placeholder="New password (6+ chars)" minlength="6" style="margin:0; padding:0.4rem; width:190px;" required>
                        <button class="mini" style="padding:0.4rem 0.8rem;">Reset Password</button>
                    </form>

                    <form method="post" onsubmit="return confirm('Permanently delete @{u.username}?');">
                        <input type="hidden" name="tab" value="users"><input type="hidden" name="username" value="{u.username}"><input type="hidden" name="q" value="{escape(q_val)}">
                        <input type="hidden" name="action" value="delete_user">
                        <button class="mini" style="padding:0.4rem 0.8rem;border-color:#ef4444;color:#ef4444;"><i class="fa-solid fa-user-xmark"></i> Delete User</button>
                    </form>
                </div>
            </div>"""

        tab_body = f"""
        <div class="card">
            <h2><i class="fa-solid fa-users" style="color:#8b5cf6;"></i> Users & Moderation ({len(users)})</h2>
            <form method="get" style="display:flex; gap:0.5rem; margin:1rem 0;">
                <input type="hidden" name="tab" value="users">
                <input name="q" value="{escape(q_val)}" placeholder="Search username..." style="margin:0;">
                <button class="btn">Search</button>
            </form>
            {user_rows or '<p>No users found.</p>'}
        </div>"""

    return page(f"""
    <div class="dash">
        <aside>
            <div style="padding:0.5rem 1rem;font-size:0.78rem;font-weight:700;text-transform:uppercase;letter-spacing:1px;color:#ff4b4b;">Staff Panel</div>
            {sidebar_html}
        </aside>
        <section class="dash-body">{tab_body}</section>
    </div>""", 'Admin Panel')


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
  * { box-sizing: border-box; margin: 0; padding: 0; font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif; }
  html, body {
    min-height: 100vh;
    width: 100%;
    background-color: #09090b;
    background-image: {{ bg_style }};
    background-size: cover;
    background-position: center;
    background-repeat: no-repeat;
    background-attachment: fixed;
  }
  body {
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 2.5rem 1.25rem;
    color: {{ p.text_color }};
    overflow-x: hidden;
  }
  .enter-overlay {
    position: fixed;
    inset: 0;
    z-index: 999;
    display: flex;
    align-items: center;
    justify-content: center;
    background: rgba(5, 5, 10, 0.92);
    backdrop-filter: blur(18px);
    -webkit-backdrop-filter: blur(18px);
    cursor: pointer;
    transition: opacity 0.35s ease, visibility 0.35s ease;
  }
  .enter-overlay.hidden {
    opacity: 0;
    visibility: hidden;
    pointer-events: none;
  }
  .enter-box {
    text-align: center;
    padding: 2.25rem;
    border-radius: 22px;
    background: rgba(255, 255, 255, 0.05);
    border: 1px solid rgba(255, 255, 255, 0.14);
    box-shadow: 0 20px 50px rgba(0, 0, 0, 0.65);
  }
  .enter-title {
    font-size: 1.6rem;
    font-weight: 800;
    letter-spacing: 0.4px;
    color: #ffffff;
  }
  .enter-sub {
    margin-top: 0.5rem;
    font-size: 0.92rem;
    color: #a1a1aa;
  }
  .profile-card {
    width: 100%;
    max-width: 680px;
    border-radius: 26px;
    overflow: visible;
    background: rgba(18, 18, 22, {{ p.card_opacity }});
    backdrop-filter: blur({{ p.card_blur }}px);
    -webkit-backdrop-filter: blur({{ p.card_blur }}px);
    border: 1px solid rgba(255, 255, 255, 0.12);
    box-shadow: 0 28px 70px rgba(0, 0, 0, 0.65);
    {% if p.enable_animations %}
    animation: fadeUp 0.6s ease-out;
    {% endif %}
  }
  .banner {
    height: 185px;
    width: 100%;
    border-radius: 26px 26px 0 0;
    background: linear-gradient(135deg, {{ p.accent }}, #111827);
    {% if p.banner %}
    background-image: url('/uploads/{{ p.banner }}');
    background-size: cover;
    background-position: center;
    {% endif %}
  }
  .card-inner { padding: 0 2.25rem 2.25rem; text-align: center; }
  .avatar-wrap { margin-top: -64px; display: flex; justify-content: center; position: relative; z-index: 2; }
  .avatar {
    width: 128px; height: 128px; border-radius: 50%; object-fit: cover; object-position: center;
    border: 4px solid {{ p.accent }};
    background: #18181b;
    box-shadow: 0 10px 28px rgba(0,0,0,0.55);
  }
  @keyframes fadeUp {
    from { opacity: 0; transform: translateY(18px); }
    to { opacity: 1; transform: translateY(0); }
  }
  .banner {
    height: 185px;
    width: 100%;
    background: linear-gradient(135deg, {{ p.accent }}, #111827);
    {% if p.banner %}
    background-image: url('/uploads/{{ p.banner }}');
    background-size: cover;
    background-position: center;
    {% endif %}
  }
  .card-inner { padding: 0 2.25rem 2.25rem; text-align: center; }
  .avatar-wrap { margin-top: -64px; display: flex; justify-content: center; }
  .avatar {
    width: 128px; height: 128px; border-radius: 50%; object-fit: cover;
    border: 4px solid {{ p.accent }};
    background: #18181b;
    box-shadow: 0 10px 28px rgba(0,0,0,0.55);
  }
  .display-name {
    font-size: 1.9rem; font-weight: 800; margin-top: 0.85rem;
    {% if p.enable_animations %}
    background: linear-gradient(90deg, {{ p.text_color }}, {{ p.accent }}, {{ p.text_color }});
    background-size: 200% auto;
    -webkit-background-clip: text;
    -webkit-text-fill-color: transparent;
    animation: shine 4s linear infinite;
    {% endif %}
  }
  @keyframes shine { to { background-position: 200% center; } }
  .username { font-size: 0.95rem; opacity: 0.65; margin-top: 2px; }
  .badges {
    display: flex; flex-wrap: wrap; justify-content: center; gap: 8px;
    margin-top: 1rem;
  }
  .badge {
    display: inline-flex; align-items: center; gap: 6px;
    padding: 5px 12px; border-radius: 999px; font-size: 0.82rem; font-weight: 600;
    background: rgba(255, 255, 255, 0.08);
    border: 1px solid rgba(255, 255, 255, 0.12);
    pointer-events: none;
    user-select: none;
    cursor: default;
  }
  .badge:hover {
    background: rgba(255, 255, 255, 0.08);
    border-color: rgba(255, 255, 255, 0.12);
    transform: none;
  }
  .badge i { color: {{ p.accent }}; }
  .bio {
    margin-top: 1rem; font-size: 1rem; line-height: 1.55; opacity: 0.92;
    white-space: pre-line;
  }
  .discord-box {
    margin-top: 1.15rem; padding: 0.85rem 1.15rem; border-radius: 16px;
    background: rgba(255, 255, 255, 0.06);
    border: 1px solid rgba(255, 255, 255, 0.09);
    display: flex; align-items: center; justify-content: space-between; text-align: left;
  }
  .audio-controls-wrap {
    margin-top: 1.15rem;
    display: flex;
    flex-direction: column;
    align-items: center;
    gap: 0.7rem;
    width: 100%;
  }
  .links { display: flex; flex-direction: column; gap: 0.7rem; margin-top: 1.25rem; }
  .link-btn {
    display: flex; align-items: center; justify-content: space-between;
    padding: 0.9rem 1.2rem; border-radius: 14px;
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
    margin-top: 1.5rem; display: flex; justify-content: space-between; align-items: center;
    font-size: 0.85rem; opacity: 0.7;
  }
  .footer-meta a { color: inherit; text-decoration: none; }
  @media (max-width: 600px) {
    .profile-card { max-width: 100%; border-radius: 20px; }
    .card-inner { padding: 0 1.2rem 1.5rem; }
  }
</style>
</head>
<body>
  <div id="enterOverlay" class="enter-overlay" role="button" tabindex="0" aria-label="Click to Enter">
    <div class="enter-box">
      <div class="enter-title"><i class="fa-solid fa-door-open" style="color:{{ p.accent }};margin-right:8px;"></i>Click to Enter</div>
      <div class="enter-sub">View {{ p.display_name or user.username }}'s profile</div>
    </div>
  </div>

  <div class="profile-card">
    <div class="banner"></div>
    <div class="card-inner">
      <div class="avatar-wrap">
        {% if p.avatar %}
          <img class="avatar" src="/uploads/{{ p.avatar }}" alt="{{ p.display_name }}">
        {% else %}
          <div class="avatar" style="display:flex;align-items:center;justify-content:center;font-size:2.4rem;font-weight:800;color:{{ p.accent }};">
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
          <i class="fa-brands fa-discord" style="font-size:1.55rem;color:#5865F2;"></i>
          <div>
            <div style="font-weight:700;font-size:0.95rem;">{{ p.discord_user }}</div>
            <div style="font-size:0.82rem;opacity:0.75;">{{ p.discord_status or 'Online' }}</div>
          </div>
        </div>
        <span style="width:10px;height:10px;border-radius:50%;background:#10b981;display:inline-block;"></span>
      </div>
      {% endif %}

      {{ audio_player_html|safe }}

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

  <script>
    (function () {
      const overlay = document.getElementById('enterOverlay');
      const audio = document.getElementById('profileAudio');

      function enterProfile() {
        overlay.classList.add('hidden');
        if (audio) {
          audio.play().catch(function () {});
        }
      }

      overlay.addEventListener('click', enterProfile);
      overlay.addEventListener('keydown', function (e) {
        if (e.key === 'Enter' || e.key === ' ') {
          e.preventDefault();
          enterProfile();
        }
      });
    })();
  </script>
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
    bg_style = f"url('{url_for('uploaded_file', filename=p.background)}')" if p.background else themes.get(p.theme, themes['default'])

    audio_player_html = render_audio_players(p)
    visible_links = [l for l in user.links if l.visible]
    visible_badges = [b for b in user.badges if b.visible]

    return render_template_string(
        PUBLIC_PROFILE_HTML,
        user=user,
        p=p,
        bg_style=bg_style,
        audio_player_html=audio_player_html,
        visible_links=visible_links,
        badges=visible_badges,
    )


if __name__ == '__main__':
    app.run(debug=False)
