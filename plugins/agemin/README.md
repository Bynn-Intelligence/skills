# Agemin

Skills for integrating [Agemin](https://agemin.com) biometric age verification: the browser
SDK for age gating a site, and the server API for confirming results you can trust.

## Install

```
/plugin marketplace add Bynn-Intelligence/skills
/plugin install agemin@bynn
```

Any agent, via the skills CLI:

```bash
npx skills add Bynn-Intelligence/skills --skill agemin
```

## Skills

| Skill | Covers |
|---|---|
| `agemin` | Router. Asset ID versus private key, and why the browser result is not proof. |
| `agemin-web-sdk` | `@bynn-intelligence/agemin-sdk`, age gating, SEO bypass, React and Vue. |
| `agemin-api` | Server-side confirmation, email and selfie checks, reference lookups. |

## Credentials

Two, and the split is the whole security model:

- **Asset ID** (`ast_...`) identifies one website or app. It goes in the browser and is
  meant to be public. From `https://agemin.com/app/websites`.
- **Private key** (`age_sk_live_...`) reads verification results. It goes on your server
  and nowhere else. From `https://agemin.com/app/api-keys`.

## The rule that matters

**The browser callback is not proof.** `onAgePass` fires in the visitor's own browser, so
anyone can call it. After the SDK reports a result, confirm it server side with
`GET /v1/agemin/check/status/{sessionToken}` using the private key, and unlock content from
that response only.

Skipping that leaves an age gate a visitor can walk through from the browser console. If a
wrong answer costs nothing, skipping it is a choice you can make deliberately. For
regulated content it is not.

## Documentation

`https://agemin.com/docs`. API base `https://api.agemin.com/v1`.
