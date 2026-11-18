# Launching clipkontrast.com today

Two pieces, one codebase:

| | Where | Settings |
|---|---|---|
| **The website** (Earn, sign-up, campaigns, payouts) | Your server or PC, at clipkontrast.com | `CLIPKONTRAST_ACCOUNTS=1`, `CLIPKONTRAST_EARN_ONLY=1` |
| **The clip studio** (the free download, the .bat) | Each clipper's own PC | nothing: it runs with no sign-in, and its Earn button opens clipkontrast.com/earn |

## 1. Put the download online (10 minutes)

Clippers download this same folder. Push it to your GitHub repository (the one the "Download free" buttons and the
update check point to). `.env`, `data/` and `secrets/` are ignored by git, so no keys or data go up.

Optional, nicer: on GitHub make a **Release** and attach the folder as a zip, then set
`CLIPKONTRAST_DOWNLOAD_URL=https://github.com/<you>/<repo>/releases/latest`.

## 2. Run the website (30 minutes, free, on your own PC)

1. Unzip to `C:\clipkontrast` and create `C:\clipkontrast\.env`:

   ```
   CLIPKONTRAST_ACCOUNTS=1
   CLIPKONTRAST_EARN_ONLY=1
   CLIPKONTRAST_PUBLIC_URL=https://clipkontrast.com
   CLIPKONTRAST_TUNNEL=1
   CLIPKONTRAST_CLIENT_IP_HEADER=CF-Connecting-IP
   CLIPKONTRAST_DOWNLOAD_URL=https://github.com/anistroz/Agak
   CLIPKONTRAST_VERIFY_EMAIL=1
   CLIPKONTRAST_SMTP_HOST=smtp-relay.brevo.com
   CLIPKONTRAST_SMTP_PORT=587
   CLIPKONTRAST_SMTP_USER=your-brevo-login
   CLIPKONTRAST_SMTP_PASSWORD=your-brevo-smtp-key
   CLIPKONTRAST_MAIL_FROM=ClipKontrast <hello@clipkontrast.com>
   CLIPKONTRAST_CONTACT_EMAIL=hello@clipkontrast.com
   CLIPKONTRAST_LEGAL_NAME=Your full name or business name
   CLIPKONTRAST_LEGAL_COUNTRY=India
   ```

   The last three fill in the Terms and Privacy pages (who runs the site, whose law applies, how to reach you).
   Without them those pages show blanks, which is not good enough for a site that pays people.

   (Gmail works too: `smtp.gmail.com`, your Gmail address, and an app password from myaccount.google.com/apppasswords.)
2. Double-click `Start-ClipKontrast-Windows.bat`. Keep the black window open.
3. **Cloudflare**: add clipkontrast.com to Cloudflare (Free plan) and change the nameservers where you bought the
   domain. Then Zero Trust → Networks → Tunnels → Create tunnel → run the Windows install command it shows (as
   administrator) → Public hostname `clipkontrast.com` → Service `http://localhost:8765`.
4. Open https://clipkontrast.com, sign up with your own email, then in `C:\clipkontrast` run:
   `python -m studio.admin grant your@email.com`
5. Optional but recommended: Google sign-in for clippers (one tap, no email confirmation). See DEPLOY.md, "Google setup".

The PC has to stay on and online. Turn off sleep (Settings → System → Power → Sleep: Never).

## 3. Create the campaign (10 minutes)

1. https://clipkontrast.com/admin/earn → **Settings**: paste a YouTube Data API v3 key (steps are on that page).
2. **Campaigns → New campaign**: title, creator, brief, rules, stream links, platforms, required tag (the creator's
   @handle), budget, rate per 1,000 views, minimum views, most per clip, hold days, start and end.
3. Save, upload a cover, press **Go live**.
4. Share `https://clipkontrast.com/earn` (or `/earn#c=<campaign-slug>`) in your reel and stories.

## 4. Every day while it runs

- **Review clips**: clips turn *Ready* after the hold period. Type in Instagram/X views from the screenshot, approve.
- **Payouts**: send the money from your UPI app, press **Mark paid**, paste the UTR.
- Keep the budget you put on the site lower than what you actually have to pay clippers with.

## Later: move off your PC

Oracle Cloud Always Free (2 ARM cores, 12 GB) runs the website fine in Earn-only mode: `docker compose up -d --build`
with the same `.env` (drop the two tunnel lines if you point the domain straight at the server). See DEPLOY.md.
