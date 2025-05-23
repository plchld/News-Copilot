# News Copilot - Ελληνική Έκδοση

> **🇬🇷 Ελληνική πλατφόρμα νοημοσύνης ειδήσεων με AI - Εμπλουτισμένη κατανόηση για κάθε άρθρο**

---

## 🌟 Επισκόπηση

Το **News Copilot** είναι μια επαναστατική πλατφόρμα που μετατρέπει την εμπειρία ανάγνωσης ειδήσεων μέσω contextual AI ανάλυσης. Σχεδιασμένο ειδικά για ελληνικούς αναγνώστες, προσφέρει:

- 🚀 **Άμεση ανάλυση άρθρου** με έναν κλικ
- 📚 **Επεξήγηση όρων** - Κατανόηση τεχνικών όρων και ιστορικών αναφορών  
- 🌐 **Πλαίσιο & Ανάλυση** - Πρόσθετες πληροφορίες από άλλες πηγές
- 📖 **Καθαρή Προβολή** - Άρθρα χωρίς διαφημίσεις και διαχειριστές
- 🎓 **Προοδευτική Ανάλυση** - Έλεγχος γεγονότων, ανάλυση μεροληψίας, χρονολόγιο, απόψεις ειδικών

## 🏗️ Αρχιτεκτονική

### Frontend - Chrome Extension
- **Sidebar UI** - Ευφυής πλαϊνή μπάρα που δεν καλύπτει το περιεχόμενο
- **Progressive Intelligence** - Γρήγορα αρχικά αποτελέσματα με επιλογή για βαθύτερη ανάλυση
- **Reader Mode** - Αφαιρεί διαφημίσεις και ακαταστατότητα για καθαρή ανάγνωση

### Backend - Python Flask + Grok API
- **Intelligent Processing** - Εξαγωγή άρθρων με trafilatura
- **Multi-Modal Analysis** - Βασική ανάλυση + 4 βαθιές αναλύσεις
- **Live Search Integration** - Χρήση Grok API Live search
- **Citation Management** - Αυτόματη εξαγωγή και επαλήθευση πηγών

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
├── content_script.js (91KB) - Complete UI & reader mode
├── background.js (3.9KB)    - Message handling & API calls  
└── manifest.json           - Extension configuration
```

### Backend Stack  
```
├── explain_with_grok.py     - Flask server with Grok integration
├── prompts.py              - All analysis prompts in Greek
└── requirements: flask, flask-cors, trafilatura, openai
```

### Key Technical Features
- **Live Search Integration** - Grok API με real-time αναζήτηση
- **JSON Schema Responses** - Δομημένες απαντήσεις για όλες τις αναλύσεις
- **Progressive Loading** - Γρήγορα βασικά + επιλογή για βαθιά ανάλυση
- **Error Handling** - Graceful degradation και user feedback
- **Citation Verification** - Έλεγχος ότι οι πηγές περιέχουν το αναφερόμενο περιεχόμενο

## ⚙️ Εγκατάσταση & Χρήση

### 1. Backend Setup
```bash
# Clone repository
git clone https://github.com/yourusername/News-Copilot.git
cd News-Copilot

# Install dependencies
pip install flask flask-cors trafilatura openai python-dotenv

# Set environment variables
echo "XAI_API_KEY=your_xai_key_here" > .env

