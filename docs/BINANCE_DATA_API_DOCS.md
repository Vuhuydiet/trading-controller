# Optional Authentication Implementation

**Date:** 2026-01-07
**Feature:** Public Market Data APIs with Optional Authentication

## Overview

Implemented optional authentication for all Market Data APIs following TradingView model. Users can view charts without login, with premium features available for authenticated users.

---

## Changes Summary

### New File Created

**app/modules/identity/optional_auth.py**
- `get_current_user_optional()` - Optional authentication dependency
- `get_user_limits()` - Tier-based limits function

**Tier System:**
```python
Anonymous (No auth):
  - max_klines: 500
  - max_depth: 100
  - rate_limit: 5 req/min
  - has_ai_access: False

Free (Registered):
  - max_klines: 500
  - max_depth: 100
  - rate_limit: 10 req/min
  - has_ai_access: False

VIP (Paid):
  - max_klines: 5000
  - max_depth: 1000
  - rate_limit: 1000 req/min
  - has_ai_access: True
```

---

## Updated Routers

All Market Data routers now use optional authentication:

### 1. get_symbols/router.py
- Changed from `get_current_user_dto` to `get_current_user_optional`
- User parameter now `Optional[UserDTO]`
- No authentication required
- Added "Public endpoint" to descriptions

### 2. get_price/router.py
- Changed from `get_current_user_dto` to `get_current_user_optional`
- User parameter now `Optional[UserDTO]`
- No authentication required
- Added "Public endpoint" to descriptions

### 3. get_ticker/router.py
- Changed from `get_current_user_dto` to `get_current_user_optional`
- User parameter now `Optional[UserDTO]`
- No authentication required
- Added "Public endpoint" to descriptions

### 4. get_klines/router.py (MOST IMPORTANT FOR CHARTS)
- Changed from `get_current_user_dto` to `get_current_user_optional`
- User parameter now `Optional[UserDTO]`
- **Added tier-based limits:**
  - Anonymous: max 500 klines
  - Free: max 500 klines
  - VIP: max 5000 klines
- Limit is automatically capped based on user tier
- Added limit info to API description

### 5. get_depth/router.py
- Changed from `get_current_user_dto` to `get_current_user_optional`
- User parameter now `Optional[UserDTO]`
- **Added tier-based limits:**
  - Anonymous: max depth 100
  - Free: max depth 100
  - VIP: max depth 1000
- Limit is automatically capped based on user tier
- Added limit info to API description

### 6. ws_status/router.py
- Changed from `get_current_user_dto` to `get_current_user_optional`
- User parameter now `Optional[UserDTO]`
- No authentication required
- Added "Public endpoint" to description

---

## API Behavior

### Before (Required Auth)
```bash
# Without token - ERROR
GET /api/v1/market/klines/BTCUSDT?interval=1h
Response: 401 Unauthorized

# With token - OK
GET /api/v1/market/klines/BTCUSDT?interval=1h
Authorization: Bearer <token>
Response: 200 OK
```

### After (Optional Auth)
```bash
# Without token - OK (limited to 500)
GET /api/v1/market/klines/BTCUSDT?interval=1h&limit=1000
Response: 200 OK (returns 500 klines, capped automatically)

# With Free token - OK (limited to 500)
GET /api/v1/market/klines/BTCUSDT?interval=1h&limit=1000
Authorization: Bearer <free-token>
Response: 200 OK (returns 500 klines)

# With VIP token - OK (full access)
GET /api/v1/market/klines/BTCUSDT?interval=1h&limit=5000
Authorization: Bearer <vip-token>
Response: 200 OK (returns 5000 klines)
```

---

## Still Protected Endpoints

These endpoints STILL require authentication:

**AI Features** (in other feature folders):
- GET /api/v1/market/ai-analysis - Requires auth
- GET /api/v1/market/check-chart-access - May require auth

**Authentication:**
- POST /api/v1/register - Public (to allow registration)
- POST /api/v1/login - Public (to allow login)

---

## Testing

### Test Anonymous Access

