# AI Collaboration Guide

**How to work with AI effectively without creating a mess.**

## Common AI Problems & Solutions

### 1. **Incomplete Implementation (AI Stops Halfway)**

#### The Problem
AI gives you partial code, you implement it, then discover missing pieces:
- Database relations not properly connected
- Error handling missing
- API endpoints incomplete
- Frontend doesn't match backend

#### The Solution: Full Context Prompts
```
Don't just say: "Add user authentication"

Say this instead:
"Implement complete user authentication for [Bot/Web App]:
- Database schema with relations
- Registration with validation
- Login with session management  
- Password hashing with bcrypt
- Error handling for all edge cases
- Integration with existing [specify your current setup]
- Test with example requests
- Provide startup script

Show me COMPLETE working code, not snippets."
```

#### Force Completeness
```
Always end prompts with:
"Provide the COMPLETE implementation including:
1. All necessary imports/dependencies
2. Database migrations if needed
3. Error handling for edge cases
4. Example usage/testing
5. Integration with existing code
6. Startup instructions

Do not give partial implementations."
```

### 2. **Database Relation Disasters**

#### The Problem
AI creates tables that don't connect properly:
- Foreign keys missing
- Join queries broken
- Data inconsistencies
- Migration failures

#### The Solution: Explicit Schema Definition
```
Always specify your COMPLETE database schema:

"Here's my current database schema:
[paste your current schema]

Now add [new feature] with proper relations:
- Show me the SQL migration
- Update existing tables if needed
- Provide JOIN queries for common operations
- Test the relations work correctly
- Show example data and queries"
```

#### Database Health Check Script
```bash
#!/bin/bash
# Add this to your automation script

echo "🔍 Database Health Check..."

# Check tables exist
echo "Checking required tables..."
psql $DATABASE_URL -c "\dt"

# Check foreign keys
echo "Checking foreign key constraints..."
psql $DATABASE_URL -c "
SELECT tc.table_name, tc.constraint_name, tc.constraint_type, kcu.column_name
FROM information_schema.table_constraints tc
JOIN information_schema.key_column_usage kcu 
ON tc.constraint_name = kcu.constraint_name
WHERE tc.constraint_type = 'FOREIGN KEY';"

# Check for orphaned records
echo "Checking for orphaned records..."
# Add your specific orphan checks here

echo "✅ Database check complete"
```

### 3. **AI Token Cost Management**

#### The Problem
- Long conversations eat up tokens
- Repetitive explanations cost money
- Context gets lost, AI repeats work

#### The Solution: Structured Sessions
```
Session 1: Planning (save output)
"Plan [project] following docs/02_prd.md template.
Save this output - I'll reference it in next session."

Session 2: Implementation (reference previous)
"Based on the plan from previous session: [paste plan]
Implement [specific part] following docs/01_dev_protocol.md"

Session 3: Testing (reference both)
"Based on plan and implementation from previous sessions:
Test and fix [specific issues]"
```

#### Token-Efficient Prompts
```
❌ Don't repeat context every time:
"I'm building a Telegram bot with user authentication using Node.js and PostgreSQL with Stripe payments..."

✅ Reference documentation:
"Reference docs/02_prd.md and docs/07_payment_security.md
Fix this Stripe webhook error: [error]"

✅ Use numbered references:
"Continue implementation from docs/02_prd.md section 2.3"
```

### 4. **Configuration & Setup Automation**

#### The Problem
- Forgetting dependency installations
- Environment variables not set correctly
- Different setup steps for different features
- Manual setup every time

