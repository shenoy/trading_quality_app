from datetime import datetime
from flask import Flask, jsonify, redirect, render_template, request, url_for
from flask_sqlalchemy import SQLAlchemy

app = Flask(__name__)

# Configure SQLite database (PythonAnywhere path compatible)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///database.db'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


# --- DATABASE MODELS ---


class Trade(db.Model):
  id = db.Column(db.Integer, primary_key=True)
  position = db.Column(
      db.Integer, default=0
  )  # New column to track custom order
  setup_quality_str = db.Column(db.String(20), nullable=False)
  ticker = db.Column(db.String(20), nullable=False)
  entry_datetime = db.Column(db.String(50), nullable=False)
  profit_taken_str = db.Column(db.String(10), nullable=False)
  stop_loss_zero_str = db.Column(db.String(10), nullable=False)
  current_equity = db.Column(db.Float, nullable=False)
  risk_str = db.Column(db.String(20), nullable=False)
  risk_reward_str = db.Column(db.String(20), nullable=False)

  risk_over_half_str = db.Column(db.String(10), nullable=True)
  daily_risk_str = db.Column(db.String(10), nullable=True)

  # Scores
  setup_score = db.Column(db.Float, nullable=False)
  profit_score = db.Column(db.Float, nullable=False)
  stop_loss_score = db.Column(db.Float, nullable=False)
  risk_score = db.Column(db.Float, nullable=False)
  risk_reward_score = db.Column(db.Float, nullable=False)
  total_score = db.Column(db.Float, nullable=False)
  timestamp = db.Column(db.DateTime, default=datetime.utcnow)


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
  # Seed default settings if empty
  if not AppSetting.query.filter_by(key='starting_equity').first():
    db.session.add(
        AppSetting(key='starting_equity', value='10000')
    )  # Default example setting
  if not AppSetting.query.filter_by(key='default_risk_limit').first():
    db.session.add(AppSetting(key='default_risk_limit', value='20'))
  db.session.commit()


# --- SCORING HELPER LOGIC ---


def calculate_scores(data):
  # Fetch dynamic settings from database with fallbacks
  def get_setting_val(key, default):
    setting = AppSetting.query.filter_by(key=key).first()
    return setting.value if setting else default

  # 1) Setup Quality scores (e.g., stored as comma or slash separated, or logic)
  sq = data.get('setup_quality', '').lower()
  if sq == 'good':
    setup_score = 1.0
  elif sq == 'medium':
    setup_score = 0.5
  else:
    setup_score = 0.0

  # 4) 1/3 rd profit taken
  pt = data.get('profit_taken', '').lower()
  profit_score = 1.0 if pt == 'yes' else 0.0

  # 5) Stop loss moved to zero
  sl = data.get('stop_loss_zero', '').lower()
  stop_loss_score = 1.0 if sl == 'yes' else 0.0

  # 7) Risk under (example using dynamic risk threshold setup if desired)
  try:
    risk_val = float(data.get('risk_val', 0))
  except ValueError:
    risk_val = 0

  # You can parse thresholds from AppSetting or keep rule checks
  if risk_val < 10:
    risk_score = 1.0
  elif risk_val < 20:
    risk_score = 0.5
  else:
    risk_score = 0.0

  # 8) Risk Reward
  try:
    rr_val = float(data.get('risk_reward_val', 0))
  except ValueError:
    rr_val = 0

  if rr_val >= 5:
    rr_score = 5.0
  elif rr_val >= 4:
    rr_score = 4.0
  elif rr_val >= 2:
    rr_score = 3.0
  elif rr_val >= 1:
    rr_score = 2.0
  elif rr_val > 0.5:
    rr_score = 1.0
  else:
    rr_score = 0.0

  # Handle any additional psychology scores if you added them (overtrading, etc.)
  overtrading_score = (
      -1.0 if data.get('overtrading', '').lower() == 'yes' else 0.0
  )
  revenge_score = -1.0 if data.get('revenge_trading', '').lower() == 'yes' else 0.0
  impatient_score = (
      -1.0 if data.get('impatient_trading', '').lower() == 'yes' else 0.0
  )
  fearful_score = -1.0 if data.get('fearful_trading', '').lower() == 'yes' else 0.0

  total_score = (
      setup_score
      + profit_score
      + stop_loss_score
      + risk_score
      + rr_score
      + overtrading_score
      + revenge_score
      + impatient_score
      + fearful_score
  )

  return {
      'setup_score': setup_score,
      'profit_score': profit_score,
      'stop_loss_score': stop_loss_score,
      'risk_score': risk_score,
      'risk_reward_score': rr_score,
      'total_score': total_score,
  }

