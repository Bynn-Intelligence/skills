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
  version: "0.1.0"
license: MIT
---

# Bynn Web SDK

The fastest way to put identity verification on a page. The SDK renders the form, creates
the session, and opens the verification flow. You provide a public key, a KYC level, and a
parent element.

## Install

Script tag:

```html
<script src="https://static.bynn.com/sdk/js/1.2.11/bynn.min.js"></script>
```

ES module:

```html
<script type="module">
  import * as Bynn from 'https://static.bynn.com/sdk/js/1.2.11/bynn.esm.js';
</script>
```

Package manager:

```bash
npm install @bynn-intelligence/websdk
```

```javascript
import { Bynn } from '@bynn-intelligence/websdk';
```

Pin the version you tested. Check the current one before you copy the URL above.

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
  }
});
```

`onSession` fires when the session is created, not when verification finishes. It is the
right place to show a spinner or log an analytics event, and the wrong place to grant
access.

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