```bash
# No authorization header - should work
curl http://localhost:8000/api/v1/market/symbols
curl http://localhost:8000/api/v1/market/price/BTCUSDT
curl http://localhost:8000/api/v1/market/ticker/BTCUSDT
curl http://localhost:8000/api/v1/market/klines/BTCUSDT?interval=1h&limit=500
curl http://localhost:8000/api/v1/market/depth/BTCUSDT?limit=100
curl http://localhost:8000/api/v1/market/ws/status
```

### Test Authenticated Access

```bash
# 1. Register and login to get token
curl -X POST http://localhost:8000/api/v1/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","password":"test123","tier":"free"}'

curl -X POST http://localhost:8000/api/v1/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=test@example.com&password=test123"

# 2. Use token - should allow same as anonymous for free tier
curl http://localhost:8000/api/v1/market/klines/BTCUSDT?interval=1h&limit=1000 \
  -H "Authorization: Bearer <token>"
# Returns 500 klines (capped for free tier)
```

### Test Tier Limits

```bash
# Create VIP user
curl -X POST http://localhost:8000/api/v1/register \
  -H "Content-Type: application/json" \
  -d '{"email":"vip@example.com","password":"test123","tier":"vip"}'

# Login and get VIP token
curl -X POST http://localhost:8000/api/v1/login \
  -H "Content-Type: application/x-www-form-urlencoded" \
  -d "username=vip@example.com&password=test123"

# Test VIP limits
curl http://localhost:8000/api/v1/market/klines/BTCUSDT?interval=1h&limit=5000 \
  -H "Authorization: Bearer <vip-token>"
# Returns 5000 klines (VIP tier)
```

---

## Swagger UI Changes

In http://localhost:8000/docs:

**Before:**
- All market endpoints showed lock icon
- Required "Authorize" before testing
- Could not test without login

**After:**
- Market endpoints show open lock icon (optional auth)
- Can test immediately without authorization
- Can optionally authorize to test premium limits
- Description shows "Public endpoint - no authentication required"

---

## Benefits

**User Experience:**
1. View charts immediately without login (like TradingView)
2. Natural conversion funnel: Anonymous → Free → VIP
3. No friction for first-time visitors

**Monetization:**
1. Clear value proposition for premium tiers
2. Users see limits and upgrade when needed
3. Can track anonymous vs authenticated usage

**Business:**
1. Increased traffic (no login wall)
2. Better conversion tracking
3. Tier-based revenue model

**Technical:**
1. Backward compatible (existing tokens still work)
2. Easy to add more tiers
3. Can adjust limits per tier easily

---

## Future Enhancements

**Rate Limiting (TODO):**
```python
# Add IP-based rate limiting for anonymous
# Add user-based rate limiting for authenticated
# Implement in middleware
```

**Analytics (TODO):**
```python
# Track anonymous vs authenticated usage
# Monitor conversion rates
# A/B test tier limits
```

**Premium Features (TODO):**
```python
# AI analysis - Premium only
# Custom indicators - Premium only
# Historical data export - VIP only
# Priority API access - VIP only
```

---

## Migration Notes

**No Breaking Changes:**
- Existing authenticated clients continue to work
- Frontend can optionally remove auth for market data
- Backward compatible with current implementation

**For Frontend:**
```javascript
// Before - required auth
const response = await fetch('/api/v1/market/klines/BTCUSDT?interval=1h', {
  headers: { 'Authorization': `Bearer ${token}` }
});

// After - optional auth
const response = await fetch('/api/v1/market/klines/BTCUSDT?interval=1h');
// No authorization needed, but can include for premium limits

// Or with optional auth
const headers = token ? { 'Authorization': `Bearer ${token}` } : {};
const response = await fetch('/api/v1/market/klines/BTCUSDT?interval=1h', { headers });
```

---

## Rollback Plan

If needed to rollback:

1. Change all routers back from `get_current_user_optional` to `get_current_user_dto`
2. Remove `Optional[UserDTO]` type hints
3. Remove tier limit checks
4. Delete `app/modules/identity/optional_auth.py`

---

**Status:** IMPLEMENTED AND READY FOR TESTING
**Testing:** Manual testing required
**Deployment:** Safe to deploy (backward compatible)