# --- TRADING QUALITY APP ROUTES ---


@app.route('/')
def index():
  return render_template('index.html')

@app.route('/new-trade')
def new_trade_page():
    return render_template('new_trade.html')


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
        'risk_val': data.get('risk_val'),
        'risk_reward_val': data.get('risk_reward_val'),
    })

    trade.setup_quality_str = data.get('setup_quality')
    trade.ticker = data.get('ticker')
    trade.entry_datetime = data.get('entry_datetime')
    trade.profit_taken_str = data.get('profit_taken')
    trade.stop_loss_zero_str = data.get('stop_loss_zero')
    trade.current_equity = float(data.get('current_equity', 0))
    trade.risk_str = str(data.get('risk_val'))
    trade.risk_reward_str = str(data.get('risk_reward_val'))

    trade.setup_score = scores['setup_score']
    trade.profit_score = scores['profit_score']
    trade.stop_loss_score = scores['stop_loss_score']
    trade.risk_score = scores['risk_score']
    trade.risk_reward_score = scores['risk_reward_score']
    trade.total_score = scores['total_score']
    # Inside your trade edit POST logic:
    trade.risk_over_half_str = request.form.get('risk_over_half', 'no')
    trade.daily_risk_str = request.form.get('daily_risk', 'no')

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
            # Make sure these keys match what your frontend JS sends:
            risk_over_half_str=data.get('risk_over_half', 'no'),
            daily_risk_str=data.get('daily_risk', 'no'),
            setup_score=scores['setup_score'],
            profit_score=scores['profit_score'],
            stop_loss_score=scores['stop_loss_score'],
            risk_score=scores['risk_score'],
            risk_reward_score=scores['risk_reward_score'],
            total_score=scores['total_score'],
        )
        db.session.add(new_trade)
        db.session.commit()
        return jsonify({'status': 'success', 'total_score': scores['total_score']})

    # GET request handler (properly nested inside the route function)
    trades = Trade.query.order_by(Trade.position.asc()).all()
    result = []
    for t in trades:
        result.append({
            'id': t.id,
            'ticker': t.ticker,
            'entry_datetime': t.entry_datetime,
            'current_equity': t.current_equity,
            'risk_val': float(t.risk_str) if t.risk_str else 0.0,
            'risk_reward_str': float(t.risk_reward_str) if t.risk_reward_str else 0.0,  # Fixed key name to match frontend
            'total_score': t.total_score,
        })
    return jsonify(result)
# GET: Fetch trades ordered by their custom position sequence
    trades = Trade.query.order_by(Trade.position.asc()).all()
    result = []
    for t in trades:
        result.append({
            'id': t.id,
            'ticker': t.ticker,
            'entry_datetime': t.entry_datetime,
            'current_equity': t.current_equity,
            'risk_val': float(t.risk_str) if t.risk_str else 0.0,
            'risk_reward_str': float(t.risk_reward_str) if t.risk_reward_str else 0.0,
            'total_score': t.total_score,
        })
    return jsonify(result)

@app.route('/trade/move/<int:id>/<direction>')
def move_trade(id, direction):
  trade = Trade.query.get_or_404(id)

  if direction == 'up':
    # Find the trade directly above it (highest position lower than current)
    adjacent = (
        Trade.query.filter(Trade.position < trade.position)
        .order_by(Trade.position.desc())
        .first()
    )
  elif direction == 'down':
    # Find the trade directly below it (lowest position higher than current)
    adjacent = (
        Trade.query.filter(Trade.position > trade.position)
        .order_by(Trade.position.asc())
        .first()
    )
  else:
    adjacent = None

  if adjacent:
    # Swap their positions
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


# --- SETTINGS ROUTES ---


