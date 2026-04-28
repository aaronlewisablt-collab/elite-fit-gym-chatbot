from flask import Flask, request, jsonify, send_from_directory
import os, json, requests as req

app = Flask(__name__, static_folder='static')

OPENAI_API_KEY = os.environ.get("OPENAI_API_KEY", "")
OPENAI_URL = "https://api.openai.com/v1/chat/completions"

# In-memory session store
sessions = {}

SYSTEM_PROMPT = """You are a friendly and professional sales assistant for Elite Fit Gym. Your name is Alex. Your goal is to:
1. Answer questions about the gym warmly and helpfully
2. Naturally qualify leads by gathering: name, email, and what they're looking for
3. Encourage visitors to book a FREE 1-day trial pass
4. Keep responses concise (2-4 sentences) and always end with a question

BUSINESS KNOWLEDGE BASE:

Business: Elite Fit Gym | Location: 12 Fitness Lane, Central London, EC1A 1BB
Nearest Tube: Barbican (2 min walk) | Phone: 020 7123 4567 | Email: info@elitefitgym.co.uk

MEMBERSHIPS & PRICING:
- Monthly: £30/month (full access, all equipment, locker rooms)
- Annual: £299/year (saves £61 vs monthly)
- Personal Training: £40/session | 5 sessions £180 | 10 sessions £340
- Group Classes: FREE with membership (Yoga, HIIT, Strength, Spin, Pilates, Boxing)
- Student Discount: 20% off with valid student ID
- No joining fee ever

OPENING HOURS:
Mon-Fri: 6am-10pm | Sat: 8am-8pm | Sun: 9am-6pm | Bank Holidays: 9am-4pm

FREE TRIAL: Yes! FREE 1-day pass, no credit card. Walk in or book online.

CANCELLATION: 30 days notice for monthly. Freeze up to 3 months/year at no cost.

FACILITIES: Free weights (to 50kg), cardio zone, functional training, 2 class studios, sauna, steam room, showers, lockers, towels included, protein bar, free WiFi, free parking (limited).

PERSONAL TRAINING: Level 3 certified PTs. Free initial consultation. Specialisms: weight loss, muscle building, sports performance, rehab, pre/post natal. Online coaching available.

GROUP CLASSES (Sample): Mon: 7am Yoga, 12pm HIIT, 6pm Strength | Tue: 7am Spin, 1pm Pilates, 7pm Boxing | Wed: 7am HIIT, 12pm Yoga, 6pm Strength | Thu: 7am Spin, 1pm HIIT, 7pm Pilates | Fri: 7am Strength, 12pm Yoga, 6pm HIIT | Sat: 9am Yoga, 10:30am HIIT, 12pm Boxing | Sun: 10am Stretch, 11:30am Pilates

KEY FAQs:
- Towels: Provided free | Guests: 1 free/month, extra £5 | No joining fee
- Beginners: Absolutely welcome, free induction session
- Pool: No pool, but partner leisure centre 5 mins away with member discounts
- Nutrition: Basic advice from PTs, nutritionist consultations £50/session

TONE: Warm, enthusiastic, natural. Never robotic. Always end with a follow-up question."""

@app.route('/')
def index():
    return send_from_directory('static', 'index.html')

@app.route('/chat', methods=['POST', 'OPTIONS'])
def chat():
    if request.method == 'OPTIONS':
        response = jsonify({'status': 'ok'})
        response.headers.add('Access-Control-Allow-Origin', '*')
        response.headers.add('Access-Control-Allow-Headers', 'Content-Type')
        response.headers.add('Access-Control-Allow-Methods', 'POST')
        return response

    data = request.get_json()
    message = data.get('message', '')
    session_id = data.get('sessionId', 'default')

    if not message:
        return jsonify({'error': 'No message provided'}), 400

    # Get or create session history
    if session_id not in sessions:
        sessions[session_id] = [{"role": "system", "content": SYSTEM_PROMPT}]

    sessions[session_id].append({"role": "user", "content": message})

    # Keep last 20 messages to avoid token overflow
    history = [sessions[session_id][0]] + sessions[session_id][-19:]

    try:
        r = req.post(
            OPENAI_URL,
            headers={
                "Authorization": f"Bearer {OPENAI_API_KEY}",
                "Content-Type": "application/json"
            },
            json={
                "model": "gpt-4o-mini",
                "messages": history,
                "max_tokens": 300,
                "temperature": 0.7
            },
            timeout=30
        )
        r.raise_for_status()
        reply = r.json()["choices"][0]["message"]["content"]
        sessions[session_id].append({"role": "assistant", "content": reply})

        resp = jsonify({'response': reply, 'sessionId': session_id})
        resp.headers.add('Access-Control-Allow-Origin', '*')
        return resp

    except Exception as e:
        resp = jsonify({'error': str(e)})
        resp.headers.add('Access-Control-Allow-Origin', '*')
        return resp, 500

@app.route('/reset', methods=['POST'])
def reset():
    data = request.get_json()
    session_id = data.get('sessionId', 'default')
    if session_id in sessions:
        del sessions[session_id]
    resp = jsonify({'status': 'reset'})
    resp.headers.add('Access-Control-Allow-Origin', '*')
    return resp

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5680))
    app.run(host='0.0.0.0', port=port, debug=False)
