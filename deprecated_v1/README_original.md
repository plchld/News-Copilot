# News Copilot 🌅

> Ελληνική Νοημοσύνη για την Ειδησεογραφία | Greek Intelligence for News

Το News Copilot είναι μια web πλατφόρμα που παρέχει εμβαθυμένη, AI-powered ανάλυση για ελληνικά άρθρα ειδήσεων. Χρησιμοποιώντας το Grok AI με δυνατότητες live search, προσφέρει επτά τύπους ανάλυσης για βαθύτερη κατανόηση του περιεχομένου.

## 🚀 Γρήγορη Εκκίνηση

### Για Χρήστες
1. Επισκεφθείτε το [News Copilot Web App](https://news-copilot.vercel.app)
2. Δημιουργήστε δωρεάν λογαριασμό με το email σας
3. Επικολλήστε έναν σύνδεσμο από ελληνικό site ειδήσεων
4. Λάβετε άμεση AI ανάλυση με επτά διαφορετικές οπτικές

Δεν απαιτείται εγκατάσταση - λειτουργεί σε όλους τους browsers!

### Για Developers

#### Backend API Setup
```bash
# Clone the repository
git clone https://github.com/yourusername/news-copilot.git
cd news-copilot

# Install dependencies
pip install -r requirements.txt

# Set up environment variables
cp .env.example .env  # Edit with your API keys

# Start the development server
python api/app.py
```

#### Web App Setup (Next.js - Coming Soon)
```bash
# Navigate to web app directory
cd web-app

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build
npm start
```

## 🎯 Χαρακτηριστικά

### Επτά Τύποι Ανάλυσης
1. **🔍 Όροι (Jargon)**: Επεξήγηση σύνθετων όρων και εννοιών
2. **👥 Οπτικές (Viewpoints)**: Εναλλακτικές προσεγγίσεις του θέματος
3. **✅ Fact-Check**: Επαλήθευση ισχυρισμών με πηγές
4. **⚖️ Προκατάληψη (Bias)**: Ανάλυση πολιτικής τοποθέτησης
5. **📅 Χρονολόγιο (Timeline)**: Ιστορικό πλαίσιο γεγονότων
6. **🎓 Ειδικοί (Expert)**: Απόψεις ειδημόνων με @username
7. **🐦 X Pulse**: Ανάλυση του διαλόγου στο X (Twitter)

### Υποστηριζόμενα Sites
50+ ελληνικά sites ειδήσεων συμπεριλαμβανομένων:
- **Mainstream**: kathimerini.gr, tanea.gr, protothema.gr, in.gr
- **Business**: naftemporiki.gr, capital.gr, euro2day.gr
- **Digital**: iefimerida.gr, newsbeast.gr, cnn.gr
- **Alternative**: efsyn.gr, avgi.gr, documento.gr
- **Regional**: makthes.gr, thestival.gr

[Δείτε την πλήρη λίστα](SUPPORTED_SITES.md)

## 🏗️ Αρχιτεκτονική

### Frontend - Next.js Web Application (Coming Soon)
```
web-app/
├── app/                    # Next.js 14 app directory
├── components/            # React components
├── hooks/                # Custom React hooks
├── lib/                  # Utilities and helpers
├── public/               # Static assets
└── styles/              # CSS modules
```

- **Modern Web Stack**: React 18, Next.js 14, TypeScript
- **Responsive Design**: Mobile-first approach
- **Real-time Updates**: Server-Sent Events for progress
- **Authentication**: Supabase Auth integration

### Backend - Python Flask API
```
api/
├── agents/               # Agentic AI system
├── app.py               # Flask application
├── routes.py            # API endpoints
├── analysis_handlers.py # Core analysis logic
├── grok_client.py       # Grok AI integration
└── supabase_auth.py     # Authentication
```

- **AI Integration**: Grok API με live search
- **Async Processing**: Parallel agent execution
- **Authentication**: JWT tokens και rate limiting
- **Content Extraction**: Trafilatura για 50+ sites

### Database - Supabase
- PostgreSQL με Row Level Security
- Magic link authentication
- User tiers: free (10/μήνα), premium (50/μήνα), admin (unlimited)

## 🔧 Technical Implementation

### API Endpoints
```
POST /augment         # Basic analysis (jargon + viewpoints)
POST /augment-stream  # Streaming analysis με SSE
POST /deep-analysis   # Full 7-type analysis

GET  /api/auth/profile    # User profile και usage
POST /api/auth/login      # Magic link login
POST /api/auth/logout     # Session logout
```

### Agentic Intelligence System
Το σύστημα χρησιμοποιεί specialized agents για κάθε τύπο ανάλυσης:

```python
# Agent coordination με parallel execution
agents = [
    JargonAgent(),      # grok-3-mini (cost-optimized)
    ViewpointsAgent(),  # grok-3
    FactCheckAgent(),   # grok-3
    BiasAgent(),        # grok-3
    TimelineAgent(),    # grok-3
    ExpertAgent(),      # grok-3
    XPulseAgent()       # grok-3 με 5 sub-agents
]
```

### Response Formats
Όλες οι απαντήσεις ακολουθούν structured JSON schemas:

```typescript
interface JargonTerm {
  term: string;
  explanation: string;
  link?: string;
}

interface ViewpointItem {
  title: string;
  description: string;
  source?: string;
}
```

## 🚀 Deployment

### Backend API (Vercel)
```bash
# Deploy to Vercel
vercel

# Set environment variables
vercel env add XAI_API_KEY
vercel env add SUPABASE_URL
vercel env add SUPABASE_ANON_KEY
vercel env add SUPABASE_SERVICE_KEY
```

### Web App (Vercel/Netlify)
```bash
# Build the web app
cd web-app
npm run build

# Deploy to Vercel
vercel --prod

# Or deploy to Netlify
netlify deploy --prod
```

## 🔐 Authentication Setup

1. Create Supabase project
2. Run schema από `supabase_schema.sql`
3. Configure email templates
4. Set environment variables
5. Test με `python test_auth_system.py`

[Δείτε το πλήρες guide](SUPABASE_SETUP.md)

## 🧪 Testing

```bash
# Run all tests με coverage
python run_tests.py

# Test specific module
pytest tests/test_routes.py -v

# Test supported sites
python test_sites.py

# Test authentication
python test_auth_system.py
```

## 📊 Performance

- **Analysis Speed**: 3-5 seconds με parallel agents
- **Extraction Success**: 95%+ για supported sites  
- **API Latency**: <200ms για cached content
- **Concurrent Users**: 100+ με rate limiting

## 🤝 Contributing

1. Fork το repository
2. Create feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit changes (`git commit -m 'Add AmazingFeature'`)
4. Push to branch (`git push origin feature/AmazingFeature`)
5. Open Pull Request

### Development Guidelines
- Όλα τα prompts και responses στα Ελληνικά
- Χρήση type hints και docstrings
- Tests για νέα features
- Follow existing code style

## 📝 Roadmap

- [x] Core analysis engine
- [x] Supabase authentication
- [x] 50+ Greek news sites support
- [x] Parallel agent execution
- [x] Web application interface
- [ ] Social media integration
- [ ] Historical analysis archive
- [ ] Mobile applications (iOS/Android)
- [ ] Public API για developers
- [ ] Custom analysis templates

## 📄 License

Αυτό το project είναι licensed under the MIT License - δείτε το [LICENSE](LICENSE) file για details.

## 🙏 Acknowledgments

- **Grok AI** by xAI για την πανίσχυρη language understanding
- **Supabase** για το excellent auth και database infrastructure
- **Trafilatura** για reliable article extraction
- **Vercel** για seamless deployment

---

<div align="center">
  <p>Φτιαγμένο με ❤️ για την Ελληνική δημοσιογραφία</p>
  <p>Ερωτήσεις; Ανοίξτε ένα <a href="https://github.com/yourusername/news-copilot/issues">issue</a></p>
</div>