@app.route('/settings')
def settings_page():
  # Define the rules with their associated database keys
  scoring_rules = [
      {
          'id': 1,
          'category': 'Setup Quality',
          'condition': 'Good / Medium / Bad',
          'key': 'setup_good',  # Use this to look up current value
      },
      {
          'id': 2,
          'category': '1/3rd Profit Taken',
          'condition': 'Yes / No',
          'key': 'profit_yes',
      },
      {
          'id': 3,
          'category': 'Stop Loss Moved to Zero',
          'condition': 'Yes / No',
          'key': 'sl_yes',
      },
      {
          'id': 4,
          'category': 'Risk Amount ($)',
          'condition': '<10 / <20 / <50',
          'key': 'risk_t1',
      },
      {
          'id': 5,
          'category': 'Risk:Reward Ratio (R:R)',
          'condition': '>0.5 / >1 / >2 / >4 / >5',
          'key': 'rr_t5',
      },
  ]

  # Fetch current values from database for each rule and attach them
  for rule in scoring_rules:
    setting_item = AppSetting.query.filter_by(key=rule['key']).first()
    # If found in DB, use it; otherwise fallback to default text
    rule['points'] = setting_item.value if setting_item else 'Custom'

  return render_template('settings.html', rules=scoring_rules)


@app.route('/settings/edit/<int:id>', methods=['GET', 'POST'])
def edit_setting(id):
  scoring_rules = {
      1: {'category': 'Setup Quality', 'points': '1 / 0.5 / 0'},
      2: {'category': '1/3rd Profit Taken', 'points': '1 / 0'},
      3: {'category': 'Stop Loss Moved to Zero', 'points': '1 / 0'},
      4: {'category': 'Risk Amount ($)', 'points': '1 / 0.5 / 0'},
      5: {'category': 'Risk:Reward Ratio (R:R)', 'points': '1 / 2 / 3 / 4 / 5'},
  }

  setting_keys_map = {
      1: ('setup_good', 'setup_medium', 'setup_bad'),
      2: ('profit_yes', 'profit_no'),
      3: ('sl_yes', 'sl_no'),
      4: ('risk_t1', 'risk_s1'),
      5: ('rr_t5', 'rr_s5'),
  }

  rule = scoring_rules.get(id, {'category': 'Unknown', 'points': ''})

  if request.method == 'POST':
    new_points = request.form.get('points')
    keys = setting_keys_map.get(id, [])

    if keys:
      setting_obj = AppSetting.query.filter_by(key=keys[0]).first()
      if setting_obj:
        setting_obj.value = str(new_points)
      else:
        new_setting = AppSetting(key=keys[0], value=str(new_points))
        db.session.add(new_setting)
      db.session.commit()

      # --- AUTOMATIC RECALCULATION FOR ALL EXISTING TRADES ---
      all_trades = Trade.query.all()
      for trade in all_trades:
        # Build payload dictionary from existing trade record
        trade_data = {
            'setup_quality': trade.setup_quality_str,
            'profit_taken': trade.profit_taken_str,
            'stop_loss_zero': trade.stop_loss_zero_str,
            'risk_val': trade.risk_str,
            'risk_reward_val': trade.risk_reward_str,
            'overtrading': getattr(trade, 'overtrading_str', 'no'),
            'revenge_trading': getattr(trade, 'revenge_str', 'no'),
            'impatient_trading': getattr(trade, 'impatient_str', 'no'),
            'fearful_trading': getattr(trade, 'fearful_str', 'no'),
        }

        # Recalculate scores with the new rules
        new_scores = calculate_scores(trade_data)

        # Update trade score columns
        trade.setup_score = new_scores['setup_score']
        trade.profit_score = new_scores['profit_score']
        trade.stop_loss_score = new_scores['stop_loss_score']
        trade.risk_score = new_scores['risk_score']
        trade.risk_reward_score = new_scores['risk_reward_score']
        trade.total_score = new_scores['total_score']

      # Save all updated trade scores to the database
      db.session.commit()
      # --------------------------------------------------------

    return redirect(url_for('settings_page'))

  return render_template('edit_setting.html', rule=rule, id=id)


if __name__ == '__main__':
  app.run(debug=True)