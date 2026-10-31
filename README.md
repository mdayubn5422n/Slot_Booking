# SlotBook - Appointment Booking Platform (Django)

SlotBook lets small businesses (salons, clinics, tutors, gyms, photographers, pet groomers) take bookings online.

**Three roles**
| Role | Who | What they can do |
|---|---|---|
| Customer | signs up on the site | search businesses, book a free slot, see/cancel bookings, print confirmation |
| Business Owner | signs up on the site | add business + image, services, working hours; confirm/complete/cancel bookings |
| Platform Admin | created with `createsuperuser` | uses `/admin/` to add categories, home page images, FAQs, and see everything |

Tech: Python 3.12, Django 5.2 LTS, Django templates, HTML/CSS/JS, SQLite (local) with PostgreSQL for live, Django test framework.

---

## PART 1 - Run it on your Windows PC (Command Prompt)

Use **Command Prompt** (press the Windows key, type `cmd`, press Enter). Type each command, then press Enter.

### Step 1 - Install Python 3.12
1. Go to https://www.python.org/downloads/ and install Python 3.12.
2. On the first installer screen, tick **"Add python.exe to PATH"**, then click Install.
3. Check it worked:
```
python --version
```
You should see `Python 3.12.x`.

### Step 2 - Unzip and open the project
1. Right-click `slotbook.zip` and choose **Extract All**.
2. In Command Prompt go into the folder (change the path to where you extracted it):
```
cd C:\Users\YourName\Downloads\slotbook
```
You should see `manage.py` when you run `dir`.

### Step 3 - Make a virtual environment (a private box for this project's packages)
```
python -m venv venv
venv\Scripts\activate
```
Your prompt now starts with `(venv)`. **Every time you open a new Command Prompt, run `venv\Scripts\activate` again.**

### Step 4 - Install the packages
```
pip install -r requirements.txt
```

### Step 5 - Create the database tables
```
python manage.py makemigrations accounts bookings
python manage.py migrate
```

### Step 6 - Add starter categories and FAQs
```
python manage.py seed_basics
```
This adds 6 categories (Salon, Clinic, Tutor, Gym, Photographer, Pet Grooming) and 5 FAQs. It adds **no images**. You can run it again safely.

### Step 7 - Create the Platform Admin account
```
python manage.py createsuperuser
```
Type a username, email and password (the password does not show while you type - that is normal).

### Step 8 - Start the website
```
python manage.py runserver
```
Open http://127.0.0.1:8000/ in your browser. Press `Ctrl + C` in the Command Prompt to stop the server.

### Step 9 - Upload your images (Platform Admin)
Open http://127.0.0.1:8000/admin/ and log in with the admin account.
- **Category images:** Admin > Categories > open a category > "Image" > Choose file > Save.
- **Home page images:** Admin > Site images > Add. Pick "Home page - main banner" (and "Home page - about section", "Contact page image"), choose the file, write a short alt text, Save.
- **Business images:** a Business Owner uploads this on the "Add a business" / "Edit details" page. The Platform Admin can also do it in Admin > Businesses.

Images must be under 5 MB (JPG, PNG, WebP). Until you upload an image, a plain "No image yet" box is shown.

### Step 10 - Try the whole flow
1. Open the site in a normal window, click **Sign up**, choose **Business Owner**. Add a business, then on the Manage page add a service and working hours (e.g. every day 09:00 - 17:00).
2. Open a private window (or log out), sign up as a **Customer**, open the business, press **Book now**, choose service + date, pick a time.
3. Log in as the owner again and **Confirm** the booking.

### Step 11 - Run the tests
```
python manage.py test
```
All tests should say `OK`.

---

## PART 2 - How to change the colours

Open `static/css/colors.css`. **Only change lines 6 and 7:**
- **Line 6:** `--brand: #014BAA;` - main colour (royal blue). Used for buttons, links, header name, highlights.
- **Line 7:** `--cream: #F8F3F0;` - background colour (light cream).

Every other colour, including dark mode, is made automatically from these two. Save the file and press Ctrl+F5 in the browser. The green/red/amber status colours for success, error and warning messages are on the `--success`, `--danger`, `--warning` lines (lines 19-21) if you want to change them.

---

## PART 3 - Where each of the 20 extra features lives

