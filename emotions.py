"""1-10 emotion scales for the trade journal.

Built from the trading-psychology deck. Each emotion has ten levels and every
level has a mental/emotional side and a technical side (what the trading
looks like). Level 1 is the slightest nudge, level 10 the most intense.

Where the text comes from:
  * Greed, Fear, Tilt          - the deck's own 10-level scales (slides 50-55).
  * Boredom, Impatience,
    Overtrading                - the deck's 1-10 maps, which describe four bands
                                 (1-3, 4-6, 7-8, 9-10); every level in a band
                                 shares that band's wording (slides 113-119).
  * Overconfidence             - the deck's confidence scale (levels 5-10) plus
                                 its overconfidence map; drafted into ten levels.
  * Low confidence             - the deck's confidence scale (levels 1-4) and its
                                 list of signs; drafted into ten levels.
  * Desperation                - the deck describes it in words only, so the ten
                                 levels are drafted from those descriptions.

The deck itself says to rewrite every level in your own words, so edit any of
the text below freely. Nothing else in the app depends on the wording.
"""

# Zones come from the deck's daily checklist (slide 121).
ZONES = [
    (1, 3, 'green', 'Green: normal execution'),
    (4, 6, 'yellow', 'Yellow: intervene, read your correction aloud before the next trade'),
    (7, 10, 'red', 'Red: step away from the screen for at least 30 minutes'),
]


def zone_for(level):
    for low, high, name, _ in ZONES:
        if low <= level <= high:
            return name
    return None


def _banded(bands):
    """bands: [(last_level, mental, technical), ...] -> ten (mental, technical)."""
    levels = []
    for level in range(1, 11):
        for last, mental, technical in bands:
            if level <= last:
                levels.append((mental, technical))
                break
    return levels