# Start server
python explain_with_grok.py --server
```

### 2. Chrome Extension Setup
1. Ανοίξτε Chrome → Extensions → Developer mode
2. Κάντε κλικ "Load unpacked" → Επιλέξτε φάκελο `extension/`
3. Επισκεφθείτε οποιοδήποτε ελληνικό άρθρο ειδήσεων
4. Κάντε κλικ στο κουμπί "Ανάλυση Άρθρου" ή πατήστε Ctrl/Cmd + Shift + A

### 3. Χρήση
- **Βασική Ανάλυση**: Άμεση με ένα κλικ
- **Προοδευτική Ανάλυση**: Επιλέξτε από τα 4 επιπλέον εργαλεία  
- **Reader Mode**: Κουμπί "Καθαρή Προβολή" για άρθρα χωρίς διαφημίσεις
- **Keyboard Shortcuts**: Ctrl/Cmd + Shift + A για toggle, Escape για κλείσιμο

## 🎯 Χαρακτηριστικά Σχεδίασης

### UI/UX Excellence
- **Non-intrusive Sidebar** - Δεν καλύπτει το περιεχόμενο άρθρου
- **Progressive Disclosure** - Βασικά insights αμέσως, advanced επιλογές
- **Greek-First Design** - Πλήρης εντοπίωση και font optimization
- **Mobile Responsive** - Λειτουργεί σε όλες τις συσκευές
- **Dark Mode Support** - Αυτόματη προσαρμογή στις προτιμήσεις συστήματος

### Performance Optimizations
- **Fast Initial Load** - <2s για βασική ανάλυση  
- **Lazy Loading** - Βαθιά ανάλυση μόνο όταν ζητηθεί
- **Intelligent Caching** - Αποθήκευση αποτελεσμάτων ανά session
- **Error Recovery** - Graceful handling σφαλμάτων δικτύου/API

## 📊 Supported Sources

### Ελληνικά News Sites (30+ Sites)
Το News Copilot υποστηρίζει όλα τα μεγάλα ελληνικά ειδησεογραφικά πορτάλ:

**Κύρια Ειδησεογραφικά Μέσα:**
- kathimerini.gr (Καθημερινή)
- tanea.gr (Τα Νέα)  
- protothema.gr (Πρώτο Θέμα)
- skai.gr (ΣΚΑΪ)
- tovima.gr (Το Βήμα)
- ethnos.gr (Έθνος)
- in.gr (in.gr)
- news247.gr (News 247)

**Οικονομικά & Business:**
- naftemporiki.gr (Ναυτεμπορική)
- capital.gr (Capital)

**Ηλεκτρονικά Μέσα:**
- iefimerida.gr (Η Εφημερίδα)
- newsbeast.gr (Newsbeast)
- cnn.gr (CNN Greece)
- ant1news.gr (ANT1 News)
- newsbomb.gr (News Bomb)
- enikos.gr (Ενικός.gr)
- newsit.gr (Newsit)
- onalert.gr (OnAlert)
- newpost.gr (NewPost)

**Εναλλακτικά & Πολιτικά:**
- efsyn.gr (Εφημερίδα των Συντακτών)
- avgi.gr (Αυγή)
- documento.gr (Documento)  
- liberal.gr (Liberal)
- thetoc.gr (TheTOC)
- zougla.gr (Zougla)
- contra.gr (Contra)
- dikaiologitika.gr (Δικαιολογητικά)

**Περιφερειακά:**
- makthes.gr (Μακθες - Θεσσαλονίκη)
- real.gr (Real.gr)
- star.gr (Star)

- Αυτόματη εξαγωγή περιεχομένου με trafilatura για όλες τις πηγές
- Intelligent content extraction που προσαρμόζεται σε κάθε site

### Analysis Sources  
- **Web Search**: Γενικές πληροφορίες και επαλήθευση
- **News Sources**: Ειδησεογραφικές πηγές για fact-checking
- **X/Twitter**: Απόψεις ειδικών και real-time insights

## 🔧 Configuration

### Environment Variables
```bash
XAI_API_KEY=your_xai_api_key      # Required for Grok API
FLASK_PORT=5000                   # Optional, default 5000
DEBUG_MODE=true                   # Optional, for development
```

### Extension Permissions
- `activeTab` - Πρόσβαση στο τρέχον tab  
- `storage` - Αποθήκευση ρυθμίσεων
- `http://localhost:5000/*` - Επικοινωνία με backend

## 🚦 API Endpoints

### Basic Analysis
```http
POST /augment
Content-Type: application/json
{
  "url": "https://example.com/article"
}
```

### Deep Analysis  
```http
POST /deep-analysis  
Content-Type: application/json
{
  "url": "https://example.com/article",
  "analysisType": "fact-check|bias|timeline|expert",
  "searchParams": { "sources": [...], "mode": "on" }
}
```

## 🔮 Roadmap

### Άμεσες Βελτιώσεις
- [ ] Offline mode για βασική ανάλυση
- [ ] Bulk analysis για πολλαπλά άρθρα  
- [ ] User preferences & customization
- [ ] Export reports (PDF, email)

### Μελλοντικές Λειτουργίες
- [ ] Real-time notifications για trending topics
- [ ] Social sharing με insights
- [ ] Journalist collaboration features
- [ ] AI-powered article recommendations

### Performance & Scale
- [ ] Redis caching για API responses
- [ ] Multi-language support επέκταση
- [ ] Cloud deployment (AWS/GCP)
- [ ] Rate limiting και abuse protection

## 🤝 Contributing

### Development Setup
```bash
# Frontend development
cd extension/
# Edit content_script.js for UI changes
# Edit background.js for API integration

# Backend development  
# Edit explain_with_grok.py for API logic
# Edit prompts.py for new analysis types
```

### Code Standards
- **JavaScript**: ES6+, meaningful variable names
- **Python**: PEP 8, type hints where helpful
- **Greek Text**: Proper Unicode handling, consistent terminology

## 📄 License

MIT License - Δείτε [LICENSE](LICENSE) για λεπτομέρειες

---

## 🙏 Acknowledgments

- **Grok AI** για την ισχυρή Live Search API
- **Trafilatura** για την αξιόπιστη εξαγωγή άρθρων  
- **Greek Media Landscape** για την έμπνευση και τις απαιτήσεις

---

**🔗 Links**: [Demo Video](#) | [Documentation](#) | [Support](#)

**🇬🇷 Φτιαγμένο με αγάπη για την ελληνική ειδησεογραφική κοινότητα** ❤️
