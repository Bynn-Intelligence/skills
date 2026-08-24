---
name: bynn-web-sdk
description: >-
  Embed Bynn identity verification in a website with the Bynn Web SDK
  (@bynn-intelligence/websdk): script tag or npm install, mount a verification
  form or a single button into a parent element, prefill and hide applicant
  fields, handle session events, and decide when to drop to the Sessions API
  instead. Use when adding KYC to a web frontend, a React or Vue app, or a
  checkout flow.
metadata:
  author: bynn
  version: "1.0.0"
license: MIT
---

# Bynn Web SDK

The fastest way to put identity verification on a page. The SDK renders the form, creates
the session, and opens the verification flow. You provide a public key, a KYC level, and a
parent element.

## Install

Package manager, which is the path that stays current on its own:

```bash
npm install @bynn-intelligence/websdk
```

```javascript
import { Bynn } from '@bynn-intelligence/websdk';
```

Script tag, from a CDN that resolves to the latest published build:

```html
<script src="https://unpkg.com/@bynn-intelligence/websdk/dist/bynn.min.js"></script>
```

```html
<script type="module">
  import * as Bynn from 'https://unpkg.com/@bynn-intelligence/websdk/dist/bynn.esm.js';
</script>
```

`https://cdn.jsdelivr.net/npm/@bynn-intelligence/websdk/dist/bynn.min.js` works the same
way if you prefer jsDelivr.

### Pinning a version

Pinning is the right call for production, because an unversioned CDN URL means a third
party can change your verification flow without a deploy on your side. Bynn serves
version-pinned builds at:

```
https://static.bynn.com/sdk/js/<version>/bynn.min.js
https://static.bynn.com/sdk/js/<version>/bynn.esm.js
```

**Look the current version up rather than copying one.** Any of these answers it:

```bash
npm view @bynn-intelligence/websdk version
curl -s https://registry.npmjs.org/@bynn-intelligence/websdk/latest | jq -r .version
```

The dashboard also shows a ready-made snippet with the current version at
`https://dashboard.bynn.com/integration`, under "Bynn.js (easy integration)".

Then pin deliberately and upgrade on your own schedule. A version number written down in
a guide is stale the moment a release ships, so treat any version you see quoted anywhere
as an example, not as the current one.

## Mount

The SDK needs one parent element:

```html
<div id="verification-form"></div>
```

```javascript
const bynn = Bynn({
  apiKey: 'your_PUBLIC_api_key',
  kycLevel: 'your_kyc_level',
  parentId: 'verification-form',
  fields: [
    { name: 'first_name',    visible: true },
    { name: 'last_name',     visible: true },
    { name: 'email_address', visible: false, value: 'john@doe.com' },
    { name: 'phone_number',  visible: true },
    { name: 'unique_id',     visible: false, value: '550e8400-e29b-41d4-a716-446655440000' }
  ]
});

bynn.mount();
```

Both `apiKey` and `kycLevel` come from the dashboard at
`https://dashboard.bynn.com/integration`, under "Bynn.js (easy integration)". The KYC
level itself is configured at `https://dashboard.bynn.com/setting/product/kyc`.

**Use the public key here, never the private key.** This code runs in a browser. The
public key is designed to be visible; the private key would let anyone read your results.

## Fields

Each entry in `fields` accepts:

| Property | Meaning |
|---|---|
| `name` | One of `first_name`, `last_name`, `email_address`, `phone_number`, `unique_id` |
| `visible` | Render the input, or keep the value hidden. Defaults to true. |
| `value` | Prefilled value |
| `label` | Custom label text |

Set every field you already know to `visible: false` with a `value`. When all of them are
hidden the SDK renders just the verification button, which is what you want in a
logged-in flow where re-typing details is friction with no upside.

**Always send `unique_id`.** It is your own user identifier, it comes back on every
webhook, and it is what makes results matchable without guessing from names. Set it even
when nothing else is prefilled.

Everything except the key and level is optional, but more applicant data means better
matching and fewer manual reviews.

## Configuration reference

