import os
import logging
from logging.handlers import RotatingFileHandler
from datetime import timedelta

from flask import Flask, render_template, request, redirect, url_for, session, flash  # type: ignore
from flask_wtf import CSRFProtect  # type: ignore
from flask_wtf.csrf import generate_csrf, CSRFError  # type: ignore
from flask_limiter import Limiter  # type: ignore
from flask_limiter.util import get_remote_address  # type: ignore
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash  # type: ignore

from database import (  # type: ignore
    init_db, get_all_indicators,
    add_indicator, remove_indicator,
    add_news_url, get_all_news_urls,
    add_attack_url, get_all_attack_urls,
    log_malware, get_malware_logs,
    get_all_malware_sites, add_malware_site,
    check_url_malicious, log_search, get_search_history,
    get_dashboard_stats
)
from ml_model import detect  # type: ignore
from validators import (  # type: ignore
    sanitize_input,
    is_valid_url,
    is_valid_keyword,
    is_valid_indicator,
    is_valid_search_input,
)

# ==================== APP CONFIGURATION ====================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
LOG_DIR = os.path.join(BASE_DIR, 'logs')

app = Flask(__name__)
app.secret_key = os.environ.get('SECRET_KEY', 'change-this-in-production')
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['SESSION_COOKIE_SECURE'] = os.environ.get('RENDER', '') == 'true'
app.permanent_session_lifetime = timedelta(minutes=30)

# ==================== EXTENSIONS ====================
csrf = CSRFProtect(app)
limiter = Limiter(
    app=app,
    key_func=get_remote_address,
    default_limits=["200 per day", "50 per hour"]
)

# ==================== LOGGING ====================
if not os.path.exists(LOG_DIR):
    os.makedirs(LOG_DIR)

file_handler = RotatingFileHandler(
    os.path.join(LOG_DIR, 'app.log'),
    maxBytes=1024 * 1024,
    backupCount=10
)
file_handler.setFormatter(logging.Formatter(
    '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
))
file_handler.setLevel(logging.INFO)
app.logger.addHandler(file_handler)
app.logger.setLevel(logging.INFO)

# ==================== USER CREDENTIALS ====================
USERS = {
    'admin': {
        'password_hash': generate_password_hash(
            os.environ.get('ADMIN_PASSWORD', 'Admin@2026Secure!')
        ),
        'role': 'admin'
    },
    'attacker': {
        'password_hash': generate_password_hash(
            os.environ.get('ATTACKER_PASSWORD', 'Attacker@2026Secure!')
        ),
        'role': 'attacker'
    }
}

# ==================== INITIALIZE DATABASE ====================
_db_initialized = False


@app.before_request
def _ensure_db():
    global _db_initialized
    if not _db_initialized:
        init_db()
        app.logger.info('Database initialized on first request')
        _db_initialized = True


@app.context_processor
def inject_csrf_token():
    return {'csrf_token': generate_csrf}


# ==================== MIDDLEWARE ====================
@app.before_request
def before_request():
    session.permanent = True
    session.modified = True


@app.after_request
def add_security_headers(response):
    response.headers['X-Content-Type-Options'] = 'nosniff'
    response.headers['X-Frame-Options'] = 'SAMEORIGIN'
    response.headers['X-XSS-Protection'] = '1; mode=block'
    response.headers['Cache-Control'] = 'no-store, no-cache, must-revalidate'
    return response


# ==================== AUTH DECORATORS ====================
def admin_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('admin_logged_in'):
            flash('Please login first', 'error')
            return redirect(url_for('admin_login'))
        return f(*args, **kwargs)
    return decorated


def attacker_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        if not session.get('attacker_logged_in'):
            flash('Please login first', 'error')
            return redirect(url_for('attacker_login'))
        return f(*args, **kwargs)
    return decorated


# ==================== PUBLIC ROUTES ====================
@app.route('/')
def index():
    return render_template('index.html')


@app.route('/search')
def search():
    return render_template('search.html')


