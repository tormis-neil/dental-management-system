# 🧪 Manual Testing Guide
## Dental Clinic Management System

This guide provides step-by-step instructions for manually testing all features of the Dental Clinic Management System.

**Purpose:** Help identify bugs, verify functionality, and ensure proper behavior for academic demo.

---

## 📋 Table of Contents

1. [Testing Environment Setup](#testing-environment-setup)
2. [Test User Accounts](#test-user-accounts)
3. [Authentication Testing](#authentication-testing)
4. [Patient Management Testing](#patient-management-testing)
5. [Staff Management Testing](#staff-management-testing)
6. [Role-Based Access Testing](#role-based-access-testing)
7. [Backup & Restore Testing](#backup--restore-testing)
8. [Audit Log Testing](#audit-log-testing)
9. [UI/UX Testing](#uiux-testing)
10. [Bug Reporting Template](#bug-reporting-template)

---

## 🔧 Testing Environment Setup

### Prerequisites
```bash
# 1. Ensure application is running
python3 app.py

# 2. Verify URL is accessible
# Open browser: http://localhost:5000

# 3. Clear browser cache (optional but recommended)
# Chrome: Ctrl+Shift+Delete
# Firefox: Ctrl+Shift+Delete
```

### Browser Compatibility Testing

Test in multiple browsers:
- [ ] Chrome/Edge (Chromium)
- [ ] Firefox
- [ ] Safari (if on Mac)
- [ ] Mobile browser (optional)

---

## 👥 Test User Accounts

### Default Accounts

| Username | Password | Role | Purpose |
|----------|----------|------|---------|
| `manager` | `12345` | Manager | Full system access |
| `STAFF-001` | `staff123` | Staff | Limited access testing |

### Creating Additional Test Accounts

1. Login as `manager`
2. Go to "Staff" menu
3. Click "Add New Staff"
4. Create test accounts:

**Test Dentist:**
- Username: `dentist01`
- Password: `Test123!`
- Full Name: `Dr. Test Dentist`
- Email: `dentist@test.com`
- Role: dentist (modify in database if needed)

**Test Staff:**
- Username: `nurse01`
- Password: `Test123!`
- Full Name: `Test Nurse`
- Email: `nurse@test.com`

---

## 🔐 Authentication Testing

### Test 1: Successful Login (Manager)

**Steps:**
1. Navigate to http://localhost:5000
2. Verify you're redirected to `/login`
3. Enter username: `manager`
4. Enter password: `12345`
5. Click "Log in" button

**Expected Result:**
- ✅ Redirected to `/dashboard`
- ✅ Welcome message appears: "Welcome back, Clinic Manager!"
- ✅ Navbar shows user name and role badge "MANAGER"
- ✅ All menu items visible: Dashboard, Patients, Staff, Backup, Audit Logs

**Status:** [ ] Pass [ ] Fail

**Notes:**
```
_________________________________________________
_________________________________________________
```

---

### Test 2: Failed Login (Invalid Credentials)

**Steps:**
1. Navigate to login page
2. Enter username: `invalid`
3. Enter password: `wrongpass`
4. Click "Log in"

**Expected Result:**
- ✅ Stays on login page
- ✅ Error message: "Invalid username or password."
- ✅ Message has red/danger styling
- ❌ No redirect to dashboard

**Status:** [ ] Pass [ ] Fail

---

### Test 3: Password Visibility Toggle

**Steps:**
1. On login page, enter password: `test123`
2. Click the eye icon in password field

**Expected Result:**
- ✅ Password becomes visible as plain text
- ✅ Eye icon changes to "eye-slash"
- ✅ Click again to hide password

**Status:** [ ] Pass [ ] Fail

---

### Test 4: Logout Functionality

**Steps:**
1. Login as any user
2. Click user dropdown (top right)
3. Click "Logout"

**Expected Result:**
- ✅ Redirected to `/login`
- ✅ Success message: "You have been logged out."
- ✅ Cannot access `/dashboard` without logging in again
- ✅ Session cleared (check by trying to navigate to `/dashboard`)

**Status:** [ ] Pass [ ] Fail

---

## 👤 Patient Management Testing

### Test 5: Add New Patient (Manager/Dentist)

**Steps:**
1. Login as `manager`
2. Click "Patients" in navbar
3. Click "Add New Patient" button
4. Fill in form:
   - First Name: `John`
   - Last Name: `Doe`
   - Date of Birth: `1990-05-15`
   - Gender: `Male`
   - Phone: `555-1234`
   - Email: `john.doe@example.com`
   - Address: `123 Test St`
   - Emergency Contact Name: `Jane Doe`
   - Emergency Contact Phone: `555-5678`
   - Allergies: `Penicillin`
   - Existing Condition: `None`
   - Dentist Notes: `Regular checkup needed`
   - Assigned Dentist: `Dr. Smith`
5. Click "Add Patient"

**Expected Result:**
- ✅ Redirected to `/patients`
- ✅ Success message: "Patient added successfully!"
- ✅ Patient appears in patient list
- ✅ Age is automatically calculated (should show ~35 years)

**Status:** [ ] Pass [ ] Fail

---

### Test 6: Add Patient with Minimum Fields

**Steps:**
1. Click "Add New Patient"
2. Fill ONLY required fields:
   - First Name: `Jane`
   - Last Name: `Smith`
3. Leave all other fields empty
4. Click "Add Patient"

**Expected Result:**
- ✅ Patient added successfully
- ✅ Optional fields are empty/null in database
- ✅ No errors thrown

**Status:** [ ] Pass [ ] Fail

---

### Test 7: Add Patient with Missing Required Fields

**Steps:**
1. Click "Add New Patient"
2. Leave First Name empty
3. Enter Last Name: `Test`
4. Try to submit

**Expected Result:**
- ✅ Error message: "First Name and Last Name are required."
- ✅ Form not submitted
- ✅ User stays on add patient page

**Status:** [ ] Pass [ ] Fail

---

### Test 8: Search Patients

**Steps:**
1. Go to Patients page
2. In search box, type: `John`
3. Click "Filter" button

**Expected Result:**
- ✅ Only patients with "John" in name/phone/ID appear
- ✅ Search is case-insensitive
- ✅ Search term remains in search box

**Status:** [ ] Pass [ ] Fail

---

### Test 9: Filter Patients by Gender

**Steps:**
1. Go to Patients page
2. Select "Male" from gender dropdown
3. Click "Filter"

**Expected Result:**
- ✅ Only male patients displayed
- ✅ Filter persists when navigating back
- ✅ "Clear" button appears

**Status:** [ ] Pass [ ] Fail

---

### Test 10: View Patient Details

**Steps:**
1. Go to Patients page
2. Click "View" button on any patient

**Expected Result:**
- ✅ Redirected to `/patients/view/<id>`
- ✅ All patient information displayed
- ✅ Age is shown correctly
- ✅ Medical information visible (if user is manager/dentist)
- ✅ "Edit" and "Back to Patients" buttons present

**Status:** [ ] Pass [ ] Fail

---

### Test 11: Edit Patient Information (Manager)

**Steps:**
1. View a patient
2. Click "Edit Patient" button
3. Change First Name to: `Updated Name`
4. Click "Update Patient"

**Expected Result:**
- ✅ Redirected to patients list
- ✅ Success message: "Patient updated successfully!"
- ✅ Changes reflected in patient list
- ✅ Audit log records the edit

**Status:** [ ] Pass [ ] Fail

---

### Test 12: Delete Patient (Manager Direct Delete)

**Steps:**
1. Login as `manager`
2. Go to Patients page
3. Click "Delete" button on a test patient
4. Confirm deletion (if prompt exists)

**Expected Result:**
- ✅ Patient immediately deleted
- ✅ Success message: "Patient deleted successfully!"
- ✅ Patient removed from list
- ✅ Audit log records deletion

**Status:** [ ] Pass [ ] Fail

---

### Test 13: Request Patient Deletion (Staff)

**Steps:**
1. Logout and login as `STAFF-001` / `staff123`
2. Go to Patients page
3. Click "Request Delete" button on a patient
4. Confirm request

**Expected Result:**
- ✅ Success message: "Deletion request sent for approval."
- ✅ Patient still visible in list
- ✅ "Request Delete" button may change state
- ✅ Pending request created in database

**Status:** [ ] Pass [ ] Fail

---

### Test 14: Age Calculation Accuracy

**Steps:**
1. Add patient with DOB: `2000-01-01`
2. View patient details

**Expected Result:**
- ✅ Age shown as 25 years (as of 2025)
- ✅ Age updates correctly based on current date

**Test Cases:**
| Date of Birth | Expected Age (2025) | Actual Age | Pass/Fail |
|---------------|---------------------|------------|-----------|
| 2000-01-01 | 25 | _____ | [ ] |
| 1990-06-15 | 35 | _____ | [ ] |
| 2010-12-31 | 15 | _____ | [ ] |

**Status:** [ ] Pass [ ] Fail

---

## 👨‍💼 Staff Management Testing

### Test 15: Add New Staff (Manager Only)

**Steps:**
1. Login as `manager`
2. Click "Staff" in navbar
3. Click "Add New Staff"
4. Fill form:
   - Username: `teststaff`
   - Password: `Test123!`
   - Full Name: `Test Staff Member`
   - Email: `teststaff@example.com`
5. Click "Add Staff"

**Expected Result:**
- ✅ Success message: "Staff member added successfully!"
- ✅ Redirected to staff list
- ✅ New staff appears in list
- ✅ Staff can login with credentials

**Status:** [ ] Pass [ ] Fail

---

### Test 16: Duplicate Username Prevention

**Steps:**
1. Try to add staff with username: `manager` (already exists)
2. Submit form

**Expected Result:**
- ✅ Error message: "Username already exists!"
- ✅ Staff not created
- ✅ Form stays on add staff page

**Status:** [ ] Pass [ ] Fail

---

### Test 17: Edit Staff Information

**Steps:**
1. Go to Staff page
2. Click "Edit" on a staff member
3. Change Full Name to: `Updated Staff Name`
4. Click "Update Staff"

**Expected Result:**
- ✅ Success message: "Staff member updated!"
- ✅ Changes reflected in staff list
- ✅ Audit log records the change

**Status:** [ ] Pass [ ] Fail

---

### Test 18: Deactivate Staff Account

**Steps:**
1. Edit a staff member
2. Uncheck "Active" checkbox
3. Save changes
4. Try to login as that staff member

**Expected Result:**
- ✅ Staff status shows as inactive in list
- ✅ Login attempt fails with appropriate message
- ✅ Staff account disabled

**Status:** [ ] Pass [ ] Fail

---

### Test 19: Change Staff Password

**Steps:**
1. Edit staff member
2. Enter new password: `NewPass123!`
3. Save changes
4. Logout
5. Login as staff with new password

**Expected Result:**
- ✅ Password successfully updated
- ✅ Old password no longer works
- ✅ New password allows login

**Status:** [ ] Pass [ ] Fail

---

### Test 20: Delete Staff Member

**Steps:**
1. Go to Staff page
2. Click "Delete" on a test staff member
3. Confirm deletion

**Expected Result:**
- ✅ Success message: "Staff member deleted."
- ✅ Staff removed from list
- ✅ Cannot login with deleted account
- ✅ Audit log records deletion

**Status:** [ ] Pass [ ] Fail

---

## 🔒 Role-Based Access Testing

### Test 21: Staff Cannot Access Staff Management

**Steps:**
1. Login as `STAFF-001`
2. Try to navigate to: http://localhost:5000/staff

**Expected Result:**
- ✅ Redirected to dashboard
- ✅ Error message: "Access denied. Manager privileges required."
- ✅ "Staff" menu not visible in navbar

**Status:** [ ] Pass [ ] Fail

---

### Test 22: Staff Cannot Access Backup Page

**Steps:**
1. Login as `STAFF-001`
2. Try to navigate to: http://localhost:5000/backup

**Expected Result:**
- ✅ Redirected to dashboard
- ✅ Error message: "Access denied. Manager privileges required."
- ✅ "Backup" menu not visible in navbar

**Status:** [ ] Pass [ ] Fail

---

### Test 23: Staff Cannot Delete Patients Directly

**Steps:**
1. Login as `STAFF-001`
2. Go to Patients page
3. Verify buttons available

**Expected Result:**
- ✅ "Delete" button NOT visible
- ✅ Only "Request Delete" button available
- ✅ Cannot directly access delete URL

**Status:** [ ] Pass [ ] Fail

---

### Test 24: Staff Cannot Edit Medical Information

**Steps:**
1. Login as `STAFF-001`
2. Edit a patient
3. Check form fields

**Expected Result:**
- ✅ Cannot see/edit: Allergies, Existing Condition, Dentist Notes
- ✅ Can edit: Basic info (name, phone, address, etc.)
- ✅ Medical fields not visible or disabled

**Status:** [ ] Pass [ ] Fail

---

### Test 25: Manager Can Access All Features

**Steps:**
1. Login as `manager`
2. Verify all menu items visible

**Expected Result:**
- ✅ Dashboard visible
- ✅ Patients visible
- ✅ Staff visible
- ✅ Backup visible
- ✅ Audit Logs visible
- ✅ Can perform all CRUD operations

**Status:** [ ] Pass [ ] Fail

---

### Test 26: Pending Request Approval (Manager)

**Steps:**
1. Staff creates deletion request (Test 13)
2. Logout and login as `manager`
3. Go to Dashboard
4. Check "Recent Pending Deletion Requests" section
5. Click "Approve" button

**Expected Result:**
- ✅ Pending request appears on dashboard
- ✅ "Approve" button works
- ✅ Patient is deleted after approval
- ✅ Success message: "Deletion request approved and patient record removed."
- ✅ Request no longer pending

**Status:** [ ] Pass [ ] Fail

---

### Test 27: Pending Request Denial (Manager)

**Steps:**
1. Staff creates deletion request
2. Login as `manager`
3. Go to "Pending Requests" page
4. Click "Deny" button

**Expected Result:**
- ✅ Request marked as denied
- ✅ Patient NOT deleted
- ✅ Success message: "Deletion request denied."
- ✅ Request removed from pending list

**Status:** [ ] Pass [ ] Fail

---

## 💾 Backup & Restore Testing

### Test 28: Create Database Backup

**Steps:**
1. Login as `manager`
2. Go to "Backup" page
3. Click "Create New Backup" button
4. Wait for backup to complete

**Expected Result:**
- ✅ Success message: "Backup created successfully!"
- ✅ New backup appears in backup list
- ✅ Filename format: `backup_YYYYMMDD_HHMMSS.db`
- ✅ File size displayed
- ✅ Backup file created in `backups/` folder

**Status:** [ ] Pass [ ] Fail

---

### Test 29: Download Backup File

**Steps:**
1. Go to Backup page
2. Click "Download" button on a backup

**Expected Result:**
- ✅ File downloads successfully
- ✅ Filename matches displayed name
- ✅ File is a valid SQLite database
- ✅ Can be opened with SQLite browser

**Status:** [ ] Pass [ ] Fail

---

### Test 30: Restore from Backup

**Steps:**
1. Note current patient count
2. Delete a patient
3. Go to Backup page
4. Click "Restore" on a previous backup
5. Confirm restoration

**Expected Result:**
- ✅ Success message: "Database successfully restored from backup!"
- ✅ Deleted patient reappears
- ✅ Data matches backup point in time
- ✅ Application continues to function

**Status:** [ ] Pass [ ] Fail

---

### Test 31: Multiple Backups Management

**Steps:**
1. Create 3 backups with different timestamps
2. Verify all appear in list
3. Try downloading each one

**Expected Result:**
- ✅ All backups listed chronologically (newest first)
- ✅ Each has unique timestamp
- ✅ Each can be downloaded individually
- ✅ File sizes may vary based on data

**Status:** [ ] Pass [ ] Fail

---

## 📊 Audit Log Testing

### Test 32: Login Activity Logged

**Steps:**
1. Logout
2. Login as `manager`
3. Go to "Audit Logs" page
4. Find most recent entry

**Expected Result:**
- ✅ Entry shows: LOGIN action
- ✅ Username: manager
- ✅ Details: "User logged in"
- ✅ Timestamp is recent and accurate

**Status:** [ ] Pass [ ] Fail

---

### Test 33: Patient Operations Logged

**Steps:**
1. Add a patient
2. Edit the patient
3. Delete the patient
4. Check Audit Logs

**Expected Result:**
Three log entries:
- ✅ ADD_PATIENT: "Added patient [name]"
- ✅ EDIT_PATIENT: "Edited patient ID [id]"
- ✅ DELETE_PATIENT: "Deleted patient ID [id]"
- ✅ All have correct timestamps and usernames

**Status:** [ ] Pass [ ] Fail

---

### Test 34: Staff Can Only View Own Logs

**Steps:**
1. Login as `STAFF-001`
2. Perform some actions (add patient)
3. Go to Audit Logs
4. Check visible logs

**Expected Result:**
- ✅ Only logs for STAFF-001 visible
- ✅ Cannot see manager's actions
- ✅ Cannot see other staff's actions

**Status:** [ ] Pass [ ] Fail

---

### Test 35: Manager Can View All Logs

**Steps:**
1. Login as `manager`
2. Go to Audit Logs

**Expected Result:**
- ✅ Can see logs from all users
- ✅ Logs include: manager, staff, dentist actions
- ✅ Limit of 100 recent logs displayed

**Status:** [ ] Pass [ ] Fail

---

## 🎨 UI/UX Testing

### Test 36: Responsive Design - Desktop

**Steps:**
1. Open application in desktop browser (1920x1080)
2. Navigate through all pages

**Expected Result:**
- ✅ Layout looks professional
- ✅ No horizontal scrolling
- ✅ Tables fit within viewport
- ✅ Cards are properly sized
- ✅ Navigation bar displays correctly

**Status:** [ ] Pass [ ] Fail

---

### Test 37: Responsive Design - Mobile

**Steps:**
1. Resize browser to 375x667 (iPhone SE size)
2. OR use browser dev tools device emulation
3. Navigate through pages

**Expected Result:**
- ✅ Navbar collapses to hamburger menu
- ✅ Cards stack vertically
- ✅ Forms are usable
- ✅ Buttons are touchable (min 44x44px)
- ✅ Text is readable without zooming

**Status:** [ ] Pass [ ] Fail

**Issues Found:**
```
Tables may overflow - needs horizontal scroll
_________________________________________________
```

---

### Test 38: Login Page Animations

**Steps:**
1. Clear cache
2. Navigate to login page
3. Watch animations

**Expected Result:**
- ✅ Left panel slides in from left
- ✅ Logo has gentle sway animation
- ✅ Animations are smooth (no jank)
- ✅ Page loads within 2 seconds

**Status:** [ ] Pass [ ] Fail

---

### Test 39: Flash Messages Auto-Dismiss

**Steps:**
1. Trigger any success message (e.g., add patient)
2. Wait and observe

**Expected Result:**
- ✅ Message appears at top of page
- ✅ Message auto-dismisses after ~5 seconds
- ✅ Dismiss button (X) works immediately
- ✅ Message styling matches type (success=green, danger=red)

**Status:** [ ] Pass [ ] Fail

---

### Test 40: Form Validation Feedback

**Steps:**
1. Go to Add Patient form
2. Leave required field empty
3. Try to submit

**Expected Result:**
- ✅ Browser validation appears ("Please fill out this field")
- ✅ Required fields marked with red asterisk (*)
- ✅ Focus moves to first invalid field

**Status:** [ ] Pass [ ] Fail

---

### Test 41: Button Loading States

**Steps:**
1. Submit any form (e.g., login, add patient)
2. Observe button during submission

**Expected Result:**
- ✅ Button shows spinner/loading state
- ✅ Button text changes to "Processing..."
- ✅ Button is disabled during submission
- ✅ Prevents double-submission

**Status:** [ ] Pass [ ] Fail

---

### Test 42: Navigation Active States

**Steps:**
1. Click through each navigation menu item
2. Observe which item is highlighted

**Expected Result:**
- ✅ Current page highlighted in navbar
- ✅ Active link has different background color
- ✅ User always knows which page they're on

**Status:** [ ] Pass [ ] Fail

---

### Test 43: Dashboard Statistics Cards

**Steps:**
1. Login and go to dashboard
2. Observe statistics cards

**Expected Result:**
- ✅ "Total Patients" shows correct count
- ✅ "Staff Members" shows correct count (managers only)
- ✅ "Your Role" displays user's role
- ✅ Cards are clickable and link to relevant pages
- ✅ Hover effect works (card lifts up)

**Status:** [ ] Pass [ ] Fail

---

### Test 44: Search and Filter UI

**Steps:**
1. Go to Patients page
2. Enter search term
3. Select gender filter
4. Submit filters

**Expected Result:**
- ✅ Search icon visible in search box
- ✅ Filter button has funnel icon
- ✅ "Clear" button appears after filtering
- ✅ Applied filters persist in form fields
- ✅ Results update immediately

**Status:** [ ] Pass [ ] Fail

---

### Test 45: Table Sorting (if implemented)

**Steps:**
1. Go to Patients page
2. Click on table headers

**Expected Result:**
- [ ] Headers are clickable
- [ ] Sort order indicator appears
- [ ] Data sorts ascending/descending
- [ ] Multiple clicks toggle sort direction

**Status:** [ ] Pass [ ] Fail [ ] N/A (Not Implemented)

---

## 🔍 Security Testing

### Test 46: CSRF Token Protection

**Steps:**
1. Login to application
2. Open browser dev tools (F12)
3. Go to Network tab
4. Submit a form (e.g., add patient)
5. Inspect request

**Expected Result:**
- ✅ Request includes `csrf_token` parameter
- ✅ Form has hidden CSRF token field
- ✅ Token is unique per session

**Status:** [ ] Pass [ ] Fail

---

### Test 47: CSRF Token Validation

**Steps:**
1. Use curl or Postman to submit form without CSRF token:
```bash
curl -X POST http://localhost:5000/login \
  -d "username=manager&password=12345"
```

**Expected Result:**
- ✅ Request is rejected
- ✅ Error: 400 Bad Request or CSRF validation error
- ✅ Login does not succeed

**Status:** [ ] Pass [ ] Fail

---

### Test 48: Password Hashing Verification

**Steps:**
1. Access database directly:
```bash
python3 -c "
import sqlite3
conn = sqlite3.connect('dental_clinic.db')
cursor = conn.cursor()
cursor.execute('SELECT username, password_hash FROM users')
for row in cursor.fetchall():
    print(f'{row[0]}: {row[1][:20]}...')
conn.close()
"
```

**Expected Result:**
- ✅ Passwords NOT stored in plain text
- ✅ Hash format: `pbkdf2:sha256:...` or similar
- ✅ Each user has different hash even if same password

**Status:** [ ] Pass [ ] Fail

---

### Test 49: SQL Injection Prevention

**Steps:**
1. In search box, try: `' OR '1'='1`
2. In username field, try: `admin' --`
3. Submit forms

**Expected Result:**
- ✅ No SQL errors thrown
- ✅ Input treated as literal string
- ✅ No unauthorized access granted
- ✅ Application handles input safely

**Status:** [ ] Pass [ ] Fail

---

### Test 50: Unauthorized Route Access

**Steps:**
1. Logout (or use incognito mode)
2. Try to access: http://localhost:5000/dashboard
3. Try to access: http://localhost:5000/patients
4. Try to access: http://localhost:5000/staff

**Expected Result:**
- ✅ All routes redirect to `/login`
- ✅ No data visible without authentication
- ✅ Message: "Please log in to access this page" (if applicable)

**Status:** [ ] Pass [ ] Fail

---

### Test 51: Session Security

**Steps:**
1. Login as manager
2. Copy session cookie value (from dev tools)
3. Logout
4. Try to restore cookie and access dashboard

**Expected Result:**
- ✅ Session invalidated on logout
- ✅ Old session cookie doesn't work
- ✅ Must login again

**Status:** [ ] Pass [ ] Fail

---

## 🐛 Known Issues & Workarounds

### Issue 1: Tables Overflow on Mobile
**Description:** Patient/staff tables extend beyond screen width on mobile devices

**Workaround:** Scroll horizontally, or use desktop view

**Priority:** Low (academic demo)

**Status:** [ ] Fixed [ ] Known Issue

---

### Issue 2: No Confirmation Dialogs
**Description:** Delete actions don't ask for confirmation

**Workaround:** Be careful when clicking delete buttons

**Priority:** Medium

**Status:** [ ] Fixed [ ] Known Issue

---

### Issue 3: Password Strength Not Enforced (Backend)
**Description:** Weak passwords accepted despite frontend validation

**Workaround:** Manually enter strong passwords

**Priority:** Medium (security)

**Status:** [ ] Fixed [ ] Known Issue

---

## 📝 Bug Reporting Template

When you find a bug, use this template:

```
### Bug Report #___

**Date:** ____________
**Tester:** ____________
**Browser:** ____________

**Title:** Short description of bug

**Steps to Reproduce:**
1.
2.
3.

**Expected Result:**


**Actual Result:**


**Screenshots:** (if applicable)


**Error Messages:** (copy from console/logs)


**Severity:**
[ ] Critical (blocks major functionality)
[ ] High (major feature broken)
[ ] Medium (feature partially broken)
[ ] Low (cosmetic, minor issue)

**Frequency:**
[ ] Always
[ ] Sometimes
[ ] Rarely

**Workaround:** (if any)


**Additional Notes:**


```

---

## ✅ Testing Checklist Summary

### Core Functionality
- [ ] Login/Logout works correctly
- [ ] Role-based access enforced
- [ ] Patient CRUD operations functional
- [ ] Staff CRUD operations functional (manager)
- [ ] Search and filter work
- [ ] Audit logging captures all actions
- [ ] Backup and restore work
- [ ] Pending request workflow functions

### Security
- [ ] CSRF protection enabled
- [ ] Passwords hashed (not plain text)
- [ ] SQL injection prevented
- [ ] Unauthorized access blocked
- [ ] Sessions managed securely

### UI/UX
- [ ] Responsive on desktop
- [ ] Responsive on mobile
- [ ] Animations work smoothly
- [ ] Forms validate properly
- [ ] Flash messages display
- [ ] Navigation clear and functional

### Cross-Browser
- [ ] Chrome/Edge
- [ ] Firefox
- [ ] Safari (if available)

---

## 📊 Test Results Summary

**Total Tests:** 51
**Passed:** _____
**Failed:** _____
**Not Applicable:** _____

**Pass Rate:** _____%

**Critical Issues Found:** _____

**Recommendation:**
- [ ] Ready for demo
- [ ] Minor fixes needed
- [ ] Major fixes needed
- [ ] Not ready for demo

---

## 🎯 Testing Tips

1. **Test in Order:** Follow tests sequentially to build test data
2. **Use Real Data:** Don't use "test test test" - use realistic names
3. **Take Screenshots:** Capture bugs immediately
4. **Check Console:** Always have browser console open (F12)
5. **Clear Cache:** If something breaks, try clearing browser cache
6. **Fresh Start:** For critical tests, restart app and use fresh database

### Before Each Testing Session:
```bash
# 1. Restart application
pkill -f "python3 app.py"
python3 app.py

# 2. Clear browser cache
# Chrome: Ctrl+Shift+Delete

# 3. Open browser console (F12)
```

---

## 🔄 Regression Testing

After any bug fix, re-test:
- [ ] The specific bug that was fixed
- [ ] Related functionality
- [ ] Login/logout (always test)
- [ ] All role-based access controls
- [ ] At least 5 critical path tests

---

## 📞 Support

If you encounter issues during testing:

1. Check `README.md` Troubleshooting section
2. Check `QA_TESTING_REPORT.md` for known limitations
3. Restart application: `python3 app.py`
4. Delete database to reset: `rm dental_clinic.db`

---

**Happy Testing! 🧪**

*Last Updated: November 2025*
