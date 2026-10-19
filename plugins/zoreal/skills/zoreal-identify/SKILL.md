---
name: zoreal-identify
description: >-
  Integrate Login with ZOREAL (ZOREAL Identify): a sign-in on OpenID Connect
  where the person proves with their ZOREAL ID that they are a verified, unique,
  live human. Covers the asset and its client id, the two flows (auth-code with
  a backend, and the no-backend button), the client libraries for React,
  browser JavaScript, React Native, Node, Python, Ruby, PHP, Go, JVM, .NET and
  Rust, the scope catalogue, requiring a live face capture with acr and
  verifying it on the server, the assurance block, pairwise sub, and the error
  codes. Use for "Continue with ZOREAL", "Sign in with ZOREAL", proof of human
  at login, or any code that talks to id.zoreal.com.
metadata:
  author: bynn
  version: "1.1.0"
license: MIT
---

# Login with ZOREAL

A sign-in button on standard OpenID Connect. Your site receives a stable pseudonymous
identifier (`sub`) for a verified human, how strongly and how recently that was proven
(`acr` and the assurance block), and identity details only when the person consents.

| Thing | Value |
|---|---|
| Issuer | `https://id.zoreal.com` |
| Discovery | `https://id.zoreal.com/.well-known/openid-configuration` |
| Token, UserInfo, JWKS | `{issuer}/token`, `{issuer}/userinfo`, `{issuer}/jwks` |
| ID token signature | ES256 only |
| Subject type | pairwise, per verified domain |
| Register a client | zoreal.com, Assets |

## Use the client libraries, not a generic OIDC library

The provider publishes **no `authorization_endpoint`**. The flow starts at a pairing
step the frontend library runs (a QR on a computer, the ZOREAL ID app on a phone) and
finishes at `/token` on your backend. A generic relying-party library that wants to build
an authorize URL has nothing to point at. Use the family:

| Platform | Install | Role |
|---|---|---|
| React | `npm install @zoreal/oauth2-react` | The button, the pairing modal, the polling |
| Browser, no framework | `npm install @zoreal/oauth2-js` | The same core for Vue, Svelte, Angular or plain pages |
| React Native | `npm install @zoreal/oauth2-react-native` | Mobile frontend; opens the ZOREAL ID app on the same device |
| Node.js | `npm install @zoreal/oauth2-node` | Backend: exchange, verify, userinfo |
| Python | `pip install zoreal-oauth2` | Backend, import `zoreal_oauth2` |
| Ruby | `gem install zoreal-oauth2` | Backend |
| PHP | `composer require zoreal/oauth2` | Backend |
| Go | `go get github.com/Bynn-Intelligence/zoreal-oauth2-go` | Backend |
| JVM | `com.zoreal:oauth2` (Maven Central) | Backend |
| .NET | `dotnet add package Zoreal.OAuth2` | Backend |
| Rust | `cargo add zoreal-oauth2` | Backend |

Each library's README is the full reference: the repositories are
`zoreal-oauth2-react`, `zoreal-oauth2-node` and so on, under
`https://github.com/Bynn-Intelligence`. Check the current version with the registry rather than pinning
one from memory.

## Get credentials

1. Create an account at `https://zoreal.com`, open **Assets**, and create an asset: a
   website (a domain you own) or an app bundle (a reverse-DNS bundle id). Its token,
   `ast_...`, is your `clientId`. It is public and ships in the frontend.
2. On the asset's **OAuth2** tab, register the JavaScript origins and redirect URIs, the
   scopes the client may request, and the backend's client authentication: a client
   secret (`client_secret_basic`) or a JWKS (`private_key_jwt`).
3. A website asset must verify its domain (DNS or meta tag) before it can request
   personal-data scopes or sign users in. The verified domain is what `sub` is pairwise
   against.
4. Mark the asset **sandbox** while building: it may register `http://localhost` origins,
   which a production asset may not. Flip it to production when you ship.

There are no test identities. Enrol a ZOREAL ID for yourself (`https://zoreal.com/download`)
and sign in with it.

## Pick the flow

| You need | Flow | What you get |
|---|---|---|
| Email, name or document fields, and you have a backend (most apps) | `auth-code` | Your backend exchanges the code and reads `/userinfo` |
| Only "a verified, unique human, the same one as last time", no backend | The `<ZorealLogin>` button | An ID token with `sub`, `acr` and the assurance block, still verified on a server before you trust it |

## Auth-code, end to end

The frontend (React shown; the other frontends take the same options):

```tsx
import { ZorealOAuthProvider, useZorealLogin } from '@zoreal/oauth2-react';

// Once, around the part of the app that signs in.
<ZorealOAuthProvider clientId={ZOREAL_CLIENT_ID}>
  <App />
</ZorealOAuthProvider>;

function ZorealSignIn() {
  const login = useZorealLogin({
    flow: 'auth-code',
    scope: 'openid email profile.name',
    onSuccess: async ({ code, code_verifier, nonce }) => {
      // Send all three to your backend.
      await fetch('/api/auth/zoreal', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ code, code_verifier, nonce }),
      });
    },
    onNonOAuthError: (e) => {
      // Declining, letting the request expire or closing the dialog are human
      // outcomes, not faults. Let the button be pressed again.
      if (['request_denied', 'request_expired', 'popup_closed'].includes(e.type)) return;
      console.error(e.type, e.description);
    },
  });
  return <button type="button" onClick={login}>Continue with ZOREAL</button>;
}
```

The provider renders the pairing modal on a computer. On a phone the tap opens the
ZOREAL ID app and returns to the page, where the same hook calls `onSuccess` on a fresh
page load, so mount it on the page the sign-in starts from.

