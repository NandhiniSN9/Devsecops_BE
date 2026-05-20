## Complete Setup Guide for Windows

This guide explains everything you need to know to test PDF report generation on Windows.

---

## Understanding the Two Python Installations

You might see two Python installations on your system:

### 1. **System Python** (Python.org installation)
- **Location**: `C:\Users\<YourName>\AppData\Local\Programs\Python\Python312\`
- **How you got it**: Downloaded from python.org
- **Used for**: General Python development

### 2. **Virtual Environment Python** (Project-specific)
- **Location**: `.venv\Scripts\python.exe` (inside your project folder)
- **How you got it**: Created with `python -m venv .venv`
- **Used for**: This specific project only (keeps packages isolated)

### Which Python Should You Use?

**ALWAYS use the Virtual Environment Python** for this project:

```powershell
# Activate virtual environment first
.venv\Scripts\activate

# Then run commands (they will use .venv Python automatically)
python test_template_rendering.py
python scripts/update_email_templates.py
```

**Why?** The virtual environment has all the project dependencies installed (FastAPI, SQLAlchemy, WeasyPrint, etc.). System Python doesn't.

---

## WeasyPrint and GTK+ Requirement

### What is WeasyPrint?
WeasyPrint converts HTML to PDF. It's like printing a webpage to PDF programmatically.

### What is GTK+?
GTK+ is a graphics library that WeasyPrint needs to render fonts, images, and layouts properly.

- **On Linux**: GTK+ is usually pre-installed ✅
- **On Windows**: You must install it manually ❌

### Why the GitHub Repo?
The GTK+ installer is hosted on GitHub because it's a community-maintained Windows build of the Linux library.

---

## Step-by-Step: Installing GTK+ on Windows

### Step 1: Download the GTK+ Installer

1. Go to: https://github.com/tschoonj/GTK-for-Windows-Runtime-Environment-Installer/releases

2. Find the **latest release** (scroll down to "Releases" section on the right)

3. Download the **.exe installer** (NOT the source code):
   ```
   Example file name: gtk3-runtime-3.24.31-2022-01-04-ts-win64.exe
   ```

### Step 2: Run the Installer

1. Double-click the downloaded `.exe` file

2. Click "Yes" if Windows asks for permission

3. Follow the installer prompts:
   - **Installation Path**: Use default `C:\Program Files\GTK3-Runtime Win64`
   - **Components**: Select all (default)
   - Click "Install"

4. Wait for installation to complete (takes 2-3 minutes)

5. Click "Finish"

### Step 3: Restart Your Terminal

**IMPORTANT**: Close and reopen PowerShell/Command Prompt/VS Code terminal.

This ensures the system recognizes the new GTK+ installation.

### Step 4: Verify Installation

```powershell
# Activate virtual environment
cd "C:\Users\SuryaRaman_9t430wh\Downloads\Devsecops - Jira\Devsecops_BE"
.venv\Scripts\activate

# Test WeasyPrint
python -c "from weasyprint import HTML; print('WeasyPrint is working!')"
```

**Expected output**:
```
WeasyPrint is working!
```

**If you see an error about `libgobject-2.0-0`**:
- GTK+ is not installed correctly
- Make sure you restarted your terminal
- Try reinstalling GTK+ and select "Add to PATH" option

---

## Testing the Report Generation System

Now that GTK+ is installed, follow these steps in order:

### Test 1: Update Database Templates

This loads the professional templates into your database:

```powershell
# Make sure virtual environment is activated
.venv\Scripts\activate

# Update templates in database
python scripts/update_email_templates.py
```

**What this does**:
- Reads professional HTML templates from `database_templates/` folder
- Updates the `email_templates` table in your database
- These templates include ZEB Company branding

**Expected output**:
```
Template: Weekly Digest
  File: weekly_digest_professional.html
  Size: 15,234 characters
  [SUCCESS] Updated in database (1 row(s))

Template: At Risk Alert
  File: at_risk_alert_professional.html
  Size: 18,567 characters
  [SUCCESS] Updated in database (1 row(s))
```

---

### Test 2: Test Template Rendering (No PDF)

This tests that templates can be rendered with sample data:

```powershell
python test_template_rendering.py
```

**What this does**:
- Tests Jinja2 template rendering
- Uses sample data (no database required)
- Saves HTML files to `test_html_output/` folder
- **Does NOT generate PDFs** (so it works even without GTK+)

**Expected output**:
```
[PASS] Template rendered successfully
  HTML size: 15,234 characters
  Contains specialization: Cloud Platform Engineering
[PASS] HTML saved to: test_html_output\weekly_digest_test.html
```

**What to check**:
- Open the HTML files in your browser
- Verify they look professional (ZEB Company logo, nice styling)
- Check that sample data appears correctly

---

### Test 3: Test PDF Generation (Requires GTK+)

This generates actual PDF files:

```powershell
python test_pdf_generation.py
```

**What this does**:
- Renders templates with sample data
- Converts HTML to PDF using WeasyPrint
- Saves PDF files to `test_pdfs/` folder

**Expected output**:
```
============================================================
Generating PDF: weekly_digest_test.pdf
Template: weekly_digest.html
============================================================
[PASS] Template rendered successfully (15234 chars)
[PASS] PDF generated in memory (245678 bytes)
[PASS] PDF saved to: test_pdfs\weekly_digest_test.pdf
  File size: 239.92 KB
