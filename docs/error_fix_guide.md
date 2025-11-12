# Error Fix Guide

**Simple workflow for fixing errors without bureaucratic overhead.**

## Quick Decision Framework

### 🎯 One Simple Question: Does This Touch Critical Systems?

**Critical Systems** = User data, money, security, production environment

- **YES** → Reference `01_dev_protocol.md`
- **NO** → Standard fix workflow

That's it. No complex templates, no decision trees.

---

## How to Report Errors Safely

### ⚠️ NEVER Just Paste Raw Errors
Raw error messages often contain:
- API keys, passwords, tokens
- Database connection strings
- Internal system paths
- User data or sensitive information

### ✅ Safe Error Reporting Template

```
Error Fix Request - Reference: docs/error_fix_guide.md

CONTEXT:
- What were you trying to do? [Brief description]
- Environment: [Development/Staging/Production]  
- Recent changes: [What was changed recently]

ERROR:
[Sanitized error message - remove sensitive data]

ADDITIONAL INFO:
- Steps to reproduce: [How to trigger this error]
- Expected behavior: [What should happen instead]
- Impact: [Critical/Medium/Low - who is affected]

[IF CRITICAL: Follow 01_dev_protocol.md fatal gates]

After fixing:
1. Test the fix works completely
2. Run debug scenarios to prevent regressions
3. Update relevant documentation  
4. Explain what caused the error and how you fixed it
```

### 🛡️ How to Sanitize Errors

**Before pasting any error, remove:**
- **Passwords/API keys**: `password=secret123` → `password=[REDACTED]`
- **Connection strings**: `postgres://user:pass@host/db` → `postgres://[USER]:[PASS]@[HOST]/[DB]`
- **File paths**: `/home/user/secret/app.js` → `/[PATH]/app.js`
- **User data**: `user_id=12345` → `user_id=[USER_ID]`
- **Internal IPs**: `192.168.1.100` → `[INTERNAL_IP]`

**Example Sanitization:**
```
❌ BAD - Exposes secrets:
Error: Connection failed to postgres://admin:secretpass123@internal-db.company.com:5432/users_production

✅ GOOD - Sanitized:
Error: Database connection failed to postgres://[USER]:[PASS]@[HOST]:[PORT]/[DATABASE]
```

---

## When to Reference 01_dev_protocol.md

### ✅ Always Reference for:
- **Authentication/authorization errors**
- **Database/data corruption issues**
- **Security vulnerabilities**
- **Production deployment problems**
- **Payment/financial system errors**
- **API security issues**
- **Infrastructure/container problems**