The backend (Node shown; every backend library has the same calls in its own idiom):

```ts
import { ZorealOAuth2Client } from '@zoreal/oauth2-node';

const zoreal = new ZorealOAuth2Client({
  clientId: process.env.ZOREAL_CLIENT_ID!,
  issuer: 'https://id.zoreal.com',
  auth: { method: 'client_secret_basic', clientSecret: process.env.ZOREAL_CLIENT_SECRET! },
});

app.post('/api/auth/zoreal', async (req, res) => {
  const { code, code_verifier, nonce } = req.body;
  const login = await zoreal.authenticate(code, code_verifier, { nonce });
  login.sub;            // the account key: stable, pairwise for your domain
  login.acr;            // how this login was proven
  login.assurance;      // how the identity behind it was proofed
  await login.email();  // from /userinfo, with the email scope
});
```

Match accounts on `sub`. Claim an existing account by email only when
`login.emailVerified()` is true.

## Scopes

Always start with `openid`. Every scope must be registered on the asset first.

| Scope | Claims | Delivered in | Needs |
|---|---|---|---|
| `openid` | `sub`, `acr`, `amr`, the assurance block, timing | ID token | Any client |
| `zoreal.age` | `age_over_13`, `_16`, `_18`, `_21`, `_65` booleans, only for thresholds registered on the asset | ID token | Any client |
| `zoreal.nationality` | `nationality` (ISO 3166-1 alpha-3) | ID token | Any client |
| `email` | `email`, `email_verified` | `/userinfo` | Backend and verified domain |
| `profile.name` | `name`, `given_name`, `family_name` | `/userinfo` | Backend and verified domain |
| `profile.birthdate` | `birthdate` | `/userinfo` | Backend and verified domain |
| `profile.document` | `document_type`, `document_number`, `issuing_country`, `document_expires_on` | `/userinfo` | Backend and verified domain |
| `profile.portrait` | `portrait` | `/userinfo` | Registrable, not served yet |

- **The ID token never carries personal data.** Email, name, birthdate and document
  fields exist only at `/userinfo`. Decoding the ID token and finding no email is correct.
- **The access token lives 10 minutes.** Read `/userinfo` while handling the login; do
  not store the token.
- **An unregistered age threshold produces no claim at all**, which is not the same as
  `false`. Register only the thresholds you gate on.
- **Request email only when you need it.** A shared email undoes the unlinkability that a
  pairwise `sub` gives.

## Requiring a live human: `acr`

| `acr` | The person | Proves |
|---|---|---|
| `zoreal.session` | Resumed silently from an existing session | Continuity, not presence |
| `zoreal.device` (default) | Approved on their enrolled phone with a local unlock | Possession of the device and an unlock |
| `zoreal.live` | The above plus a fresh face capture, matched to the document read at enrolment | A live, verified human at the moment of this login |

Requesting and verifying are two steps, and **only the second is security**:

1. Request it in the frontend with `acr_values: 'zoreal.live'`. This makes the app run
   the face capture. It is advisory: a browser is attacker-controlled.
2. Verify it on the backend, from the signed token:

```ts
const login = await zoreal.authenticate(code, code_verifier, { nonce, acr: 'zoreal.live' });
// Rejects unless the signed acr is zoreal.live. Levels satisfy upward:
// session < device < live, so requiring device accepts a live token.
```

A relying party that requests `zoreal.live` and never verifies it has checked nothing.

## The assurance block

The ID token's `zoreal` claim describes the identity behind the login, separate from
`acr`, which grades this login event. A high-value flow checks both.

| Key | Values |
|---|---|
| `uniqueness` | `personal_number`, `document` or `none`: what the person is deduplicated on |
| `verified_on` | `YYYY-MM`, the month the document was verified |
| `chip_liveness_proven` | Whether the document chip's active authentication was proven |
| `trust_tier` | `high` when the chip was proven, else `standard` |
| `key_protection` | `secure_enclave`, `strongbox`, `tee` or `software` |

## Verifying the ID token yourself

Prefer the libraries. If you must hand-roll it: ES256 only, against `{issuer}/jwks`;
`iss` compared as an exact string to `https://id.zoreal.com`; `aud` against your client
id; `exp`; and the `nonce` your frontend posted. Without the nonce check you cannot tell
a substituted token from the real one.

## Errors

| Where | Code | Means | Do |
|---|---|---|---|
| `/token` | `invalid_grant` | The code is spent: expired (60 seconds), reused, PKCE mismatch, or the domain verification lapsed | Start a new login |
| `/token` | `invalid_request` | Client authentication failed | Fix the secret or assertion |
| Pairing | `invalid_scope` | A scope not registered on the asset, or a personal-data scope from a public client | Register it, or move to auth-code |
| Pairing | `request_denied`, `request_expired`, `popup_closed` | The person declined, walked away or closed the dialog | Not an error. Offer the button again |
| Pairing | `platform_unsupported`, `enrolment_abandoned` | No ZOREAL ID app for this platform, or enrolment not finished | Explain gently, offer another way in |

## Rules that are easy to break

- **`sub` changes if the asset's domain changes.** Treat a domain change as a data
  migration.
- **No redirect mode.** It would put the PKCE verifier in a URL.
- **The button asserts nothing.** Label it "Continue with ZOREAL". The proof is in the
  verified claims, not the label.
- **Identify is a sign-in, not a KYC decision.** The document attributes are verified
  inputs to your own checks; the regulatory determination stays yours. For an
  end-to-end identity check of someone without a ZOREAL ID, use `bynn-kyc-sessions`.
