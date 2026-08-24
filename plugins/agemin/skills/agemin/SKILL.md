---
name: agemin
description: >-
  Start here for any Agemin task: adding biometric age verification or an age gate
  to a website or app. Covers what an Asset ID and a reference ID are, the two
  integration paths (browser SDK versus server-side API), the security model that
  makes the browser result untrustworthy on its own, and where the result actually
  comes from. Routes to agemin-web-sdk and agemin-api. Use whenever Agemin, age
  gating, or "verify this visitor is old enough" comes up.
metadata:
  author: bynn
  version: "0.1.0"
license: MIT
---

# Agemin (router)

Agemin is biometric age verification for websites and apps. A visitor scans their face,
Agemin estimates whether they meet the age threshold, and your backend confirms the
result.

## Quick reference

| Thing | Value |
|---|---|
| Dashboard | `https://agemin.com/app` |
| Docs | `https://agemin.com/docs` |
| API base | `https://api.agemin.com/v1` |
| Verification app | `https://verify.agemin.com` |
| SDK package | `@bynn-intelligence/agemin-sdk` |
| Asset ID | `https://agemin.com/app/websites`, format `ast_...` |
| Private key | `https://agemin.com/app/api-keys`, format `age_sk_live_...` |

## The two credentials

This is the thing to get right before writing any code.

- **Asset ID** (`ast_...`) identifies one website or app. It goes in the browser. It is
  meant to be public.
- **Private key** (`age_sk_live_...`) reads verification results. It goes on your server
  and nowhere else. Anyone holding it can read your results and spend your account.

The split exists so the browser can start a verification but cannot decide its outcome.

## Which path

| You want | Use | Skill |
|---|---|---|
| A face scan gate on a website, modal or redirect | Browser SDK | `agemin-web-sdk` |
| Age-gate every page of a site with one call | Browser SDK, `validateSession()` | `agemin-web-sdk` |
| Confirm a result you can trust | Server API | `agemin-api` |
| Check age from an email address, no face scan | Server API | `agemin-api` |
| Check age from a selfie you already hold | Server API | `agemin-api` |
| Reconcile a user whose callback never arrived | Server API, lookup by reference | `agemin-api` |

Most integrations use both: the SDK runs the flow in the browser, then your backend
confirms with one API call before granting access.

## Reference IDs

Every verification carries a `reference_id` that you generate. It is your join key: it
ties an Agemin session back to your own user, and it is how you look a result up later.

- Generate it **server side**, one per verification.
- Maximum 50 bytes.
- Use a UUID, a session id, or a visitor id. Do not use anything personally identifying.

A reference maps to many sessions, because a visitor who fails and retries creates a new
one each time. See `agemin-api` for what that means when you look one up.

## The security model, stated plainly

**The browser callback is not proof.** `onAgePass` fires in the visitor's own browser.
Anyone can call it. Treat it as a signal to proceed with your check, never as the check
itself.

The flow that is actually safe:

1. Your server generates a `reference_id` and returns it to the page.
2. The SDK runs the verification with your Asset ID and that reference.
3. `onAgePass` fires. Your page tells your server "this reference finished".
4. **Your server calls the Agemin API with the private key** and reads the real result.
5. Your server, and only your server, unlocks the content.

Skipping step 4 leaves an age gate that a visitor can walk through from the browser
console. If a wrong answer costs you nothing, skipping it is a choice you can make
deliberately. If you are gating regulated content, it is not.

## Do not age-gate the failure page

If a visitor who fails is redirected to `/age-restricted`, that page must not itself run
age verification. Otherwise it re-launches the flow, fails again, and redirects to itself
forever. Same for any error or fallback page.

## Related

Agemin is the age-verification product. For full identity verification with an ID
document, or document fraud detection, see the `bynn` skills.
