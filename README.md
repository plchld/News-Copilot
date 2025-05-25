# News Copilot - Ελληνική Έκδοση

> **🇬🇷 Ελληνική πλατφόρμα νοημοσύνης ειδήσεων με AI - Εμπλουτισμένη κατανόηση για κάθε άρθρο**

## 📢 Transparency Notice

News Copilot is committed to transparency in how it analyzes news. We minimize bias by:
- **No curated lists**: X Pulse finds relevant discussions organically, not from pre-selected accounts
- **Intelligent language detection**: Automatically includes international sources when topics have global relevance (EU, NATO, climate, etc.)
- **Transparent exclusions**: Any filtered sites are listed publicly (empty by default)

See our [Configuration Transparency Notice](config/README.md) for details on your rights as a user.

---

## 🚀 Beta User Quick Start Guide

Welcome, Beta User! This guide will help you quickly install and start using the News Copilot Chrome Extension. The backend services are hosted on Vercel, so you **do not** need to set up any local server, database, or authentication.

**Installation Steps:**

1.  **Download the Extension Files:**
    *   Clone this repository or download it as a ZIP file and unzip it. You'll only need the `extension/` folder.
    ```bash
    git clone https://github.com/yourusername/News-Copilot.git 
    # Or download and unzip the project
    ```

2.  **Load the Extension in Chrome:**
    *   Open Google Chrome.
    *   Navigate to `chrome://extensions`.
    *   Enable "Developer mode" (usually a toggle in the top-right corner).
    *   Click the "Load unpacked" button.
    *   Select the `extension/` folder from the files you downloaded/cloned.

3.  **Configure API Endpoint (If Necessary):**
    *   The extension should be pre-configured to use the production API.
    *   If you are provided with a specific API URL for beta testing, you might need to update it in the extension's options (if available) or by modifying the `extension/manifest.json` or `extension/background.js` to point to the correct production/beta API URL (e.g., `https://news-copilot.vercel.app`).
    *   **Default Production API URL**: `https://news-copilot.vercel.app` (This should be the target for beta users).

