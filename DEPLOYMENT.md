# Deployment Guide - News Copilot

This guide covers deploying News Copilot to Vercel, which hosts both the Next.js web app and the Python Flask API as serverless functions.

## Prerequisites

- Vercel account (free tier works)
- GitHub repository with your code
- Environment variables ready

## Deployment Structure

```
/ (root)
├── web/          # Next.js app (main deployment)
├── api/          # Python Flask API (serverless functions)
└── vercel.json   # Deployment configuration
```

## Step 1: Prepare for Deployment

1. **Ensure all code is committed:**
   ```bash
   git add .
   git commit -m "Prepare for Vercel deployment"
   git push origin main
   ```

2. **Verify `vercel.json` configuration:**
   ```json
   {
     "version": 2,
     "builds": [
       {
         "src": "web/package.json",
         "use": "@vercel/next"
       },
       {
         "src": "api/index.py",
         "use": "@vercel/python",
         "config": {
           "maxLambdaSize": "15mb",
           "runtime": "python3.9"
         }
       }
     ],
     "routes": [
       {
         "src": "/api/(.*)",
         "dest": "/api/index.py"
       },
       {
         "src": "/(.*)",
         "dest": "/web/$1"
       }
     ]
   }
   ```

## Step 2: Connect to Vercel

1. **Install Vercel CLI (optional):**
   ```bash
   npm i -g vercel
   ```

2. **Connect via GitHub:**
   - Go to [vercel.com](https://vercel.com)
   - Click "Add New Project"
   - Import your GitHub repository
   - Vercel will auto-detect the configuration

## Step 3: Configure Environment Variables

In the Vercel dashboard, add these environment variables:

### Required Variables:
```
XAI_API_KEY=your_grok_api_key_here
```

### Optional Variables (for authentication):
```
SUPABASE_URL=your_supabase_url
SUPABASE_ANON_KEY=your_supabase_anon_key  
SUPABASE_SERVICE_KEY=your_supabase_service_key
AUTH_REQUIRED=true
```

### Production Settings:
```
NODE_ENV=production
PYTHONPATH=/var/task
```

## Step 4: Deploy

### Via Vercel Dashboard:
1. Click "Deploy" after configuring environment variables
2. Vercel will build both the Next.js app and Python API
3. Monitor the build logs for any errors

### Via CLI:
```bash
# From project root
vercel

# For production deployment
vercel --prod
```

## Step 5: Verify Deployment

After deployment, test these endpoints:

1. **Web App:** `https://your-project.vercel.app`
2. **API Health:** `https://your-project.vercel.app/api/health`
3. **Analysis Types:** `https://your-project.vercel.app/api/analysis/types`

## Deployment Architecture

```
┌─────────────────────────────────────────┐
│         Vercel Edge Network             │
├─────────────────────────────────────────┤
│                                         │
│  ┌─────────────┐    ┌────────────────┐ │
│  │  Next.js    │    │  Python API    │ │
│  │  Web App    │    │  (Serverless)  │ │
│  │             │    │                │ │
│  │  /pages     │    │  /api/*        │ │
│  │  /components│    │                │ │
│  │  /styles    │    │  Flask routes  │ │
│  └─────────────┘    └────────────────┘ │
│          ↓                   ↓          │
│  ┌─────────────────────────────────┐   │
│  │     Static Assets (CDN)         │   │
│  └─────────────────────────────────┘   │
└─────────────────────────────────────────┘
```

## Production Considerations

### 1. API Rate Limits
- Grok API has rate limits
- Consider implementing caching for repeated requests
- Monitor usage in Vercel Functions dashboard

### 2. Serverless Function Limits
- Default timeout: 10 seconds (hobby), 60 seconds (pro)
- Memory: 1024 MB default
- Adjust in `vercel.json` if needed:
  ```json
  {
    "functions": {
      "api/index.py": {
        "maxDuration": 60,
        "memory": 1024
      }
    }
  }
  ```

### 3. Environment-Specific Settings
The app automatically detects the environment:
- Development: Proxies to localhost:8080
- Production: Uses relative `/api/*` paths

### 4. Custom Domain
1. In Vercel dashboard, go to Settings → Domains
2. Add your custom domain
3. Update DNS records as instructed
4. SSL certificates are automatic

## Monitoring & Logs

### View Logs:
- **Vercel Dashboard:** Project → Functions → View Logs
- **CLI:** `vercel logs`

### Monitor Performance:
- Function execution time
- Error rates
- API usage

## Troubleshooting

### Common Issues:

1. **"Module not found" errors:**
   - Ensure all dependencies are in `requirements.txt`
   - Check Python version compatibility

2. **API routes returning 404:**
   - Verify `vercel.json` routing configuration
   - Check Flask blueprint URL prefixes

3. **Environment variable issues:**
   - Redeploy after adding new variables
   - Use Vercel dashboard, not `.env` files

4. **Build failures:**
   - Check build logs for specific errors
   - Ensure `package.json` and `requirements.txt` are complete

### Debug Locally with Vercel CLI:
```bash
# Simulate Vercel environment locally
vercel dev
```

## Rollback Deployment

If issues arise:

1. **Via Dashboard:**
   - Go to Deployments tab
   - Find previous working deployment
   - Click "..." → "Promote to Production"

2. **Via CLI:**
   ```bash
   vercel rollback
   ```

## Continuous Deployment

Vercel automatically deploys when you push to GitHub:
- `main` branch → Production
- Other branches → Preview deployments

To disable auto-deploy:
1. Project Settings → Git
2. Toggle "Auto-deploy" off

## Cost Optimization

Free tier includes:
- 100GB bandwidth
- 100K serverless function invocations
- Unlimited static requests

To stay within limits:
- Implement caching
- Optimize API calls
- Use static generation where possible

## Next Steps

After successful deployment:

1. **Set up monitoring alerts**
2. **Configure custom error pages**
3. **Implement analytics**
4. **Set up staging environment**
5. **Create deployment checklist**

For more details, see [Vercel Documentation](https://vercel.com/docs).