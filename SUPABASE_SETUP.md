# 🚀 Supabase Setup Guide for News Copilot

## Step 1: Create Supabase Project

1. **Go to [supabase.com](https://supabase.com)**
2. **Sign up/Login** with GitHub
3. **Create New Project**
   - Organization: Your organization
   - Name: `news-copilot`
   - Database Password: Generate strong password
   - Region: Choose closest to your users (e.g., `eu-west-1` for Europe)

## Step 2: Configure Database

1. **Go to SQL Editor** in your Supabase dashboard
2. **Run the schema script:**
   - Copy the contents of `supabase_schema.sql`
   - Paste and execute in SQL Editor
   - This creates all necessary tables and security policies

## Step 3: Get API Keys

1. **Go to Settings > API**
2. **Copy these values:**
   ```
   Project URL: https://your-project.supabase.co
   anon/public key: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   service_role key: eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
   ```

## Step 4: Update Environment Variables

### For Vercel Deployment:
```bash
# Supabase Configuration
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...

# Existing Variables
XAI_API_KEY=your_grok_api_key
BASE_URL=https://news-copilot.vercel.app
```

### For Local Development (.env):
```bash
SUPABASE_URL=https://your-project.supabase.co
SUPABASE_ANON_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
SUPABASE_SERVICE_KEY=eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
XAI_API_KEY=your_grok_api_key
BASE_URL=http://localhost:8080
```

## Step 5: Update Chrome Extension

1. **Update `extension/js/supabase-auth.js`:**
   - Replace `'https://your-project.supabase.co'` with your actual URL
   - Replace `'your-anon-key'` with your actual anon key

2. **Update manifest.json** to use the new popup:
   ```json
   {
     "action": {
       "default_popup": "popup-supabase.html"
     }
   }
   ```

## Step 6: Configure Email Templates (Optional)

1. **Go to Authentication > Templates**
2. **Customize email templates:**
   - Confirm signup
   - Magic Link
   - Password recovery

3. **Example Magic Link Template:**
   ```html
   <h2>Welcome to News Copilot!</h2>
   <p>Click the link below to sign in:</p>
   <p><a href="{{ .ConfirmationURL }}">Sign in to News Copilot</a></p>
   <p>Enjoy 10 free analyses per month!</p>
   ```

## Step 7: Set Up Admin User

1. **Go to Authentication > Users**
2. **Create admin user manually:**
   - Email: your-admin@example.com
   - Auto-confirm: Yes
   - Email confirm: Yes

3. **Update user profile in SQL Editor:**
   ```sql
   INSERT INTO public.user_profiles (user_id, email, tier, email_verified)
   VALUES (
     'admin-user-id-from-auth-table',
     'your-admin@example.com',
     'admin',
     true
   );
   ```

## Step 8: Test Authentication

### Backend Test:
```bash
# Install dependencies
pip install -r requirements.txt

# Run locally
python explain_with_grok.py --server

# Test auth endpoint
curl -X GET http://localhost:8080/api/auth/profile \
  -H "Authorization: Bearer YOUR_SUPABASE_JWT_TOKEN"
```

### Extension Test:
1. Load extension in Chrome
2. Open popup
3. Enter email and click "Αποστολή Magic Link"
4. Check email and click link
5. Should see authenticated state

## Step 9: Production Deployment

1. **Deploy to Vercel:**
   ```bash
   git add .
   git commit -m "Add Supabase authentication"
   git push
   ```

2. **Set environment variables in Vercel:**
   - Go to Vercel dashboard
   - Project settings > Environment Variables
   - Add all the variables from Step 4

3. **Test production:**
   - Visit your Vercel URL
   - Test `/api/auth/profile` endpoint
   - Load extension and test auth flow

## 🔧 Troubleshooting

### Common Issues:

1. **"Supabase not initialized" error:**
   - Check SUPABASE_URL and SUPABASE_ANON_KEY are set
   - Verify the URL format: `https://xxx.supabase.co`

2. **"User not found" error:**
   - User profile might not be created
   - Check if user exists in `auth.users` table
   - Run profile creation manually if needed

3. **CORS errors in extension:**
   - Add your domain to Supabase CORS settings
   - Go to Settings > API > CORS
   - Add `chrome-extension://*` for extension

4. **Email not sending:**
   - Check Supabase email settings
   - Verify SMTP configuration if using custom email

### Database Queries for Debugging:

```sql
-- Check all users
SELECT * FROM auth.users;

-- Check user profiles
SELECT * FROM public.user_profiles;

-- Check usage logs
SELECT * FROM public.usage_logs ORDER BY created_at DESC LIMIT 10;

-- Get user stats
SELECT * FROM get_user_stats();
```

## 🎉 You're Done!

Your News Copilot now uses Supabase for:
- ✅ Magic link authentication
- ✅ User management
- ✅ Usage tracking
- ✅ Rate limiting
- ✅ Admin operations
- ✅ Secure database with RLS
- ✅ Automatic email verification

The system is now production-ready with enterprise-grade authentication!