4.  **Start Using News Copilot:**
    *   Visit any supported Greek news article (see list below).
    *   Click the News Copilot extension icon in your Chrome toolbar.
    *   Authenticate using the magic link sent to your email. (You'll be prompted for your email on first use).
    *   Enjoy enhanced news reading!

**Providing Feedback:**
*   Your feedback is invaluable! Please report any issues, bugs, or suggestions via [Link to your preferred feedback channel - e.g., GitHub Issues, a specific email, or a beta feedback form].

---

## ✅ Supported Sites for Beta Testing

Το News Copilot υποστηρίζει όλα τα μεγάλα ελληνικά ειδησεογραφικά πορτάλ. Η ανάλυση λειτουργεί καλύτερα σε άρθρα με κυρίως κειμενικό περιεχόμενο.

**Κύρια Ειδησεογραφικά Μέσα:**
- kathimerini.gr, tanea.gr, protothema.gr, skai.gr, tovima.gr, ethnos.gr, in.gr, news247.gr

**Οικονομικά & Business:**
- naftemporiki.gr, capital.gr

**Ηλεκτρονικά Μέσα:**
- iefimerida.gr, newsbeast.gr, cnn.gr, ant1news.gr, newsbomb.gr, newsit.gr

**Εναλλακτικά & Πολιτικά:**
- efsyn.gr, avgi.gr, documento.gr, liberal.gr, tvxs.gr

*Δείτε το αρχείο `SUPPORTED_SITES.md` για την πλήρη, ενημερωμένη λίστα και τεχνικές λεπτομέρειες, καθώς και για πληροφορίες σχετικά με το πώς προσδιορίζεται η υποστήριξη.*

### Analysis Sources (Used by the AI)
- **Web Search**: Γενικές πληροφορίες και επαλήθευση
- **News Sources**: Ειδησεογραφικές πηγές για fact-checking
- **X/Twitter**: (Σύντομα "X Pulse") Για απόψεις και δημόσιο λόγο

---

## 🌟 Επισκόπηση

Το **News Copilot** είναι μια επαναστατική πλατφόρμα που μετατρέπει την εμπειρία ανάγνωσης ειδήσεων μέσω contextual AI ανάλυσης. Σχεδιασμένο ειδικά για ελληνικούς αναγνώστες, προσφέρει:

- 🚀 **Άμεση ανάλυση άρθρου** με έναν κλικ
- 📚 **Επεξήγηση όρων** - Κατανόηση τεχνικών όρων και ιστορικών αναφορών  
- 🌐 **Πλαίσιο & Ανάλυση** - Πρόσθετες πληροφορίες από άλλες πηγές
- 📖 **Καθαρή Προβολή** - Άρθρα χωρίς διαφημίσεις και διαχειριστές
- 🎓 **Προοδευτική Ανάλυση** - Έλεγχος γεγονότων, ανάλυση μεροληψίας, χρονολόγιο, απόψεις ειδικών
- 🔐 **Ασφαλής Αυθεντικοποίηση** - Supabase authentication με magic links (μέσω του Vercel backend)

## 🏗️ Αρχιτεκτονική

### Frontend - Chrome Extension
- **Sidebar UI** - Ευφυής πλαϊνή μπάρα που δεν καλύπτει το περιεχόμενο
- **Progressive Intelligence** - Γρήγορα αρχικά αποτελέσματα με επιλογή για βαθύτερη ανάλυση
- **Reader Mode** - Αφαιρεί διαφημίσεις και ακαταστατότητα για καθαρή ανάγνωση
- **Authentication UI** - Magic link authentication με Supabase integration

### Backend - Vercel API + Supabase
- **Modular Flask API** - Structured API with separate modules (`api/` directory)
- **Intelligent Processing** - Εξαγωγή άρθρων με trafilatura
- **Multi-Modal Analysis** - Βασική ανάλυση + 4 βαθιές αναλύσεις
- **Live Search Integration** - Χρήση Grok API Live search
- **Citation Management** - Αυτόματη εξαγωγή και επαλήθευση πηγών
- **User Management** - Complete authentication system with rate limiting
- **Scalable Deployment** - Production-ready Vercel serverless functions

### 🚀 NEW: Agentic Intelligence Architecture
- **Parallel Agent Execution** - 3x faster analysis through concurrent processing
- **Dynamic Model Selection** - Automatic model optimization (grok-3-mini for simple, grok-3 for complex)
- **Nested Agent Systems** - X Pulse uses 5 specialized sub-agents working together
- **Quality Control** - Automated refinement for subpar results
- **Cost Optimization** - Strategic use of models reduces costs by ~40%

### Authentication & User Management
- **Supabase Backend** - Enterprise-grade authentication and database (managed by the deployed backend)
- **Magic Link Auth** - Passwordless authentication via email
- **JWT Tokens** - Secure token-based authentication
- **Rate Limiting** - Tiered usage limits (10 free, 50 premium, unlimited admin)
- **User Profiles** - Complete user management with email verification

## 🚀 Λειτουργίες

### 📚 Βασική Ανάλυση (Γρήγορη)
- **Επεξήγηση Όρων**: Αυτόματη εντόπιση και εξήγηση τεχνικών όρων, οργανισμών, ιστορικών αναφορών
- **Πλαίσιο & Ανάλυση**: Πρόσθετες πληροφορίες από άλλες έγκυρες πηγές
- **Highlighting**: Επισήμανση όρων στο άρθρο με tooltips
- **Citations**: Παρακολούθηση και εμφάνιση πηγών πληροφοριών

### 🔬 Προοδευτική Ανάλυση (Βαθιά)

#### ✔️ Έλεγχος Γεγονότων
- Επαλήθευση κύριων ισχυρισμών με live web search
- Scoring αξιοπιστίας (υψηλή/μέτρια/χαμηλή)
- Εντοπισμός προειδοποιήσεων και ασυνεπειών
- Συγκεκριμένες πηγές επαλήθευσης

#### ⚖️ Ανάλυση Μεροληψίας
- Ανίχνευση πολιτικής κλίσης (αριστερά/κεντροαριστερά/κέντρο/κεντροδεξιά/δεξιά)
- Ανάλυση συναισθηματικού τόνου (θετικός/ουδέτερος/αρνητικός)
- Εντοπισμός φορτισμένων λέξεων και framing
- Σύγκριση με άλλες πηγές

#### 📅 Χρονολόγιο Εξελίξεων  
- Δημιουργία timeline της ιστορίας
- Ιστορικό πλαίσιο και προηγούμενα γεγονότα
- Εκτίμηση μελλοντικών εξελίξεων
- Βαθμολογία σπουδαιότητας γεγονότων

#### 🎓 Απόψεις Ειδικών
- Εντοπισμός εμπειρογνωμόνων από X/Twitter και ειδησεογραφικές πηγές
- Συλλογή πραγματικών αποσπασμάτων και απόψεων
- Ανάλυση stance (υποστηρικτική/αντίθετη/ουδέτερη)
- Reliability scoring βάσει πληροφοριών πηγής

### 📖 Reader Mode (Καθαρή Προβολή)
- **Intelligent Content Extraction** - Αυτόματη εξαγωγή κύριου περιεχομένου
- **Aggressive Cleaning** - Αφαίρεση διαφημίσεων, navigation, social clutter
- **Beautiful Typography** - Magazine-style layout με βελτιωμένη τυπογραφία
- **Seamless Toggle** - Άμεση εναλλαγή κανονικής/καθαρής προβολής

## 🛠️ Τεχνική Υλοποίηση

### Chrome Extension Stack
```
extension/
├── content_script_clean.js      - Complete UI & reader mode
├── background.js                - Message handling & API calls  
├── popup-auth.html/js          - Simple authentication popup
├── popup-supabase.html/js      - Full Supabase authentication UI
├── manifest.json               - Extension configuration
└── css/content_styles.css      - Extension styling
```

### Backend API Stack (Deployed on Vercel)
```
api/
├── index.py                    - Vercel entry point
├── app.py                      - Flask application setup
├── routes.py                   - Main analysis endpoints
├── auth_routes.py              - Authentication endpoints
├── admin_auth.py               - Admin authentication
├── models.py                   - Database models and schemas
├── analysis_handlers.py        - AI analysis processing
├── grok_client.py              - Grok API integration
├── article_extractor.py        - Content extraction
├── supabase_auth.py            - Supabase authentication
├── http_supabase.py            - Supabase HTTP client
├── email_verification.py       - Email verification system
├── config.py                   - Configuration management
└── agents/                     - NEW: Agentic intelligence system
    ├── base_agent.py           - Base agent classes with model selection
    ├── coordinator.py          - Orchestrates parallel agent execution
    ├── jargon_agent.py         - Term explanation agent (grok-3-mini)
    ├── viewpoints_agent.py     - Alternative perspectives agent
    ├── fact_check_agent.py     - Claim verification agent
    ├── bias_agent.py           - Political bias analysis agent
    ├── timeline_agent.py       - Event chronology agent
    ├── expert_agent.py         - Expert opinions agent
    └── x_pulse_agent.py        - X discourse analysis (nested agents)
```

### Testing Infrastructure
```
tests/
├── conftest.py                 - Test configuration
├── test_routes.py              - API endpoint tests
├── test_analysis_handlers.py   - Analysis logic tests
├── test_grok_client.py         - Grok API tests
├── test_article_extractor.py   - Content extraction tests
└── __init__.py                 - Test package
```

### Supporting Files
```
├── run_tests.py                - Test runner with coverage
├── pytest.ini                 - Pytest configuration
├── setup_admin.py              - Admin user setup
├── setup_test_env.py           - Test environment setup
├── supabase_schema.sql         - Database schema
├── SUPABASE_SETUP.md           - Complete setup guide
├── CLAUDE.md                   - Development documentation
└── SUPPORTED_SITES.md          - Supported sites list
```

### Key Technical Features
- **Live Search Integration** - Grok API με real-time αναζήτηση
- **JSON Schema Responses** - Δομημένες απαντήσεις για όλες τις αναλύσεις
- **Progressive Loading** - Γρήγορα βασικά + επιλογή για βαθιά ανάλυση
- **Error Handling** - Comprehensive error handling και user feedback
- **Citation Verification** - Έλεγχος ότι οι πηγές περιέχουν το αναφερόμενο περιεχόμενο
- **Serverless Architecture** - Scalable Vercel deployment
- **Database Security** - Row Level Security (RLS) policies
- **Agentic Intelligence** - Parallel agent execution with smart model selection
- **Nested Agent Systems** - Complex analyses using multiple specialized sub-agents
- **Quality Assurance** - Automated quality checks and refinement loops

## ⚙️ Εγκατάσταση & Χρήση

### 1. Environment Setup
```bash
# Clone repository
git clone https://github.com/yourusername/News-Copilot.git
cd News-Copilot

# Install dependencies
pip install -r requirements.txt

# Set environment variables (.env file)
XAI_API_KEY=your_xai_key_here
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=your_anon_key
SUPABASE_SERVICE_KEY=your_service_key
BASE_URL=http://localhost:8080  # For local development
```

### 2. Supabase Setup
```bash
# Follow complete setup guide
cat SUPABASE_SETUP.md

# Create database schema
# Run supabase_schema.sql in your Supabase SQL editor

# Setup admin user
python setup_admin.py

# Test authentication
python setup_test_env.py
```

### 3. Backend Development
```bash
# Start local development server
python explain_with_grok.py --server

# Run tests with coverage
python run_tests.py

# Test specific components
pytest tests/test_routes.py -v
pytest tests/test_analysis_handlers.py -v
```

### 4. Chrome Extension Setup
1. Ανοίξτε Chrome → Extensions → Developer mode
2. Κάντε κλικ "Load unpacked" → Επιλέξτε φάκελο `extension/`
3. Επισκεφθείτε οποιοδήποτε ελληνικό άρθρο ειδήσεων
4. Κάντε κλικ στο extension icon για authentication
5. Χρησιμοποιήστε magic link για σύνδεση

### 5. Production Deployment
```bash
# Deploy to Vercel
git add .
git commit -m "Deploy to production"
git push

# Set environment variables in Vercel dashboard
# Update extension manifest.json to use production URL
```

### 6. Χρήση
- **Authentication**: Magic link μέσω email (10 δωρεάν αναλύσεις/μήνα)
- **Βασική Ανάλυση**: Άμεση με ένα κλικ
- **Προοδευτική Ανάλυση**: Επιλέξτε από τα 4 επιπλέον εργαλεία  
- **Reader Mode**: Κουμπί "Καθαρή Προβολή" για άρθρα χωρίς διαφημίσεις
- **Admin Functions**: Unlimited usage for admin users

## 🚦 API Endpoints

### Authentication Endpoints
```http
POST /api/auth/login
Content-Type: application/json
{
  "email": "user@example.com"
}

GET /api/auth/profile
Authorization: Bearer <jwt_token>

POST /api/auth/logout
Authorization: Bearer <jwt_token>
```

### Analysis Endpoints
```http
POST /augment
Content-Type: application/json
Authorization: Bearer <jwt_token>
{
  "url": "https://example.com/article"
}

POST /augment-stream
Content-Type: application/json
Authorization: Bearer <jwt_token>
{
  "url": "https://example.com/article"
}

POST /deep-analysis  
Content-Type: application/json
Authorization: Bearer <jwt_token>
{
  "url": "https://example.com/article",
  "analysisType": "fact-check|bias|timeline|expert",
  "searchParams": { "sources": [...], "mode": "on" }
}
```

### Admin Endpoints
```http
GET /api/admin/users
Authorization: Bearer <admin_jwt_token>

GET /api/admin/usage-stats
Authorization: Bearer <admin_jwt_token>

POST /api/admin/update-user-tier
Authorization: Bearer <admin_jwt_token>
{
  "userId": "uuid",
  "tier": "free|premium|admin"
}
```

## 🧪 Testing & Code Quality

### Development Tools Setup
```bash
# Install development dependencies
pip install -r requirements.txt

# Install pre-commit hooks
pre-commit install
```

### Code Quality Tools

#### Python Linting & Formatting
- **Black**: Automatic code formatting (88 char line length)
- **Ruff**: Fast Python linter checking for errors and style issues

```bash
# Format Python code automatically
black api/

# Check for linting issues
ruff check api/

# Fix auto-fixable issues
ruff check --fix api/
```

#### Chrome Extension Validation
The project includes a custom validation script for the Chrome extension:

```bash
# Validate extension structure and syntax
python validate_extension.py
```

This checks:
- ✅ manifest.json validity
- ✅ Content script syntax (brace/parenthesis matching)
- ✅ Required file presence
- ✅ API endpoint references
- ✅ Security issues (eval, innerHTML usage)
- ✅ Chrome API usage patterns

### Pre-commit Hooks
Automatic checks before each commit:
- Trailing whitespace removal
- End of file fixing
- JSON syntax validation
- Python formatting with Black
- Python linting with Ruff

### Quick Commands (Makefile)
```bash
make install   # Install dependencies
make lint      # Run all linting checks
make format    # Auto-format code
make test      # Run Python tests
make validate  # Validate Chrome extension
make clean     # Clean cache files
make run       # Start local server
```

### Run All Tests
```bash
# Complete test suite with coverage
python run_tests.py

# Or directly with pytest
pytest --cov=api --cov-report=term-missing
```

### Specific Test Categories
```bash
# API endpoint tests
pytest tests/test_routes.py -v

# Analysis logic tests
pytest tests/test_analysis_handlers.py -v

# Authentication tests
pytest tests/test_grok_client.py -v

# Content extraction tests
pytest tests/test_article_extractor.py -v

# Run tests by marker
pytest -m "not slow"  # Skip slow tests
pytest -m unit        # Run only unit tests
```

### Manual Testing
```bash
# Test CLI mode
python explain_with_grok.py <article_url>

# Test authentication system
python setup_test_env.py

# Test supported sites
python -c "from tests.test_sites import test_all_sites; test_all_sites()"
```

### CI/CD (GitHub Actions)
The project includes GitHub Actions workflows that run on every pull request:
- Python linting (Black, Ruff)
- Python tests with coverage
- Chrome extension validation
- Vercel deployment checks

All checks must pass before merging to main branch.

## 📊 Supported Sources

### Ελληνικά News Sites (50+ Sites)
Το News Copilot υποστηρίζει όλα τα μεγάλα ελληνικά ειδησεογραφικά πορτάλ:

**Κύρια Ειδησεογραφικά Μέσα:**
- kathimerini.gr, tanea.gr, protothema.gr, skai.gr, tovima.gr, ethnos.gr, in.gr, news247.gr

**Οικονομικά & Business:**
- naftemporiki.gr, capital.gr

**Ηλεκτρονικά Μέσα:**
- iefimerida.gr, newsbeast.gr, cnn.gr, ant1news.gr, newsbomb.gr, newsit.gr

**Εναλλακτικά & Πολιτικά:**
- efsyn.gr, avgi.gr, documento.gr, liberal.gr, tvxs.gr

*Δείτε `SUPPORTED_SITES.md` για πλήρη λίστα και τεχνικές λεπτομέρειες*

### Analysis Sources  
- **Web Search**: Γενικές πληροφορίες και επαλήθευση
- **News Sources**: Ειδησεογραφικές πηγές για fact-checking
- **X/Twitter**: Απόψεις ειδικών και real-time insights

## 🔧 Configuration

### Environment Variables
```bash
# Required
XAI_API_KEY=your_xai_api_key          # Grok API access
SUPABASE_URL=https://xxx.supabase.co  # Supabase project URL
SUPABASE_ANON_KEY=xxx                 # Public Supabase key
SUPABASE_SERVICE_KEY=xxx              # Service role key

# Optional
BASE_URL=https://news-copilot.vercel.app  # Production URL
FLASK_PORT=8080                           # Local development port
DEBUG_MODE=true                           # Development mode
```

### Extension Permissions
- `activeTab` - Πρόσβαση στο τρέχον tab  
- `scripting` - Content script injection
- `storage` - Αποθήκευση authentication tokens
- `https://news-copilot.vercel.app/*` - Production API
- `https://*.supabase.co/*` - Supabase authentication

### User Tiers & Rate Limiting
- **Free Tier**: 10 αναλύσεις/μήνα
- **Premium Tier**: 50 αναλύσεις/μήνα  
- **Admin Tier**: Unlimited αναλύσεις

## 🔮 Roadmap

### Άμεσες Βελτιώσεις
- [ ] Offline mode για βασική ανάλυση
- [ ] Bulk analysis για πολλαπλά άρθρα  
- [ ] Enhanced user dashboard
- [ ] Export reports (PDF, email)
- [ ] Browser extension for Firefox & Safari

### Μελλοντικές Λειτουργίες
- [ ] Real-time notifications για trending topics
- [ ] Social sharing με insights
- [ ] Journalist collaboration features
- [ ] AI-powered article recommendations
- [ ] Multi-language support expansion

### Performance & Scale
- [ ] Redis caching για API responses
- [ ] CDN integration για static assets
- [ ] Advanced monitoring και analytics
- [ ] Load balancing για high traffic

## 🤝 Contributing

### Development Setup
```bash
# Backend development
cd api/
# Edit specific modules in api/ directory
# Add new analysis types in analysis_handlers.py
# Update prompts in prompts.py

# Frontend development
cd extension/
# Edit content_script_clean.js for UI changes
# Edit background.js for API integration
# Update popup files for authentication changes

# Testing
# Add tests in tests/ directory
# Run test suite before committing
python run_tests.py
```

### Code Standards
- **JavaScript**: ES6+, meaningful variable names
- **Python**: PEP 8, type hints, comprehensive docstrings
- **Greek Text**: Proper Unicode handling, consistent terminology
- **Testing**: Minimum 80% test coverage for new features
- **API**: RESTful design, proper HTTP status codes

### Adding New Features
1. **New Analysis Types**: Add to `analysis_handlers.py` and `prompts.py`
2. **New Sites**: Update `manifest.json` and test with extraction
3. **UI Changes**: Test across different screen sizes and themes
4. **Database Changes**: Update `supabase_schema.sql` and migrations

## 📄 License

MIT License - Δείτε [LICENSE](LICENSE) για λεπτομέρειες

---

## 🙏 Acknowledgments

- **Grok AI** για την ισχυρή Live Search API
- **Trafilatura** για την αξιόπιστη εξαγωγή άρθρων  
- **Supabase** για την enterprise-grade authentication platform
- **Vercel** για την άψογη serverless deployment experience
- **Greek Media Landscape** για την έμπνευση και τις απαιτήσεις

---

**🔗 Links**: [Live Demo](https://news-copilot.vercel.app) | [Documentation](CLAUDE.md) | [Setup Guide](SUPABASE_SETUP.md)

**🇬🇷 Φτιαγμένο με αγάπη για την ελληνική ειδησεογραφική κοινότητα** ❤️
