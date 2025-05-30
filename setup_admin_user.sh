#!/bin/bash

echo "Setting up admin user for News Copilot..."
echo "========================================="

# Navigate to backend directory
cd backend

# Run migrations
echo "Running database migrations..."
python manage.py migrate

# Create seed user
echo "Creating admin user..."
python manage.py createsuperuser --username admin --email admin@newscopilot.com

echo ""
echo "✅ Setup complete!"
echo ""
echo "Admin credentials:"
echo "  Email: admin@newscopilot.com"
echo "  Password: admin123!"
echo ""
echo "Test user credentials:"
echo "  Email: user@newscopilot.com"
echo "  Password: user123!"
echo ""
echo "To start the servers:"
echo "  Backend: cd backend && python manage.py runserver"
echo "  Frontend: cd frontend && npm run dev"
echo ""
echo "Then visit http://localhost:3000/login to sign in"