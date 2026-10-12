# Customer sign-in with Google

MetalWolft keeps Flask as the session authority. Google Identity Services provides
an ID token to the browser; Flask verifies it and issues the existing MetalWolft
JWT. No Google access token, client secret, or Google API permission is required.

## Google Cloud setup

1. Create or select a Google Cloud project and configure its OAuth branding,
   support email, homepage and privacy-policy URL for MetalWolft.
2. Create a **Web application** OAuth client. Use only the standard sign-in
   scopes (`openid`, `email`, `profile`).
3. Add each exact frontend origin under **Authorized JavaScript origins**:
   `https://www.metalwolft.com` for production, the actual Vercel preview origin
   for staging if used, and `http://localhost:3002` for local development.
   A Codespaces origin must be added explicitly if testing there. Do not put paths
   in origins. This JavaScript callback flow needs no redirect URI.
4. Set `NEXT_PUBLIC_GOOGLE_CLIENT_ID` in Vercel and `GOOGLE_CLIENT_ID` in Render
   to the Web client ID for each environment. Use separate clients for development
   and production where possible. Never put a client secret in Next.js.

The button is hidden when the frontend variable is absent; Flask rejects Google
credentials when its client ID is absent. Apply migration `c3d4e5f6a7b8` to the
intended **non-production** database before testing the backend. Do not point
local tests at Neon production.

## Test before release

With both services pointing to an isolated database, test a new Google customer
on `/registro`, repeat access on `/login`, and confirm `/mi-cuenta` and the cart
use the normal session. Test a password customer with the same Google email:
Google access must ask for password login, then Mi cuenta can explicitly link
Google after password confirmation. Confirm that orders remain attached to the
same `users.id`. An unrelated Google identity must not claim the account.

The recovery email uses a purpose-bound 15-minute token. Google-only customers
may set a password through that verified email flow. No automatic order linking
by email is performed. There is no Google unlink action in this initial version.

Deploy the additive migration before enabling the button in production. Keep
`NEXT_PUBLIC_GOOGLE_CLIENT_ID` unset until the matching Render configuration and
migration are verified; deploying only the frontend cannot enable a working login.
