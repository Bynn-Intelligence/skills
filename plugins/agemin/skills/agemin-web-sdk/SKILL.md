---
name: agemin-web-sdk
description: >-
  Integrate the Agemin browser SDK (@bynn-intelligence/agemin-sdk) for biometric age
  verification: install, initialize with an Asset ID and reference ID, choose
  verify() for a single trigger or validateSession() to gate every page, wire the
  onAgePass/onAgeFail/onError/onCancel callbacks, handle React and Vue mounting, and
  configure search-engine bypass for SEO. Use when adding an age gate to a web
  frontend.
metadata:
  author: bynn
  version: "0.1.0"
license: MIT
---

# Agemin Web SDK

Face-scan age verification in the browser. The SDK opens the verification app, runs the
scan, and calls you back.

## Install

```bash
npm install @bynn-intelligence/agemin-sdk
```

```html
<script src="https://unpkg.com/@bynn-intelligence/agemin-sdk/dist/agemin-sdk.umd.js"></script>
```

## Initialize

```javascript
import Agemin from '@bynn-intelligence/agemin-sdk';

// reference IDs come from your backend, one per verification
const { referenceId } = await (await fetch('/api/agemin/reference', { method: 'POST' })).json();

const agemin = new Agemin({
  assetId: 'ast_5b08b274353b92f4',   // from agemin.com/app/websites
  referenceId,                       // max 50 bytes
  metadata: { userId: 123 },         // optional, max 256 bytes stringified
  debug: false
});
```

From v5 the SDK is a singleton: only the first constructor call creates an instance. Use
`Agemin.getInstance()` to reach the existing one, or `Agemin.getInstance(config)` to
create it if it does not exist yet. This is what stops React StrictMode from opening two
modals.

Never put the private key in this code. The Asset ID is the only credential the browser
gets. See the `agemin` skill.

## Two methods, one decision

```
Single "Verify Age" button          -> verify()
Protect every page automatically    -> validateSession()
Seamless multi-page experience      -> validateSession()
```

### verify()

The visitor triggers it. A modal opens, the scan runs, callbacks fire.

```javascript
agemin.verify({
  onSuccess: (result) => {
    // the flow completed. This does NOT mean the visitor passed.
    // confirm server side with result.sessionToken
  },
  onAgePass: (result) => { /* met the threshold */ },
  onAgeFail: (result) => { window.location.href = '/age-restricted'; },
  onError:   (err)    => { showFallbackAgeModal(); },
  onCancel:  ()       => { /* visitor closed the modal */ }
});
```

`onSuccess` always fires when the flow completes, pass or fail. `onAgePass` and
`onAgeFail` are the branches. Do not treat `onSuccess` as approval: that mistake ships an
age gate that lets everyone through.

### validateSession()

Call it at the top of every protected page. It returns `true` immediately when a valid
verification already exists, and otherwise launches verification itself.

```javascript
const result = await agemin.validateSession({
  onAgePass: (data) => { /* allow access */ },
  onAgeFail: (data) => { window.location.href = '/age-restricted'; },
  onError:   (err)  => { showFallbackAgeModal(); }
});

if (result === true) {
  // already verified in a previous session, nothing rendered
}
```

It relaunches verification when there is no verification cookie, when the stored token is
expired or invalid, or when the visitor previously failed. Session storage is handled for
you: do not write your own cookie on top of it.

**The failure page must not call `validateSession()`.** A gated `/age-restricted` page
redirects to itself forever.

## Confirm server side

The callbacks run in the visitor's browser, so they can be called by anyone. After
`onSuccess` or `onAgePass`, send `result.sessionToken` to your backend and confirm it:

```
GET https://api.agemin.com/v1/agemin/check/status/{sessionToken}
Authorization: Bearer age_sk_live_...
```

Unlock content from that response, not from the callback. See `agemin-api`.

## Handle technical errors deliberately

`onError` means the verification could not run: camera denied, network failure, an
unsupported browser. It does not mean the visitor is underage.

Failing closed here blocks legitimate adults whose camera permission prompt was dismissed.
Failing open removes the gate for anyone who can force an error. Pick per surface, and
have a fallback path ready, typically a manual age gate or an alternative check from
`agemin-api`.

## SEO: search engine bypass

Crawlers cannot scan a face, so a gated page indexes as an empty gate.

```javascript
const agemin = new Agemin({
  assetId: 'ast_xxx',
  referenceId: 'ref_xxx',
  allowSearchEngineBypass: true,
  searchEngineDetection: 'combined'
});
```

Detection modes:

| Mode | Behaviour |
|---|---|
| `ua` | User agent patterns only. Default, fast, spoofable. |
| `headless` | Headless browser characteristics. |
| `cookies` | Cookie support, which Googlebot typically lacks. |
| `combined` | Any signal triggers bypass. Most inclusive, more false positives. |
| `strict` | Requires several signals. Most accurate, fewest false positives. |

Every mode is defeatable by someone who wants to defeat it, because a user agent is just
a string the client chooses. Use `combined` when discoverability matters more than the
gate, and `strict`, or no bypass at all, when the gate is a legal requirement. Do not
enable this and then treat the gate as airtight.

## React and Vue

Create the instance in an effect, not during render, and rely on the singleton rather than
your own guard:

```javascript
useEffect(() => {
  const agemin = Agemin.getInstance({ assetId, referenceId });
  agemin.validateSession({ onAgePass, onAgeFail, onError });
}, [referenceId]);
```

StrictMode runs effects twice in development. The singleton is what keeps that from
opening two modals, which is why you should not construct with `new` inside a component.

## Auto-initialization

The SDK can be configured from data attributes on the script tag, which is the path for a
site with no build step. It still needs a reference ID, so generating one server side and
rendering it into the page remains your job.

## Checklist

- [ ] Asset ID in the browser, private key nowhere near it
- [ ] Reference ID generated server side, one per verification, under 50 bytes
- [ ] `onAgePass` confirmed server side before anything unlocks
- [ ] `onError` has a fallback that is neither "block everyone" nor "allow everyone"
- [ ] The age-fail and error pages are not themselves gated
- [ ] React or Vue instances created in an effect, via `getInstance()`