| Feature | Where |
|---|---|
| Dark mode toggle | button in header; `static/js/main.js` (block 2); colours in `colors.css` |
| Simple cookie banner | `templates/base.html` (`cookie-banner`) + `main.js` (block 5) |
| Site search | search box in header (`base.html`); logic in `bookings/views.py` `business_list` |
| Back-to-top button | `base.html` (`back-to-top`) + `main.js` (block 4) |
| Mobile menu | "Menu" button in `base.html` + `main.js` (block 3) + `style.css` |
| Loading animation | `page-loader` in `base.html` + `main.js` (block 1) |
| Hover states | `.btn:hover`, `.card:hover`, nav links in `static/css/style.css` |
| Scroll progress bar | `scroll-progress` in `base.html` + `main.js` (block 4) |
| Copy button | `data-copy` buttons (business page, booking page) + `main.js` (block 6) |
| Print stylesheet | `static/css/print.css`; "Print" button on the booking page |
| Sticky header | `.site-header` in `style.css` |
| Skip to content | `skip-link` at top of `base.html` |
| Password visibility toggle | added to every password box by `main.js` (block 8) |
| UTM tracking | `bookings/middleware.py`; saved on bookings and contact messages (see them in Admin) |
| Form success state | green message banner (`messages` in `base.html`, `.message.success` in `style.css`) |
| Confirmation modals | `confirm-dialog` in `base.html`; forms with class `js-confirm` |
| Last updated date | footer; change the text in `config/settings.py` -> `SITE_LAST_UPDATED` |
| Expandable FAQ | home page; add/edit questions in Admin > FAQs |
| Floating contact button | `contact-fab` in `base.html` |
| Form error state | red messages and red borders (`.errorlist`, `main.js` block 11) |

Smooth animations: scroll-reveal on cards, hover lifts, fade/slide of menus and messages. They switch off automatically for people who set "reduce motion" in their device.

UTM test: open `http://127.0.0.1:8000/?utm_source=newsletter&utm_medium=email`, then make a booking. Admin > Bookings shows `utm_source`.

---

## PART 4 - Project map
```
slotbook/
  manage.py            run commands with this
  config/              settings.py (settings), urls.py (address list)
  accounts/            sign up, login, Profile (role)
  bookings/            models.py (data), views.py (pages), utils.py (slot maths),
                       forms.py, admin.py, middleware.py (UTM), tests.py
                       management/commands/seed_basics.py
  templates/           all HTML pages (base.html is the shared frame)
  static/css, static/js   styles and JavaScript
  media/               uploaded images are saved here
```
Booking rules: one booking at a time per business; slots are as long as the service; customers can book from today up to 60 days ahead (`BOOKING_WINDOW_DAYS` in `config/settings.py`); cancelled bookings free the slot.

---

## PART 5 - Put it on GitHub
1. Install Git from https://git-scm.com/ and create an empty repository on https://github.com (no README).
2. In Command Prompt inside the project:
```
git init
git add .
git commit -m "SlotBook first version"
git branch -M main
git remote add origin https://github.com/YOUR-NAME/slotbook.git
git push -u origin main
```
`.gitignore` already keeps your database, `venv` and uploaded images out of GitHub.

---

## PART 6 - Deployment guide (example: Render.com with PostgreSQL)
1. Push the project to GitHub (Part 5).
2. On https://render.com create a **PostgreSQL** database. Copy its host, database name, user, password.
3. Create a **Web Service** from your GitHub repo and set:
   - Build Command: `./build.sh`
   - Start Command: `gunicorn config.wsgi`
4. Add **Environment Variables** (names are in `.env.example`):
   - `DJANGO_SECRET_KEY` - a long random text. Make one with: `python -c "import secrets; print(secrets.token_urlsafe(50))"`
   - `DJANGO_DEBUG` = `False`
   - `DJANGO_ALLOWED_HOSTS` = `your-app-name.onrender.com`
   - `DJANGO_CSRF_TRUSTED_ORIGINS` = `https://your-app-name.onrender.com`
   - `DB_NAME`, `DB_USER`, `DB_PASSWORD`, `DB_HOST`, `DB_PORT` from the database page
5. Deploy. Then open the Render "Shell" and run:
```
python manage.py seed_basics
python manage.py createsuperuser
```
6. **Uploaded images on a live server:** most hosts erase the `media/` folder on every deploy. Attach a persistent disk mounted at the project's `media/` folder (Render: Disks), or move to cloud storage (e.g. `django-storages` with S3) before real customers upload images.
7. Live checklist: `DJANGO_DEBUG=False`, a strong secret key, HTTPS only, regular database backups.

**Using PostgreSQL on your PC instead of SQLite (optional):** install PostgreSQL, `pip install -r requirements-prod.txt`, and set `DB_NAME`, `DB_USER`, `DB_PASSWORD` (e.g. `set DB_NAME=slotbook` in Command Prompt) before `migrate`.

---

## Troubleshooting
- `'python' is not recognized` - reinstall Python and tick "Add python.exe to PATH".
- `No module named django` - you forgot `venv\Scripts\activate`.
- Pages look unstyled on the live site - run `python manage.py collectstatic` (the build script does this).
- Changed a model? Run `python manage.py makemigrations` then `python manage.py migrate`.