| Option | Type | Required | Notes |
|---|---|---|---|
| `apiKey` | string | yes | Your **public** key |
| `kycLevel` | string | yes | KYC level token |
| `parentId` | string | yes | Id of the container element |
| `fields` | Field[] | no | Form field configuration |
| `i18n` | string | no | Language code, for example `en-US` |
| `startTimeoutSeconds` | number | no | How long to wait for verification to start. Default 10. |
| `onSession` | function | no | Session created |
| `onStart` | function | no | Verification started |
| `onComplete` | function | no | Flow completed |
| `onSuccess` | function | no | Completed successfully |
| `onReject` | function | no | Rejected |
| `onError` | function | no | Technical error |
| `onClose` | function | no | Modal closed |

## Customizing and events

```javascript
bynn.mount({
  submitBtnText: 'Verify Identity',
  loadingText: 'Please wait...'
});
```

```javascript
const bynn = Bynn({
  // ...
  onSession: (error, response) => {
    if (error) {
      console.error('Verification error:', error);
      return;
    }
    console.log('Verification started:', response);
  },
  onStart:    ()  => showSpinner(),
  onComplete: ()  => hideSpinner(),
  onClose:    ()  => trackAbandonment()
});
```

Use these for **UI only**. `onSession` fires when the session is created, `onStart` when
the applicant begins, and `onComplete` when the flow ends. None of them is a verdict, and
`onSuccess` here means the flow finished cleanly, not that the person passed. Show
spinners and fire analytics from these; grant access from the webhook.

`startTimeoutSeconds` bounds the wait for verification to start, defaulting to 10 seconds.
Raise it on slow connections rather than treating the timeout as a hard failure.

## Styling

The SDK is themed with CSS custom properties. Override them on `:root`:

```css
:root {
  --bynn-primary: #6366F1;
  --bynn-primary-hover: #4F46E5;
  --bynn-primary-disabled: #C7D2FE;
  --bynn-primary-light: #EEF2FF;
  --bynn-bg-white: #FFFFFF;
  --bynn-bg-input: #F9FAFB;
  --bynn-neutral-50: #F9FAFB;
  --bynn-neutral-100: #F3F4F6;
  --bynn-neutral-200: #E5E7EB;
  --bynn-neutral-300: #D1D5DB;
  --bynn-neutral-600: #4B5563;
  --bynn-neutral-800: #1F2937;
}
```

Element classes are namespaced behind `.data-bynn-sdk` so they do not collide with your
own: `.bynn-form`, `.bynn-input-wrapper`, `.bynn-input`, `.bynn-submit`,
`.bynn-description`, `.bynn-modal-overlay`, `.bynn-modal-container`, `.bynn-modal-content`.

```css
.data-bynn-sdk .bynn-submit {
  background: var(--bynn-primary);
  font-weight: 600;
}
```

Prefer the custom properties over class overrides. Variables survive SDK updates; selector
overrides are coupled to markup that can change.

## Language

```javascript
const bynn = Bynn({ apiKey, kycLevel, parentId, i18n: 'en-US' });
```

Set it from the same source as the rest of your page's locale, so the verification step
does not switch languages mid-flow.

## Where the outcome comes from

**Nothing the browser reports is proof.** The SDK runs on the client, so anything it hands
you can be forged by whoever controls that client. The verdict arrives at your backend as
a webhook, signed, and that is the only channel that should unlock anything. See
`bynn-webhooks`.

A useful split:

- Frontend: the SDK renders the flow and shows the user where they are.
- Backend: the webhook decides what the user may now do.

## When to use the Sessions API instead

Drop the SDK and call `POST /sessions` directly when you want:

- Your own button, modal, or multi-step wizard, with full control of the markup.
- A native mobile app, or any non-browser client.
- Desktop to mobile handoff with your own QR rendering.
- Server-side session creation, so the applicant never sees a key at all.

The API gives you a `url`, a `qr_base64_png`, and a `websocket_url` to build against. See
`bynn-kyc-sessions`.

## Frameworks

The SDK mounts into a DOM node, so in React or Vue create it in an effect that runs after
the parent element exists, and tear it down when the component unmounts. Do not construct
it during render, and guard against double-mounting under React StrictMode, which runs
effects twice in development.
