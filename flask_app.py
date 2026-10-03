from datetime import datetime
import re
from flask import Flask, jsonify, redirect, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy
from sqlalchemy import text

app = Flask(__name__)

# Configure SQLite database (PythonAnywhere path compatible)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# --- DATABASE MODELS ---


class Trade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    position = db.Column(db.Integer, default=0)
    setup_quality_str = db.Column(db.String(20), nullable=False)
    ticker = db.Column(db.String(20), nullable=False)
    entry_datetime = db.Column(db.String(50), nullable=False)
    profit_taken_str = db.Column(db.String(10), nullable=False)
    stop_loss_zero_str = db.Column(db.String(10), nullable=False)
    current_equity = db.Column(db.Float, nullable=False)
    risk_str = db.Column(db.String(20), nullable=False)
    risk_reward_str = db.Column(db.String(20), nullable=False)

    risk_under_half_str = db.Column(db.String(10), nullable=True)
    daily_risk_str = db.Column(db.String(10), nullable=True)

    overtrading_str = db.Column(db.String(10), nullable=True, default='no')
    revenge_trading_str = db.Column(db.String(10), nullable=True, default='no')
    impatient_trading_str = db.Column(db.String(10), nullable=True, default='no')
    fearful_trading_str = db.Column(db.String(10), nullable=True, default='no')

    setup_score = db.Column(db.Float, nullable=False)
    profit_score = db.Column(db.Float, nullable=False)
    stop_loss_score = db.Column(db.Float, nullable=False)
    risk_score = db.Column(db.Float, nullable=False)
    risk_reward_score = db.Column(db.Float, nullable=False)
    daily_risk_score = db.Column(db.Float, nullable=True, default=0.0)
    psychology_score = db.Column(db.Float, nullable=True, default=0.0)
    total_score = db.Column(db.Float, nullable=False)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)
    screenshot_url = db.Column(db.String(500), nullable=True)

    @property
    def psychology_flags(self):
        flags = []
        if self.overtrading_str == 'yes':
            flags.append('Overtrading')
        if self.revenge_trading_str == 'yes':
            flags.append('Revenge')
        if self.impatient_trading_str == 'yes':
            flags.append('Impatient')
        if self.fearful_trading_str == 'yes':
            flags.append('Fearful')
        return flags