```

**What to check**:
- Open the PDF files from `test_pdfs/` folder
- Verify they look professional and print-ready
- Check page layout and formatting

**If this fails**:
- Make sure GTK+ is installed (see Step 4 above)
- Restart your terminal
- Check that you're using the virtual environment

---

### Test 4: Test Complete API Flow

This tests the entire system from API to database to email:

#### Step 4a: Start the Server

```powershell
# Terminal 1
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

**Expected output**:
```
INFO:     Application starting up
INFO:     Settings validated successfully
INFO:     Database migration check completed
INFO:     Uvicorn running on http://127.0.0.1:8000
```

#### Step 4b: Test the API

In a **new terminal** (keep the server running):

```powershell
# Terminal 2
cd "C:\Users\SuryaRaman_9t430wh\Downloads\Devsecops - Jira\Devsecops_BE"
.venv\Scripts\activate

# Test the API
python test_api_endpoint.py
```

**OR** use curl:

```powershell
curl -X GET http://127.0.0.1:8000/api/v1/reports/generate
```

**Expected response**:
```json
{
  "status_code": 200,
  "status": "success",
  "message": "Email sent successfully",
  "data": []
}
```

**What this does**:
- Fetches active specializations from database
- Reads templates from `email_templates` table
- Renders templates with real data
- Generates PDFs
- Uploads to S3 (or uses placeholder if not configured)
- Sends emails to configured recipients

---

## Troubleshooting

### Error: "ModuleNotFoundError: No module named 'weasyprint'"

**Cause**: Dependencies not installed

**Fix**:
```powershell
.venv\Scripts\activate
pip install -e .
```

---

### Error: "cannot load library 'libgobject-2.0-0'"

**Cause**: GTK+ not installed or terminal not restarted

**Fix**:
1. Install GTK+ (see "Installing GTK+ on Windows" section above)
2. **Restart your terminal** (very important!)
3. Try again

---

### Error: "Connection refused" when testing API

**Cause**: Server is not running

**Fix**:
```powershell
# Start the server first
uvicorn main:app --host 127.0.0.1 --port 8000 --reload
```

---

### Warning: "No active specializations"

**Cause**: Database is empty or no specializations configured

**Fix**: This is expected if you haven't seeded the database yet. The API still works, it just has nothing to report.

To seed the database:
```powershell
python scripts/load_data.py
```

---

### Templates Don't Have Company Logo

**Cause**: Old templates still in database

**Fix**:
```powershell
# Update to new professional templates
python scripts/update_email_templates.py
```

---

## Alternative: Skip GTK+ Installation

If you don't want to install GTK+ on Windows, you have options:

### Option 1: Test HTML Only (No PDFs)
```powershell
# This works without GTK+
python test_template_rendering.py
```

### Option 2: Use Docker
```powershell
# Build and run in Docker (Linux has GTK+ built-in)
docker-compose up
docker exec -it devsecops-backend python test_pdf_generation.py
```

### Option 3: Use WSL2 (Windows Subsystem for Linux)
```powershell
# Install WSL2 first, then:
wsl
cd /mnt/c/Users/SuryaRaman_9t430wh/Downloads/Devsecops\ -\ Jira/Devsecops_BE
python3 -m venv .venv
source .venv/bin/activate
pip install -e .
python test_pdf_generation.py
```

---

## Summary: What You Need to Know

1. **Use Virtual Environment**: Always activate `.venv` before running commands

2. **Install GTK+**: Required for PDF generation on Windows
   - Download from GitHub releases (not clone)
   - Run the .exe installer
   - Restart terminal after installing

3. **Update Templates**: Run `python scripts/update_email_templates.py` to load professional templates

4. **Test in Order**:
   1. Update database templates
   2. Test HTML rendering
   3. Test PDF generation (needs GTK+)
   4. Test API endpoint (needs server running)

5. **Two Pythons Explained**:
   - **System Python**: Your global installation
   - **Virtual Environment**: Project-specific (THIS ONE!)

---

## Quick Reference

```powershell
# Activate virtual environment
cd "C:\Users\SuryaRaman_9t430wh\Downloads\Devsecops - Jira\Devsecops_BE"
.venv\Scripts\activate

# Update templates in database
python scripts/update_email_templates.py

# Test HTML rendering (no GTK+ needed)
python test_template_rendering.py

# Test PDF generation (needs GTK+)
python test_pdf_generation.py

# Start server
uvicorn main:app --host 127.0.0.1 --port 8000 --reload

# Test API (in new terminal)
python test_api_endpoint.py
```

---

## Need Help?

1. Check application logs: `logs/application.log`
2. Verify database connection in `.env` file
3. Make sure all environment variables are set
4. Review error traces in `error_logs` table

---

**That's it!** Follow these steps and you'll have professional PDF reports with ZEB Company branding working on Windows.
