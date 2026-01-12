# Session Storage Testing Guide

## How to Test if Session is Storing

### Step 1: Run the Login Script
```bash
python src/session/login_once.py
```

**What this does:**
1. Connects to your MCP server (self-hosted at localhost:8090)
2. Calls the `login` tool to get a login URL
3. Opens browser with Zerodha login page
4. Extracts session cookie from the login URL
5. Saves session to file using `SessionManager`
6. Validates the session

**Expected output:**
- Should show: "🍪 Extracted session cookie → ..."
- Should show: "✅ Session validated successfully for {user_id}"

---

### Step 2: Check if Session File was Created
```bash
python src/session/test_session_storage.py
```

**What this does:**
1. Checks if session file exists
2. Shows session file location (from `SESSION_FILE_PATH` env var)
3. Displays session file contents
4. Tests loading session using `SessionManager`
5. Validates session with MCP server

**Expected output:**
- Should show session file path
- Should show "✅ Session loaded successfully!"
- Should show cookie preview
- Should show "✅ Session is VALID and working!"

---

### Step 3: Verify Session File Manually

**Check the session file location:**
- Default: `./data/sessions/session.json`
- Or check your `.env` file for `SESSION_FILE_PATH`

**Session file should contain:**
```json
{
  "user_id": "demo-user",
  "provider": "kite",
  "cookie": "session_id=...",
  "created_at": "2024-...",
  "last_validated_at": "2024-...",
  "status": "ACTIVE",
  "meta": {}
}
```

---

## Troubleshooting

### Issue: Session file not created
**Check:**
1. Is MCP server running? (Should be at `http://localhost:8090`)
2. Did you complete login in browser?
3. Check console output for errors
4. Check file permissions on `data/sessions/` directory

### Issue: Session file exists but empty/corrupt
**Check:**
1. Delete the session file
2. Run `login_once.py` again
3. Make sure login completes successfully

### Issue: Session validation fails
**Check:**
1. Is MCP server running?
2. Is the session cookie still valid? (Zerodha sessions expire)
3. Check MCP server logs for errors
4. Try re-login if session expired

### Issue: Session not restoring on next run
**Check:**
1. Verify `SESSION_FILE_PATH` in `.env` matches where file was created
2. Verify `USER_ID` in `.env` matches the user_id in session file
3. Check if session file exists at expected location
4. Run `test_session_storage.py` to diagnose

---

## Environment Variables Required

Make sure these are set in your `.env` file:

```env
# Session file location
SESSION_FILE_PATH=./data/sessions/session.json

# User ID (should match the user_id in session file)
USER_ID=demo-user

# MCP server URLs (self-hosted)
MCP_SSE_URL=http://localhost:8090/sse
MCP_HTTP_URL=http://localhost:8090/mcp
```

---

## Quick Test Commands

```bash
# 1. Test if session file exists and can be loaded
python src/session/test_session_storage.py

# 2. Create/login and save session
python src/session/login_once.py

# 3. Test again to verify session was saved
python src/session/test_session_storage.py
```

---

## Files in Session Folder

- `login_once.py` - **RUN THIS** to login and save session
- `test_session_storage.py` - **RUN THIS** to test if session is stored
- `store.py` - Low-level file storage
- `manager.py` - High-level session API
- `schema.py` - Session data model
- `kite_mcp_client.py` - MCP client with session restore
- `use_session.py` - Consumer API for other modules

---

## Current Design Limitation

⚠️ **Note:** Current implementation stores ONE session per file. 
- The `user_id` and `provider` are stored IN the session record
- But the file structure doesn't support multiple users in one file
- For multiple users, you'd need separate files or a database

This is fine for single-user scenarios or if each user has their own instance.

