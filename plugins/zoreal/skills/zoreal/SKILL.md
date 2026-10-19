---
name: zoreal
description: >-
  Start here for any ZOREAL task: Login with ZOREAL (ZOREAL Identify, a sign-in
  that proves a verified, live human), the ZOREAL Meet meetings API and the
  ZOREAL Book scheduling embed, or ZOREAL Verify (identity verification and
  document forensics, including PDFChecker). Explains which ZOREAL products a
  developer can integrate today, what each one proves and does not prove, and
  routes Verify work to the Bynn skills that run its checks. Routes to
  zoreal-identify and zoreal-meet. Use whenever ZOREAL, zoreal.com, ZOREAL ID,
  "continue with ZOREAL", proof of human, or a verified meeting comes up.
metadata:
  author: bynn
  version: "1.1.0"
license: MIT
---

# ZOREAL (router)

ZOREAL is the trust layer from Bynn Intelligence that proves a real human is present
behind a digital interaction, and who they are. It has five products: Meet, Identify,
Mark, Sign and Verify. Pick the lane here and open only the skill you need.

## Quick reference

| Thing | Value |
|---|---|
| Site and account | `https://zoreal.com` |
| API documentation | `https://zoreal.com/documentation` |
| Site index for agents | `https://zoreal.com/llms.txt` |
| Price list | `https://zoreal.com/pricing` |
| Sign-in provider (OpenID Connect issuer) | `https://id.zoreal.com` |
| Provider discovery | `https://id.zoreal.com/.well-known/openid-configuration` |
| Meetings API base | `https://api.bynn.com/v1/zoreal/meet` |
| Downloads (ZOREAL ID, Meet apps) | `https://zoreal.com/download` |
| Support | `https://zoreal.com/support` |

The documentation page renders in the browser, so a plain fetch of it returns an empty
shell. The two skills below carry the integration facts in text form; read them rather
than scraping the page.

## Routing

| Task | Skill |
|---|---|
| Add a "Continue with ZOREAL" sign-in, require a live human at login, read verified age, nationality, name or document fields on consent | `zoreal-identify` |
| Create, schedule, list or end meetings from your backend, read meeting notes, run host controls, the knock-to-enter door, room policy | `zoreal-meet` |
| Put ZOREAL Book scheduling on your own site (script tag, `@zoreal/book-js`, `@zoreal/book-react`) | `zoreal-meet` |
| Is this PDF, invoice, statement or ID document genuine, altered or AI-generated (ZOREAL Verify, PDFChecker) | `bynn-document-fraud` (the `bynn` plugin) |
| Verify a person you do not know yet: document, liveness and face match in an onboarding flow (ZOREAL Verify) | `bynn-kyc-sessions` (the `bynn` plugin) |

## ZOREAL Verify runs through the Bynn API today

ZOREAL Verify is where Bynn's identity verification and document forensics, including
PDFChecker, now live within ZOREAL. Its checks run through the Bynn API today, and its
integrated dashboard is coming soon. So the code for a Verify integration is a Bynn
integration: keys from `https://dashboard.bynn.com`, the base `https://api.bynn.com/v1`,
and the `bynn-document-fraud` and `bynn-kyc-sessions` skills. Do not look for a separate
ZOREAL Verify API or SDK, and do not invent one.

If those skills are not installed, install the `bynn` plugin from the same marketplace
(`claude plugin install bynn@bynn`) or with
`npx skills add Bynn-Intelligence/skills --skill bynn-document-fraud --skill bynn-kyc-sessions`.

## What each product proves, and what it does not

Get this right in any copy, UI string or comment you write. Each product makes a narrow,
checkable claim, and overstating it is the most common integration mistake.

| Product | Proves | Does not prove |
|---|---|---|
| Identify | A verified, unique human signed in, how strongly and how recently that was proven (`acr`), and, on consent, attributes read from their government document | It is not a KYC decision and not a signature. Your service remains responsible for any regulatory determination it makes from the attributes. |
| Meet | A participant who passed the room's presence rule is a live, enrolled human, or a live human with a verified legal name | Nothing about a participant the rule did not check. A room with the rule off proves nothing about anyone in it. |
| Verify | Findings about how a document or image may have been created or changed, and an identity check of a person against their government ID | A clean report is not a guarantee of authenticity. Treat findings as evidence for a reviewer or a policy. |

ZOREAL Sign and ZOREAL Mark are used by people, at zoreal.com and in the Mark browser
extension. Neither has a developer API in the documentation, so there is nothing to
integrate against yet; say so rather than guessing at endpoints.

## The ZOREAL ID app

Identify, and the proof options in Meet and Book, rely on the person holding a ZOREAL ID:
a credential on their own phone, made by reading their government document's chip over
NFC and binding it to a live face capture. There are no test or sandbox identities. To
develop, enrol a ZOREAL ID for yourself from `https://zoreal.com/download` and sign in
with it.

## Credentials, by product

| Product | Credential | Where |
|---|---|---|
| Identify | An asset's client id (`ast_...`, public) and, for a backend, a client secret or a registered JWKS | zoreal.com, Assets, the asset's OAuth2 tab |
| Meet | An API key (`private_...` or `public_...`, `sandbox_` on test keys) | zoreal.com, Settings, API keys |
| Book embed | None. The booking link (`handle/event-type`) is all the embed needs | zoreal.com, Meet, Book |
| Verify | A Bynn API key or dashboard token | `https://dashboard.bynn.com` |

Secrets belong on your server. Never put a client secret or a `private_` key in browser
code, a mobile app or a repository.