### ❌ No Need to Reference for:
- **UI bugs** (button doesn't work, styling issues)
- **Typos** in code or documentation
- **Local development setup** issues
- **Performance optimizations** (unless affecting production)
- **Code refactoring** without functional changes
- **Documentation updates** only

### 🤷 When Uncertain:
Reference it anyway. Better safe than sorry.

---

## Common Error Types & Prompts

### Application Crashes
```
Fix this crash: [ERROR MESSAGE AND STACK TRACE]

Root cause analysis:
1. What triggered the crash?
2. Why wasn't this caught earlier?
3. How can we prevent similar crashes?

Test thoroughly and add error handling if missing.
```

### Security Issues
```
SECURITY ISSUE: [DESCRIBE VULNERABILITY]

Follow 01_dev_protocol.md security controls.
This affects user safety - fix immediately and test all security boundaries.
Update security documentation if needed.
```

### Database Problems
```
Database error: [ERROR DETAILS]

Follow 01_dev_protocol.md data integrity requirements.
Ensure no data corruption, test backup/restore if needed.
Update database documentation.
```

### Performance Issues
```
Performance problem: [SLOW OPERATION/HIGH RESOURCE USAGE]

Target: Improve [metric] from [current] to [target]
Measure before/after, don't break existing functionality.
Update performance notes in documentation.
```

### Production Emergencies
```
PRODUCTION EMERGENCY: [CRITICAL ISSUE AFFECTING USERS]

Follow 01_dev_protocol.md emergency procedures.
Priority: Restore service, then investigate root cause.
Document incident and prevention measures.
```

---

## Testing & Debug Checklist

### After Every Fix:
- [ ] **Fix works**: Error no longer occurs under original conditions
- [ ] **No regressions**: Existing functionality still works
- [ ] **Edge cases**: Test boundary conditions and error scenarios  
- [ ] **Performance**: Fix doesn't introduce new slowdowns
- [ ] **Documentation**: Update if user-facing behavior changes

### For Critical Fixes:
- [ ] **Security check**: No new vulnerabilities introduced
- [ ] **Data integrity**: No risk of data corruption
- [ ] **Rollback plan**: Can revert if fix causes problems
- [ ] **Monitoring**: Verify fix effectiveness in production

---

## Documentation Updates

### Always Update:
- **core_summary.md**: Current status and known issues
- **CHANGELOG.md**: For user-facing changes

### Update If Relevant:
- **README.md**: If setup/usage instructions change
- **Architecture docs**: If system behavior changes
- **Security docs**: If security fixes affect policies
- **Operations docs**: If infrastructure changes

---

## Communication Template

### For Team Updates:
```
Fixed: [BRIEF DESCRIPTION]
Cause: [ROOT CAUSE]
Solution: [WHAT WAS CHANGED]
Testing: [HOW IT WAS VERIFIED]
Impact: [USER/SYSTEM IMPACT]
Prevention: [HOW TO AVOID IN FUTURE]
```

### For User Communication:
```
Issue: [USER-FRIENDLY DESCRIPTION]
Status: Fixed
Timeline: [WHEN IT WILL BE RESOLVED]
Prevention: [STEPS TO PREVENT RECURRENCE]
```

---

## Escalation Guidelines

### Escalate Immediately If:
- **Data loss** or corruption detected
- **Security breach** suspected
- **Production system** completely down
- **Financial transactions** affected
- **Legal/compliance** implications

### Escalation Prompt:
```
ESCALATION NEEDED: [CRITICAL ISSUE]

Impact: [BUSINESS/USER IMPACT]
Urgency: [TIMELINE REQUIREMENTS]
Resources needed: [WHAT HELP YOU NEED]

Follow 01_dev_protocol.md emergency procedures.
```

---

## Anti-Patterns to Avoid

❌ **Over-engineering fixes**: Don't rebuild systems for simple bugs
❌ **Under-testing**: "It works on my machine" isn't enough
❌ **No root cause**: Fixing symptoms without understanding why
❌ **Documentation debt**: Fixing without updating docs
❌ **Scope creep**: Fixing unrelated issues in same change

✅ **Minimal effective fix**: Smallest change that solves the problem
✅ **Comprehensive testing**: Verify fix works in all scenarios
✅ **Root cause analysis**: Understand and prevent recurrence
✅ **Documentation hygiene**: Keep docs current with reality
✅ **Single responsibility**: One fix per change

---

## Quick Reference Card

```
ERROR REPORTING WORKFLOW:
1. Sanitize error (remove passwords, API keys, sensitive data)
2. Provide context (what you were doing, environment)
3. Critical system? → Add "Follow 01_dev_protocol.md"
4. Include steps to reproduce and expected behavior

ERROR FIX WORKFLOW:
1. Analyze sanitized error and context
2. Fix + test + debug + document
3. Verify no regressions
4. Update core_summary.md status

CRITICAL SYSTEMS:
- User data/money
- Security/auth  
- Production environment
- Database/infrastructure

ALWAYS SANITIZE:
- Passwords/API keys
- Database connection strings
- File paths with sensitive info
- User data/IDs
- Internal IP addresses

ALWAYS TEST:
- Fix works
- No regressions
- Edge cases  
- Performance impact
```

---

**Remember**: The goal is fixing problems effectively, not following perfect processes. Use this guide to work faster and safer, not slower and more bureaucratic.