@app.route('/search/results', methods=['GET', 'POST'])
@limiter.limit("20 per minute")
def search_results():
    headline = request.args.get('search', '') or request.form.get('urls', '') or ''
    headline = sanitize_input(headline, max_length=1000)
    ip_addr = request.remote_addr or '0.0.0.0'
    validation_error = None

    if not headline:
        return render_template(
            'search_results.html',
            result=None,
            headline=headline,
            validation_error=validation_error
        )

    if not is_valid_search_input(headline):
        validation_error = (
            'Please enter a full news headline with at least 4 words or a valid '
            'http/https news URL.'
        )
        app.logger.info('Rejected invalid search input: "%s" from %s', headline[:80], ip_addr)
        return render_template(
            'search_results.html',
            result=None,
            headline=headline,
            validation_error=validation_error
        )

    malicious_entry = check_url_malicious(headline)

    if malicious_entry:
        keyword = malicious_entry.get('keyword', 'Blocked URL')
        log_malware(headline, keyword, ip_addr, request.user_agent.string)
        log_search(headline, 'Malicious URL', 100, ip_addr)
        app.logger.warning(f'Malicious URL detected: {headline} from {ip_addr}')
        return render_template('malicious_warning.html', url=headline, keyword=keyword)

    try:
        detection = detect(headline)
    except Exception:
        app.logger.exception('Detection failed for search input from %s', ip_addr)
        detection = {
            'result': 'Unknown',
            'confidence': 0,
            'method': 'Machine Learning Model',
            'details': 'The system could not analyze this input right now. Please try again.',
            'risk_factors': ['Detection service error']
        }

    log_search(
        headline,
        detection.get('result', 'Unknown'),
        detection.get('confidence', 0),
        ip_addr
    )

    app.logger.info(
        f'Search: "{headline[:50]}..." -> {detection.get("result", "Unknown")}'
    )

    return render_template(
        'search_results.html',
        headline=headline,
        validation_error=validation_error,
        result=detection.get('result', 'Unknown'),
        confidence=detection.get('confidence', 0),
        method=detection.get('method', 'Machine Learning Model'),
        details=detection.get('details', 'No details available'),
        risk_factors=detection.get('risk_factors', [])
    )


# ==================== ADMIN ROUTES ====================
@app.route('/admin/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def admin_login():
    if session.get('admin_logged_in'):
        return redirect(url_for('admin_home'))

    if request.method == 'POST':
        name = sanitize_input(request.form.get('name', ''))
        password = request.form.get('pass', '')

        user = USERS.get(name)
        if user and user['role'] == 'admin' and check_password_hash(user['password_hash'], password):
            session['admin_logged_in'] = True
            session['username'] = name
            app.logger.info(f'Admin login from {request.remote_addr}')
            flash('Login Successful!', 'success')
            return redirect(url_for('admin_home'))
        else:
            app.logger.warning(f'Failed admin login from {request.remote_addr}')
            flash('Invalid ID and Password', 'error')
            return redirect(url_for('admin_login'))

    return render_template('admin_login.html')


@app.route('/admin/home')
@admin_required
def admin_home():
    stats = get_dashboard_stats()
    return render_template('admin_home.html', stats=stats)


@app.route('/admin/indicators', methods=['GET', 'POST'])
@admin_required
def admin_indicators():
    if request.method == 'POST':
        action = request.form.get('action')

        if action == 'add':
            new_word = sanitize_input(request.form.get('new_word', '')).lower()
            if not new_word:
                flash('Please enter a word', 'error')
            elif not is_valid_indicator(new_word):
                flash('Invalid format (letters only, 2-50 characters)', 'error')
            elif add_indicator(new_word):
                app.logger.info(f'Indicator added: {new_word}')
                flash('Indicator added successfully!', 'success')
            else:
                flash('Indicator already exists!', 'error')

        elif action == 'remove':
            word_to_remove = sanitize_input(request.form.get('remove_word'))
            if word_to_remove:
                remove_indicator(word_to_remove)
                app.logger.info(f'Indicator removed: {word_to_remove}')
                flash('Indicator removed successfully!', 'success')

        return redirect(url_for('admin_indicators'))

    indicators = get_all_indicators()
    return render_template('admin_indicators.html', indicators=indicators)


@app.route('/admin/add-url', methods=['GET', 'POST'])
@admin_required
def admin_add_url():
    if request.method == 'POST':
        url = sanitize_input(request.form.get('urls', ''))
        keyword = sanitize_input(request.form.get('message', ''))

        if not url or not keyword:
            flash('Please fill in all fields', 'error')
        elif not is_valid_url(url):
            flash('Please enter a valid URL', 'error')
        elif not is_valid_keyword(keyword):
            flash('Invalid keyword (letters, numbers, spaces only)', 'error')
        else:
            add_news_url(url, keyword)
            app.logger.info(f'News URL added: {url}')
            flash('URL added to indexer!', 'success')
            return redirect(url_for('admin_view_urls'))

    return render_template('admin_add_url.html')


@app.route('/admin/view-urls')
@admin_required
def admin_view_urls():
    urls = get_all_news_urls()
    return render_template('admin_view_urls.html', urls=urls)


@app.route('/admin/view-malware')
@admin_required
def admin_view_malware():
    records = get_malware_logs()
    return render_template('admin_view_malware.html', records=records)


@app.route('/admin/view-all-malware')
@admin_required
def admin_view_all_malware():
    sites = get_all_malware_sites()
    return render_template('admin_view_all_malware.html', sites=sites)


@app.route('/admin/search-history')
@admin_required
def admin_search_history():
    history = get_search_history(100)
    return render_template('admin_search_history.html', history=history)


@app.route('/admin/logout')
def admin_logout():
    app.logger.info(f'Admin logout from {request.remote_addr}')
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))