class IBKRTrade(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    ticker = db.Column(db.String(20), nullable=False)
    time_entered = db.Column(db.String(50), nullable=False)
    time_exited = db.Column(db.String(50), nullable=False)
    entry_price = db.Column(db.Float, nullable=False, default=0.0)
    exit_price = db.Column(db.Float, nullable=False, default=0.0)
    pnl = db.Column(db.Float, nullable=False, default=0.0)
    balance = db.Column(db.Float, nullable=False, default=0.0)
    timestamp = db.Column(db.DateTime, default=datetime.utcnow)


class AppSetting(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    key = db.Column(db.String(50), unique=True, nullable=False)
    value = db.Column(db.String(200), nullable=False)


with app.app_context():
    db.create_all()
    if not AppSetting.query.filter_by(key='starting_equity').first():
        db.session.add(AppSetting(key='starting_equity', value='10000'))
    if not AppSetting.query.filter_by(key='default_risk_limit').first():
        db.session.add(AppSetting(key='default_risk_limit', value='20'))
    db.session.commit()


# --- SCORING HELPER LOGIC ---

SCORING_RULES = {
    'setup_good': {
        'count': 3,
        'defaults': [1.0, 0.5, 0.0],
        'hint': 'Points for: Good / Medium / Bad',
    },
    'profit_yes': {
        'count': 2,
        'defaults': [1.0, 0.0],
        'hint': 'Points for: Yes / No',
    },
    'sl_yes': {'count': 2, 'defaults': [1.0, 0.0], 'hint': 'Points for: Yes / No'},
    'risk_under_half': {
        'count': 2,
        'defaults': [5.0, -5.0],
        'hint': 'Points for "Risk under 0.5%?": Yes / No',
    },
    'daily_dd': {
        'count': 2,
        'defaults': [5.0, -5.0],
        'hint': 'Points for "Daily drawdown under 1.5%?": Yes / No',
    },
    'rr_bands': {
        'count': 6,
        'defaults': [-5.0, 1.0, 5.0, 15.0, 100.0, 200.0],
        'hint': (
            'Points for R:R in this order: below 0 / 0 to 0.5 / 0.5 to 1 / '
            '1 to 2 / 2 to 3 / 3 and over'
        ),
    },
    'overtrading_yes': {
        'count': 2,
        'defaults': [-1.0, 0.0],
        'hint': 'Points for "Overtrading?": Yes / No',
    },
    'revenge_yes': {
        'count': 2,
        'defaults': [-1.0, 0.0],
        'hint': 'Points for "Revenge trading?": Yes / No',
    },
    'impatient_yes': {
        'count': 2,
        'defaults': [-1.0, 0.0],
        'hint': 'Points for "Impatient trading?": Yes / No',
    },
    'fearful_yes': {
        'count': 2,
        'defaults': [-1.0, 0.0],
        'hint': 'Points for "Fearful trading?": Yes / No',
    },
}


def parse_points(text, count):
    parts = [p for p in re.split(r'[/,\s]+', str(text or '').strip()) if p]
    if len(parts) != count:
        return None
    try:
        return [float(p) for p in parts]
    except ValueError:
        return None


def format_points(points):
    return ' / '.join(f'{p:g}' for p in points)


def get_rule_points(key):
    rule = SCORING_RULES[key]
    setting = AppSetting.query.filter_by(key=key).first()
    if setting:
        parsed = parse_points(setting.value, rule['count'])
        if parsed is not None:
            return parsed
    return list(rule['defaults'])


def to_float_or_none(value):
    try:
        return float(value)
    except (ValueError, TypeError):
        return None


def yes_no_points(answer, pts):
    answer = (answer or '').lower()
    if answer == 'yes':
        return pts[0]
    if answer == 'no':
        return pts[1]
    return 0.0


def calculate_scores(data):
    setup_pts = get_rule_points('setup_good')
    profit_pts = get_rule_points('profit_yes')
    sl_pts = get_rule_points('sl_yes')
    risk_pts = get_rule_points('risk_under_half')
    daily_pts = get_rule_points('daily_dd')
    rr_pts = get_rule_points('rr_bands')

    sq = (data.get('setup_quality') or '').lower()
    if sq == 'good':
        setup_score = setup_pts[0]
    elif sq == 'medium':
        setup_score = setup_pts[1]
    elif sq == 'bad':
        setup_score = setup_pts[2]
    else:
        setup_score = 0.0

    pt = (data.get('profit_taken') or '').lower()
    profit_score = profit_pts[0] if pt == 'yes' else profit_pts[1]

    sl = (data.get('stop_loss_zero') or '').lower()
    stop_loss_score = sl_pts[0] if sl == 'yes' else sl_pts[1]

    risk_score = yes_no_points(data.get('risk_under_half'), risk_pts)
    daily_risk_score = yes_no_points(data.get('daily_risk'), daily_pts)

    rr_val = to_float_or_none(data.get('risk_reward_val'))
    if rr_val is None:
        rr_score = 0.0
    elif rr_val < 0:
        rr_score = rr_pts[0]
    elif rr_val < 0.5:
        rr_score = rr_pts[1]
    elif rr_val < 1:
        rr_score = rr_pts[2]
    elif rr_val < 2:
        rr_score = rr_pts[3]
    elif rr_val < 3:
        rr_score = rr_pts[4]
    else:
        rr_score = rr_pts[5]

    def psych(field, rule_key):
        return yes_no_points(data.get(field) or 'no', get_rule_points(rule_key))

    psychology_score = (
        psych('overtrading', 'overtrading_yes')
        + psych('revenge_trading', 'revenge_yes')
        + psych('impatient_trading', 'impatient_yes')
        + psych('fearful_trading', 'fearful_yes')
    )

    total_score = (
        setup_score
        + profit_score
        + stop_loss_score
        + risk_score
        + daily_risk_score
        + rr_score
        + psychology_score
    )

    return {
        'setup_score': setup_score,
        'profit_score': profit_score,
        'stop_loss_score': stop_loss_score,
        'risk_score': risk_score,
        'daily_risk_score': daily_risk_score,
        'psychology_score': psychology_score,
        'risk_reward_score': rr_score,
        'total_score': round(total_score, 4),
    }


def apply_scores(trade, scores):
    trade.setup_score = scores['setup_score']
    trade.profit_score = scores['profit_score']
    trade.stop_loss_score = scores['stop_loss_score']
    trade.risk_score = scores['risk_score']
    trade.daily_risk_score = scores['daily_risk_score']
    trade.psychology_score = scores['psychology_score']
    trade.risk_reward_score = scores['risk_reward_score']
    trade.total_score = scores['total_score']


def recalculate_all_trades():
    for trade in Trade.query.all():
        apply_scores(
            trade,
            calculate_scores({
                'setup_quality': trade.setup_quality_str,
                'profit_taken': trade.profit_taken_str,
                'stop_loss_zero': trade.stop_loss_zero_str,
                'risk_under_half': trade.risk_under_half_str,
                'daily_risk': trade.daily_risk_str,
                'risk_reward_val': trade.risk_reward_str,
                'overtrading': trade.overtrading_str,
                'revenge_trading': trade.revenge_trading_str,
                'impatient_trading': trade.impatient_trading_str,
                'fearful_trading': trade.fearful_trading_str,
            }),
        )
    db.session.commit()


def ensure_schema():
    columns = {
        row[1] for row in db.session.execute(text('PRAGMA table_info(trade)'))
    }
    changed = False
    try:
        for name, ddl in [
            ('daily_risk_score', 'REAL DEFAULT 0.0'),
            ('psychology_score', 'REAL DEFAULT 0.0'),
            ('overtrading_str', "TEXT DEFAULT 'no'"),
            ('revenge_trading_str', "TEXT DEFAULT 'no'"),
            ('impatient_trading_str', "TEXT DEFAULT 'no'"),
            ('fearful_trading_str', "TEXT DEFAULT 'no'"),
            ('screenshot_url', 'VARCHAR(500)'),
        ]:
            if name not in columns:
                db.session.execute(
                    text(f'ALTER TABLE trade ADD COLUMN {name} {ddl}')
                )
                changed = True
        if 'risk_under_half_str' not in columns:
            db.session.execute(
                text('ALTER TABLE trade ADD COLUMN risk_under_half_str TEXT')
            )
            if 'risk_over_half_str' in columns:
                db.session.execute(
                    text(
                        "UPDATE trade SET risk_under_half_str = CASE"
                        " risk_over_half_str WHEN 'yes' THEN 'no' WHEN 'no'"
                        " THEN 'yes' END"
                    )
                )
            changed = True
        db.session.commit()
    except Exception:
        db.session.rollback()
        app.logger.exception('Schema upgrade skipped')
        return
    if changed:
        recalculate_all_trades()


with app.app_context():
    ensure_schema()


# --- TRADING QUALITY APP ROUTES ---


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/new-trade')
def new_trade_page():
    pts = {key: get_rule_points(key) for key in SCORING_RULES}
    return render_template('new_trade.html', pts=pts)


@app.route('/trades-list')
def trades_list():
    all_trades = Trade.query.order_by(Trade.position.asc()).all()
    return render_template('trades.html', trades=all_trades)


@app.route('/trade/edit/<int:id>', methods=['GET', 'POST'])
def edit_trade(id):
    trade = Trade.query.get_or_404(id)
    if request.method == 'POST':
        data = request.form
        scores = calculate_scores({
            'setup_quality': data.get('setup_quality'),
            'profit_taken': data.get('profit_taken'),
            'stop_loss_zero': data.get('stop_loss_zero'),
            'risk_reward_val': data.get('risk_reward_val'),
            'risk_under_half': data.get('risk_under_half'),
            'daily_risk': data.get('daily_risk'),
            'overtrading': data.get('overtrading'),
            'revenge_trading': data.get('revenge_trading'),
            'impatient_trading': data.get('impatient_trading'),
            'fearful_trading': data.get('fearful_trading'),
        })

        trade.setup_quality_str = data.get('setup_quality')
        trade.ticker = data.get('ticker')
        trade.entry_datetime = data.get('entry_datetime')
        trade.profit_taken_str = data.get('profit_taken')
        trade.stop_loss_zero_str = data.get('stop_loss_zero')
        trade.current_equity = float(data.get('current_equity', 0))
        trade.risk_str = str(data.get('risk_val'))
        trade.risk_reward_str = str(data.get('risk_reward_val'))

        apply_scores(trade, scores)
        trade.risk_under_half_str = data.get('risk_under_half')
        trade.daily_risk_str = data.get('daily_risk')
        trade.overtrading_str = data.get('overtrading', 'no')
        trade.revenge_trading_str = data.get('revenge_trading', 'no')
        trade.impatient_trading_str = data.get('impatient_trading', 'no')
        trade.fearful_trading_str = data.get('fearful_trading', 'no')

        trade.screenshot_url = request.form.get('screenshot_url', '').strip() or None

        db.session.commit()
        return redirect(url_for('trades_list'))

    return render_template('edit_trade.html', trade=trade)


@app.route('/trade/delete/<int:id>', methods=['POST', 'GET'])
def delete_trade(id):
    trade = Trade.query.get_or_404(id)
    db.session.delete(trade)
    db.session.commit()
    return redirect(url_for('trades_list'))


@app.route('/api/trades', methods=['GET', 'POST'])
def manage_trades():
    if request.method == 'POST':
        data = request.json
        scores = calculate_scores(data)
        max_pos = db.session.query(db.func.max(Trade.position)).scalar() or 0
        new_trade = Trade(
            position=max_pos + 1,
            setup_quality_str=data.get('setup_quality'),
            ticker=data.get('ticker'),
            entry_datetime=data.get('entry_datetime'),
            profit_taken_str=data.get('profit_taken'),
            stop_loss_zero_str=data.get('stop_loss_zero'),
            current_equity=float(data.get('current_equity', 0)),
            risk_str=str(data.get('risk_val')),
            risk_reward_str=str(data.get('risk_reward_val')),
            risk_under_half_str=data.get('risk_under_half'),
            daily_risk_str=data.get('daily_risk'),
            overtrading_str=data.get('overtrading', 'no'),
            revenge_trading_str=data.get('revenge_trading', 'no'),
            impatient_trading_str=data.get('impatient_trading', 'no'),
            fearful_trading_str=data.get('fearful_trading', 'no'),
            screenshot_url=data.get('screenshot_url', '').strip() or None,
            setup_score=scores['setup_score'],
            profit_score=scores['profit_score'],
            stop_loss_score=scores['stop_loss_score'],
            risk_score=scores['risk_score'],
            daily_risk_score=scores['daily_risk_score'],
            psychology_score=scores['psychology_score'],
            risk_reward_score=scores['risk_reward_score'],
            total_score=scores['total_score'],
        )
        db.session.add(new_trade)
        db.session.commit()
        return jsonify({
            'status': 'success',
            'total_score': scores['total_score'],
        })

    trades = Trade.query.order_by(Trade.position.asc()).all()
    result = []
    for t in trades:
        result.append({
            'id': t.id,
            'ticker': t.ticker,
            'entry_datetime': t.entry_datetime,
            'current_equity': t.current_equity,
            'risk_val': float(t.risk_str) if t.risk_str else 0.0,
            'risk_reward_str': (
                float(t.risk_reward_str) if t.risk_reward_str else 0.0
            ),
            'total_score': t.total_score,
        })
    return jsonify(result)


@app.route('/trade/move/<int:id>/<direction>')
def move_trade(id, direction):
    trade = Trade.query.get_or_404(id)

    if direction == 'up':
        adjacent = (
            Trade.query.filter(Trade.position < trade.position)
            .order_by(Trade.position.desc())
            .first()
        )
    elif direction == 'down':
        adjacent = (
            Trade.query.filter(Trade.position > trade.position)
            .order_by(Trade.position.asc())
            .first()
        )
    else:
        adjacent = None

    if adjacent:
        trade.position, adjacent.position = adjacent.position, trade.position
        db.session.commit()

    return redirect(url_for('trades_list'))


# --- IBKR TRADES ROUTES ---


@app.route('/ibkr', methods=['GET', 'POST'])
def ibkr_trades():
    if request.method == 'POST':
        try:
            entry_price_val = float(request.form.get('entry_price', 0))
        except ValueError:
            entry_price_val = 0.0

        try:
            exit_price_val = float(request.form.get('exit_price', 0))
        except ValueError:
            exit_price_val = 0.0

        try:
            pnl_val = float(request.form.get('pnl', 0))
        except ValueError:
            pnl_val = 0.0

        try:
            balance_val = float(request.form.get('balance', 0))
        except ValueError:
            balance_val = 0.0

        new_ibkr_trade = IBKRTrade(
            ticker=request.form.get('ticker'),
            time_entered=request.form.get('time_entered'),
            time_exited=request.form.get('time_exited'),
            entry_price=entry_price_val,
            exit_price=exit_price_val,
            pnl=pnl_val,
            balance=balance_val,
        )
        db.session.add(new_ibkr_trade)
        db.session.commit()
        return redirect(url_for('ibkr_trades'))

    all_ibkr_trades = IBKRTrade.query.order_by(IBKRTrade.id.asc()).all()
    return render_template('ibkr.html', trades=all_ibkr_trades)


@app.route('/ibkr/delete/<int:id>', methods=['POST', 'GET'])
def delete_ibkr_trade(id):
    ibkr_trade = IBKRTrade.query.get_or_404(id)
    db.session.delete(ibkr_trade)
    db.session.commit()
    return redirect(url_for('ibkr_trades'))


@app.route('/ibkr/edit/<int:id>', methods=['GET', 'POST'])
def edit_ibkr_trade(id):
    ibkr_trade = IBKRTrade.query.get_or_404(id)
    if request.method == 'POST':
        try:
            ibkr_trade.ticker = request.form.get('ticker')
            ibkr_trade.time_entered = request.form.get('time_entered')
            ibkr_trade.time_exited = request.form.get('time_exited')
            ibkr_trade.entry_price = float(request.form.get('entry_price', 0))
            ibkr_trade.exit_price = float(request.form.get('exit_price', 0))
            ibkr_trade.pnl = float(request.form.get('pnl', 0))
            ibkr_trade.balance = float(request.form.get('balance', 0))
            db.session.commit()
            return redirect(url_for('ibkr_trades'))
        except ValueError:
            pass

    return render_template('edit_ibkr.html', trade=ibkr_trade)


@app.route('/ibkr-charts')
def ibkr_charts():
    return render_template('ibkr_charts.html')


@app.route('/api/ibkr-trades')
def api_ibkr_trades():
    trades = IBKRTrade.query.order_by(IBKRTrade.id.asc()).all()
    return jsonify([
        {
            'id': t.id,
            'ticker': t.ticker,
            'time_entered': t.time_entered,
            'time_exited': t.time_exited,
            'entry_price': t.entry_price,
            'exit_price': t.exit_price,
            'pnl': t.pnl,
            'balance': t.balance,
        }
        for t in trades
    ])


# --- SETTINGS ROUTES ---

SETTINGS_PAGE_RULES = {
    1: ('Setup Quality', 'Good / Medium / Bad', 'setup_good'),
    2: ('1/3rd Profit Taken', 'Yes / No', 'profit_yes'),
    3: ('Stop Loss Moved to Zero', 'Yes / No', 'sl_yes'),
    4: ('Risk < 0.5%', 'Yes / No', 'risk_under_half'),
    5: ('Daily Drawdown < 1.5%', 'Yes / No', 'daily_dd'),
    6: (
        'Risk:Reward Ratio (R:R)',
        '<0 / 0-0.5 / 0.5-1 / 1-2 / 2-3 / 3+',
        'rr_bands',
    ),
    7: ('Overtrading', 'Yes / No', 'overtrading_yes'),
    8: ('Revenge Trading', 'Yes / No', 'revenge_yes'),
    9: ('Impatient Trading', 'Yes / No', 'impatient_yes'),
    10: ('Fearful Trading', 'Yes / No', 'fearful_yes'),
}


def current_points_text(key):
    return format_points(get_rule_points(key))


@app.route('/settings')
def settings_page():
    scoring_rules = [
        {
            'id': rule_id,
            'category': category,
            'condition': condition,
            'key': key,
            'points': current_points_text(key),
        }
        for rule_id, (category, condition, key) in SETTINGS_PAGE_RULES.items()
    ]
    return render_template('settings.html', rules=scoring_rules)


@app.route('/settings/edit/<int:id>', methods=['GET', 'POST'])
def edit_setting(id):
    if id not in SETTINGS_PAGE_RULES:
        return redirect(url_for('settings_page'))

    category, _condition, key = SETTINGS_PAGE_RULES[id]
    rule_info = SCORING_RULES[key]
    rule = {'category': category, 'points': current_points_text(key)}
    error = None

    if request.method == 'POST':
        submitted = (request.form.get('points') or '').strip()
        parsed = parse_points(submitted, rule_info['count'])

        if parsed is None:
            error = (
                f"Please enter exactly {rule_info['count']} numbers separated by"
                f" '/' or ','. {rule_info['hint']}."
            )
            rule['points'] = submitted
        else:
            value = format_points(parsed)
            setting_obj = AppSetting.query.filter_by(key=key).first()
            if setting_obj:
                setting_obj.value = value
            else:
                db.session.add(AppSetting(key=key, value=value))
            db.session.commit()

            recalculate_all_trades()
            return redirect(url_for('settings_page'))

    return render_template(
        'edit_setting.html', rule=rule, id=id, error=error, hint=rule_info['hint']
    )


if __name__ == '__main__':
    app.run(debug=True)