EMOTIONS = [
    {
        'key': 'greed',
        'label': 'Greed',
        'color': '#b7791f',
        'point': 'circle',
        'source': 'Deck slides 50-51',
        'levels': [
            ("Glance at the open P&L. Pleasant if green, not shaken if red.",
             "No change. Plan followed."),
            ("Start thinking about what the money is worth. Want a big winner to feel progress.",
             "Attention drifts from price action and % to dollars."),
            ("Calculating what I still need this week or month. Excited, feeling back on the ball.",
             "Entries get less selective. Marginal setups start to look fine."),
            ("Imagining how others will see the trade. Want to talk about it and show off.",
             "Size creeping up. Justifying instead of assessing."),
            ("\"I could push the target further.\" Urge to change things.",
             "Profit target moved. First real deviation from the plan."),
            ("Don't want to give anything back. Irritable if asked about my trading.",
             "Tight trailing stops. At the screen when I don't need to be."),
            ("Can't stop thinking about the open trade. Hunched over, staring at live charts.",
             "Reacting to every tick or short-timeframe candle."),
            ("The trade feels personal: is the market with me or against me?",
             "Plan abandoned. Only a stop and target left as a safety net. Adding to winners."),
            ("Believe I can predict or control the market. Snappy with people.",
             "Oversized, over-leveraged, too many positions, re-entering straight after selling."),
            ("Must make the best possible return right now. No long-term thinking.",
             "No system, no risk limits. Micro-managing every candle."),
        ],
    },
    {
        'key': 'fear',
        'label': 'Fear',
        'color': '#4f63a8',
        'point': 'rect',
        'source': 'Deck slides 52-53',
        'levels': [
            ("Slight doubt: \"Was that the right decision? Is this a loser?\"",
             "Judgement slightly clouded. A market change reads as \"I did something wrong.\""),
            ("Checking the live trade more than needed. \"What if...\" thoughts begin.",
             "Less objective. Probabilistic thinking weakens."),
            ("Worrying about having to take the loss. Replaying recent losses.",
             "Emotional thinking about past losses drives the read."),
            ("Mind loops on the same questions without new answers.",
             "Second-guessing entries. Hunting for indicators outside my system."),
            ("Logging in to check how much I've lost. Heart rate up.",
             "Distrust my own strategy. Need reassurance from someone else."),
            ("Tension, trouble sleeping after bad days. Focus narrows to tunnel vision.",
             "Skipping valid setups. Sizing too small. Talking myself out of good trades."),
            ("Strong urge to move the stop to breakeven. Can't take another loss.",
             "Focused on guaranteed profit or getting back to even."),
            ("Need to take profit the moment it's green, to prove I can still do it.",
             "No longer thinking rationally. Exiting winners early."),
            ("Discomfort so high I snap, \"Screw it,\" and fire a trade to stop feeling it.",
             "Impulsive entries or exits to relieve the feeling, not to follow the plan."),
            ("Frozen or panicked, staring at the charts.",
             "Not thinking at all. Can't manage the position or the risk."),
        ],
    },
    {
        'key': 'tilt',
        'label': 'Tilt',
        'color': '#c23b3b',
        'point': 'triangle',
        'source': 'Deck slides 54-55',
        'levels': [
            ("Slight frustration. Gripping the mouse tighter, tension in the head.",
             "Still see good areas, but considering subpar trades to \"get on the board.\""),
            ("Impatient: \"Why is nothing presenting itself?\"",
             "Clicking around charts without real analysis."),
            ("Tension turns to heat. The loss feels unfair.",
             "Trading outside the areas I planned pre-market. Repeating the same losing trade."),
            ("Self-talk gets harsh. \"I can't believe this.\"",
             "Taking trades with less thought. Chasing: \"it can't go any further.\""),
            ("Fixated on getting the money back.",
             "Holding a loser past where I'd exit. Skipping the stop."),
            ("Fighting myself: \"stop now\" versus \"I can make this back.\"",
             "Increasing size to recover. Watching price only, not the chart."),
            ("Righteous: the market is rigged or out to get me. Cursing.",
             "Doubling a loser, trading one after another. The floodgates open."),
            ("Don't see risk, or see it and don't care.",
             "Ignoring risk limits. Revenge entries."),
            ("Toxic story on a loop about luck, stupidity or the market.",
             "No consideration. Clicking trades with no decision process."),
            ("Don't care. Wanting to quit. Might throw something.",
             "Gambling to the margin call. No process at all."),
        ],
    },
    {
        'key': 'low_confidence',
        'label': 'Low confidence',
        'color': '#0b5563',
        'point': 'rectRot',
        'source': 'Drafted from deck slides 16-17 and 22 (confidence levels 1-4)',
        'drafted': True,
        'levels': [
            ("Calm, with a touch of hesitation. A flicker of doubt about this trade.",
             "Still executing my plan."),
            ("Pessimistic. Assuming my open positions will lose.",
             "A bit hesitant, but still executing my plan."),
            ("Overfocused on P&L, balance or drawdown size. Wondering if the strategy stopped working.",
             "Hunting for perfect trades, so I take few. Overworried about reversals."),
            ("Self-critical and discouraged. Doubting my strategy.",
             "Little interest in finding setups. Can't find new ideas, or can't trust the ones I find."),
            ("Comparing myself with better traders. Embarrassed.",
             "Making excuses not to trade. Skipping trades, then seeing the ones I missed."),
            ("Beating myself up for not having what it takes. Past success feels like it means nothing.",
             "Switching systems hoping something works."),
            ("Negative self-talk takes over. Asking myself whether I'm any good.",
             "Getting creative: forcing trades and losing more."),
            ("Need a win fast to feel good enough again.",
             "Swinging for a home run: an extreme trade outside my system."),
            ("Want to give up, but still fighting.",
             "Barely trading, and doubting every decision I do make."),
            ("Knot in my stomach. I can't see how I'll ever make money again.",
             "Stop trading, or only watch the screen."),
        ],
    },
    {
        'key': 'overconfidence',
        'label': 'Overconfidence',
        'color': '#b0408a',
        'point': 'star',
        'source': 'Drafted from deck slides 15, 23 and 115 (confidence levels 5-10)',
        'drafted': True,
        'logic': "A winning streak means my strategy fits current conditions, not that I control the market. Stick strictly to standard sizing.",
        'levels': [
            ("Calm and confident. No extra chatter. Losses barely register.",
             "Stick easily to my plan while sensing what the market gives me."),
            ("Pleased after a win, but still see wins as probabilistic.",
             "Standard position sizing maintained. Routines kept."),
            ("Expect the next trade to work. Excited.",
             "Deciding faster and taking more risk than ideal."),
            ("Sure of direction. Losses feel like temporary blips.",
             "Less rigorous prep. Justifying marginal trades. Less focus at the charts."),
            ("Feeling superior to the market after a winning streak. Smirking.",
             "Skipping the pre-market checklist. Position size slightly above plan."),
            ("Everything I do is right. Not thinking about losses. Amped up, adrenaline pumping.",
             "Bigger positions. Harder to let go of trades and respect stops. More trades than usual."),
            ("Believing losses are impossible. Dismissing counter-signals and risk warnings.",
             "Risk expansion: moving stops wider or removing them."),
            ("Sure I've figured out the market. Can't admit mistakes. Dismissing advice and other traders.",
             "Refusing profit at target. Treating leverage as no extra risk. Skipping routines."),
            ("Total hubris. Feeling immune to market volatility.",
             "Catastrophic leverage. Averaging down heavily into losing positions."),
            ("Invincible and euphoric. Spending the money in my head.",
             "Pushing targets ever further, certain they'll hit."),
        ],
    },
    {
        'key': 'desperation',
        'label': 'Desperation',
        'color': '#131c26',
        'point': 'crossRot',
        'source': 'Drafted from deck slides 30-31, 42, 84 and 88 (described in words, no scale)',
        'drafted': True,
        'levels': [
            ("Slight unease about being red for the day. Checking P&L a little more often.",
             "Plan followed."),
            ("\"I need to make this back today\" starts to run in the background.",
             "Marginal setups begin to look acceptable."),
            ("Urgent wish to make it back on this trade. Pulse up, muscles tense.",
             "Taking trades just to get on the board. Size a little above plan."),
            ("Tunnel vision. Need proof right now that I can do this.",
             "Dropping to a lower timeframe. Chasing moves."),
            ("Greed, fear and anger flooding in at once. Reasoning struggles to keep up.",
             "Revenge entries. Bending my own rules."),
            ("\"Screw it\" thoughts. Don't want to feel this any longer.",
             "Moving stops. Holding losers and hoping."),
            ("Panic. Need certainty from somewhere.",
             "Switching systems or indicators mid-session. Second-guessing everything."),
            ("Reasoning shuts down. Watching myself trade without being able to stop.",
             "Doubling or tripling a losing position."),
            ("Will do almost anything to avoid a losing day.",
             "Firing off trades on a one-minute chart with no process."),
            ("Blackout. Nothing is left of the plan.",
             "Gambling toward the margin call. No process at all."),
        ],
    },
    {
        'key': 'boredom',
        'label': 'Boredom',
        'color': '#7a8794',
        'point': 'dash',
        'source': 'Deck slide 113 (banded: 1-3, 4-6, 7-8, 9-10)',
        'logic': "Boredom is the price of discipline. My job is not to trade; my job is to execute an edge.",
        'levels': _banded([
            (3, "Acceptance of market pace; zero urge to act without a signal. Relaxed posture, calm engagement, stepping away comfortably.",
                "Disciplined waiting; strict adherence to watchlists and plans."),
            (6, "Under-stimulated; feeling like time is being wasted. Restlessness, checking phone, switching chart timeframes.",
                "Lowering entry criteria; taking borderline or secondary setups."),
            (8, "Resentment toward inactivity; feeling compelled to trade. Tense posture, rapid scrolling, adding unnecessary indicators.",
                "Forcing positions in low-volume or chop zones without edge."),
            (10, "Total detachment from plan; seeking thrills and dopamine. Pacing, erratic mouse movements, ignoring risk parameters.",
                 "Reckless over-sized gambling on random non-watchlist assets."),
        ]),
    },
    {
        'key': 'impatience',
        'label': 'Impatience',
        'color': '#0f8a5f',
        'point': 'cross',
        'source': 'Deck slide 117 (banded: 1-3, 4-6, 7-8, 9-10)',
        'logic': "A missed move costs $0. A chased trade degrades my Risk-to-Reward, inflates my risk, and turns execution into a gamble.",
        'levels': _banded([
            (3, "Content to let price come to designated entry zones. Steady breathing, relaxed hands, comfortable waiting.",
                "Clean limit order execution at planned structural levels."),
            (6, "Anxiety seeing price move in desired direction without you. Leaning in, hovering cursor over order button, foot tapping.",
                "Early triggers; jumping the gun before full candle closure."),
            (8, "High FOMO; urgent need to jump into any expanding move. Elevated heart rate, tense shoulders, rapid clicking.",
                "Chasing price; buying breakout tops or selling breakdown bottoms."),
            (10, "Panic-driven execution; desperate need for immediate results. Violent mouse clicking, physical agitation, rapid breathing.",
                 "Hyperactive chasing; taking terrible Risk-to-Reward on extended moves."),
        ]),
    },
    {
        'key': 'overtrading',
        'label': 'Overtrading',
        'color': '#7c5cd6',
        'point': 'rectRounded',
        'source': 'Deck slide 119 (banded: 1-3, 4-6, 7-8, 9-10)',
        'logic': "More trades do not equal more money. They equal higher friction and lower edge. My job is to protect capital, not force volume.",
        'levels': _banded([
            (3, "Total process focus; zero urge to force unscripted volume. Hands off keys, calm posture, monitoring setups passively.",
                "Strictly executing defined setups according to plan parameters."),
            (6, "Urge to recover a loss or 'make back money' during the session. Frequently switching charts, hovering cursor, checking P&L.",
                "Lowering criteria; re-entering closed trades without fresh signals."),
            (8, "Refusing to accept a red session; treating the market as endless cash. Fast scrolling, multiple ticket windows open, refusing to leave.",
                "Flipping positions long/short rapidly on micro timeframes."),
            (10, "Revenge spiral; prefrontal cortex offline; acting purely on impulse. Complete physical agitation, impulsive clicking, pacing the room.",
                 "Doubling or tripling trade sizes on unanalyzed charts until blow-up."),
        ]),
    },
]

for _emotion in EMOTIONS:
    assert len(_emotion['levels']) == 10, _emotion['key']

EMOTION_KEYS = [e['key'] for e in EMOTIONS]


def clean_emotions(source):
    """Pulls {emotion_key: level 1-10} out of a form, JSON dict or stored dict.

    Accepts keys as `greed` or `emo_greed`. Blank, non-numeric and
    out-of-range values are left out, so "not rated" is simply absent.
    """
    cleaned = {}
    for key in EMOTION_KEYS:
        raw = source.get(key)
        if raw in (None, ''):
            raw = source.get('emo_' + key)
        try:
            level = int(raw)
        except (TypeError, ValueError):
            continue
        if 1 <= level <= 10:
            cleaned[key] = level
    return cleaned


def chart_meta():
    """What the dashboard chart needs: key, label, colour, marker shape."""
    return [
        {'key': e['key'], 'label': e['label'], 'color': e['color'], 'point': e['point']}
        for e in EMOTIONS
    ]