# ==================== ATTACKER ROUTES ====================
@app.route('/attacker/login', methods=['GET', 'POST'])
@limiter.limit("5 per minute")
def attacker_login():
    if session.get('attacker_logged_in'):
        return redirect(url_for('attacker_home'))

    if request.method == 'POST':
        name = sanitize_input(request.form.get('name', ''))
        password = request.form.get('pass', '')

        user = USERS.get(name)
        if user and user['role'] == 'attacker' and check_password_hash(user['password_hash'], password):
            session['attacker_logged_in'] = True
            session['username'] = name
            app.logger.info(f'Attacker login from {request.remote_addr}')
            flash('Attacker Login Successful!', 'success')
            return redirect(url_for('attacker_home'))
        else:
            app.logger.warning(f'Failed attacker login from {request.remote_addr}')
            flash('Invalid ID and Password', 'error')
            return redirect(url_for('attacker_login'))

    return render_template('attacker_login.html')


@app.route('/attacker/home', methods=['GET', 'POST'])
@attacker_required
def attacker_home():
    if request.method == 'POST':
        url = sanitize_input(request.form.get('urls', ''))
        keyword = sanitize_input(request.form.get('message', ''))

        if not url or not keyword:
            flash('Please fill in all fields', 'error')
        elif not is_valid_url(url):
            flash('Please enter a valid URL', 'error')
        elif not is_valid_keyword(keyword):
            flash('Invalid keyword format', 'error')
        else:
            add_attack_url(url, keyword)
            add_malware_site(url)
            app.logger.warning(f'Attack URL added: {url} from {request.remote_addr}')
            flash('Attack URL added!', 'success')
            return redirect(url_for('attacker_view'))

    return render_template('attacker_home.html')


@app.route('/attacker/view')
@attacker_required
def attacker_view():
    urls = get_all_attack_urls()
    return render_template('attacker_view.html', urls=urls)


@app.route('/attacker/logout')
def attacker_logout():
    app.logger.info(f'Attacker logout from {request.remote_addr}')
    session.clear()
    flash('Logged out successfully', 'success')
    return redirect(url_for('index'))


# ==================== ERROR HANDLERS ====================
@app.errorhandler(404)
def page_not_found(e):
    return render_template('error.html', error_code=404, error_msg='Page Not Found'), 404


@app.errorhandler(CSRFError)
def handle_csrf_error(e):
    app.logger.warning('CSRF validation failed: %s', e.description)
    return render_template('error.html', error_code=400, error_msg='Your session expired. Please refresh and try again.'), 400


@app.errorhandler(500)
def internal_error(e):
    app.logger.error(f'Internal error: {str(e)}')
    return render_template('error.html', error_code=500, error_msg='Internal Server Error'), 500


@app.errorhandler(429)
def rate_limit_exceeded(e):
    return render_template('error.html', error_code=429,
                          error_msg='Too many requests. Please try again later.'), 429


# ==================== RUN ====================
if __name__ == '__main__':
    init_db()
    debug_mode = os.environ.get('FLASK_DEBUG', 'False').lower() == 'true'
    port = int(os.environ.get('PORT', 5000))
    app.run(debug=debug_mode, host='0.0.0.0', port=port)