#### The Solution: Smart Setup Script
```bash
#!/bin/bash
# setup.sh - Automated project setup

set -e  # Exit on any error

echo "🚀 Setting up your project..."

# Detect project type
if [ -f "package.json" ]; then
    PROJECT_TYPE="node"
elif [ -f "requirements.txt" ]; then
    PROJECT_TYPE="python"
elif [ -f "go.mod" ]; then
    PROJECT_TYPE="go"
else
    echo "❓ Project type not detected. What are you building?"
    echo "1) Node.js (Bot/Web App)"
    echo "2) Python (Bot/Web App)" 
    echo "3) Go (Bot/Web App)"
    read -p "Choose (1-3): " choice
    case $choice in
        1) PROJECT_TYPE="node" ;;
        2) PROJECT_TYPE="python" ;;
        3) PROJECT_TYPE="go" ;;
        *) echo "Invalid choice" && exit 1 ;;
    esac
fi

echo "📦 Detected: $PROJECT_TYPE project"

# Install dependencies
case $PROJECT_TYPE in
    "node")
        echo "Installing Node.js dependencies..."
        npm install
        
        # Check for common bot dependencies
        if grep -q "telegraf\|discord\|whatsapp" package.json; then
            echo "🤖 Bot project detected"
            BOT_TYPE=true
        fi
        ;;
    "python")
        echo "Installing Python dependencies..."
        pip install -r requirements.txt
        
        if grep -q "telegram\|discord\|whatsapp" requirements.txt; then
            echo "🤖 Bot project detected"
            BOT_TYPE=true
        fi
        ;;
    "go")
        echo "Installing Go dependencies..."
        go mod tidy
        
        if grep -q "telegram\|discord\|whatsapp" go.mod; then
            echo "🤖 Bot project detected"
            BOT_TYPE=true
        fi
        ;;
esac

# Environment setup
if [ ! -f ".env" ]; then
    echo "⚙️ Creating environment file..."
    
    if [ "$BOT_TYPE" = true ]; then
        cat > .env << 'EOF'
# Bot Configuration
BOT_TOKEN=your_bot_token_here
DATABASE_URL=sqlite:///bot.db

# Payment Configuration (if needed)
STRIPE_SECRET_KEY=sk_test_your_stripe_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret

# Security
JWT_SECRET=your_jwt_secret_here
WEBHOOK_SECRET=your_webhook_secret

# Admin Configuration
ADMIN_USER_IDS=123456789,987654321
EOF
    else
        cat > .env << 'EOF'
# Web App Configuration
DATABASE_URL=postgresql://user:pass@localhost:5432/dbname
JWT_SECRET=your_jwt_secret_here

# Payment Configuration
STRIPE_SECRET_KEY=sk_test_your_stripe_key
STRIPE_WEBHOOK_SECRET=whsec_your_webhook_secret

# API Configuration
API_PORT=3000
NODE_ENV=development
EOF
    fi
    
    echo "✅ Created .env file - EDIT IT with your actual values!"
    echo "⚠️  Never commit .env to git!"
fi

# Database setup
if command -v psql &> /dev/null; then
    echo "🗄️ PostgreSQL detected"
    if [ -f "migrations" ] || [ -f "schema.sql" ]; then
        echo "Running database migrations..."
        # Add your migration command here
    fi
elif [ ! -f "*.db" ]; then
    echo "🗄️ Setting up SQLite database..."
    # Create SQLite database if needed
fi

# Security checks
echo "🔒 Running security checks..."

# Check for secrets in code
if command -v grep &> /dev/null; then
    if grep -r "sk_live\|sk_test\|bot.*token.*=" . --exclude-dir=node_modules --exclude=".env" 2>/dev/null; then
        echo "⚠️  WARNING: Potential secrets found in code!"
        echo "Move all secrets to .env file"
    fi
fi

# Start the application
echo "🚀 Starting application..."

case $PROJECT_TYPE in
    "node")
        if [ "$BOT_TYPE" = true ]; then
            echo "Starting bot..."
            npm run start:bot 2>/dev/null || npm start 2>/dev/null || node index.js
        else
            echo "Starting web server..."
            npm run dev 2>/dev/null || npm start 2>/dev/null || node server.js
        fi
        ;;
    "python")
        if [ "$BOT_TYPE" = true ]; then
            echo "Starting bot..."
            python bot.py 2>/dev/null || python main.py 2>/dev/null || python app.py
        else
            echo "Starting web server..."
            python app.py 2>/dev/null || python main.py 2>/dev/null || flask run
        fi
        ;;
    "go")
        echo "Building and starting Go application..."
        go build -o app
        ./app
        ;;
esac

echo "✅ Setup complete!"
echo "📚 Check docs/03_error_fix_guide.md if you encounter issues"
```

### 5. **Preventing AI Project Chaos**

#### The Problem
AI suggests complex solutions that make project harder to maintain

#### The Solution: Complexity Constraints
```
Always add to your prompts:
"Keep this simple for a solo developer:
- Use SQLite instead of PostgreSQL for small projects
- Use environment variables, not complex config systems
- Use simple hosting (Railway/Render), not complex infrastructure
- Focus on the core feature, ignore nice-to-haves
- Provide working code, not enterprise architecture"
```

#### Anti-Chaos Checklist
```
Before implementing AI suggestions, ask:
□ Can I understand this code in 6 months?
□ Can I debug this at 3am when something breaks?
□ Is this solving the core user problem?
□ Am I adding complexity without clear benefit?
□ Will this work with my current skill level?

If any answer is NO, ask AI for simpler approach.
```

### 6. **Stability Without Constant Monitoring**

#### The Problem
Apps break when you're not watching

#### The Solution: Self-Healing Patterns
```bash
#!/bin/bash
# healthcheck.sh - Add to your deployment

while true; do
    # Check if app is responding
    if ! curl -f http://localhost:3000/health &>/dev/null; then
        echo "🚨 App not responding, restarting..."
        pm2 restart app || systemctl restart myapp
        
        # Wait and check again
        sleep 30
        if ! curl -f http://localhost:3000/health &>/dev/null; then
            # Send alert (email, Telegram, etc.)
            curl -X POST "https://api.telegram.org/bot$BOT_TOKEN/sendMessage" \
                -d "chat_id=$ADMIN_CHAT_ID" \
                -d "text=🚨 App restart failed on $(hostname)"
        fi
    fi
    
    # Check database connection
    if ! psql $DATABASE_URL -c "SELECT 1" &>/dev/null; then
        echo "🚨 Database connection failed"
        # Alert admin
    fi
    
    # Check disk space
    DISK_USAGE=$(df / | awk 'NR==2 {print $5}' | sed 's/%//')
    if [ $DISK_USAGE -gt 90 ]; then
        echo "🚨 Disk space critical: ${DISK_USAGE}%"
        # Clean up logs, temp files
        find ./logs -name "*.log" -mtime +7 -delete
    fi
    
    sleep 300  # Check every 5 minutes
done
```

## AI Prompting Best Practices

### For Database Work
```
"Design database schema for [feature]:
1. Show CREATE TABLE statements with proper foreign keys
2. Include indexes for performance
3. Show example INSERT/SELECT queries
4. Test data integrity with example data
5. Provide migration script from current schema"
```

### For Payment Integration
```
"Implement [Stripe/PayPal] for [subscription/one-time]:
1. Complete webhook verification code
2. Database schema for transactions
3. Error handling for failed payments
4. Testing with webhook simulator
5. Security checklist compliance"
```

### For Bot Development
```
"Create [Telegram/WhatsApp] bot for [specific feature]:
1. Complete bot setup with error handling
2. Rate limiting and spam prevention
3. User state management in database
4. Admin commands and user authorization
5. Deployment instructions for Railway/Render"
```

---

**Remember**: AI is a powerful tool, but you need to direct it properly. Give complete context, demand complete implementations, and always test the results before considering the work done.