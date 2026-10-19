# ZOREAL

Skills for integrating [ZOREAL](https://zoreal.com), the trust layer that proves a real
human is present behind a digital interaction: Login with ZOREAL, the ZOREAL Meet
meetings API, and the ZOREAL Book scheduling embed.

## Install

```
/plugin marketplace add Bynn-Intelligence/skills
/plugin install zoreal@bynn
```

Any agent, via the skills CLI:

```bash
npx skills add Bynn-Intelligence/skills --skill zoreal --skill zoreal-identify --skill zoreal-meet
```

## Skills

| Skill | Covers |
|---|---|
| `zoreal` | Router. What each ZOREAL product proves, which ones have a developer integration, and why ZOREAL Verify work goes through the Bynn skills. |
| `zoreal-identify` | Login with ZOREAL: the client libraries, auth-code and button flows, scopes, requiring a live human with `acr`, the assurance block. |
| `zoreal-meet` | The meetings API, host controls, the door and the presence rule, and the ZOREAL Book embed. |

## ZOREAL Verify

ZOREAL Verify, which includes PDFChecker, runs its identity and document checks through
the Bynn API today. Install the `bynn` plugin and use `bynn-document-fraud` and
`bynn-kyc-sessions` for that work.

## Credentials

| Product | Get it at |
|---|---|
| Login with ZOREAL | `https://zoreal.com`, Assets: the client id (`ast_...`) and the backend's client secret or JWKS |
| Meetings API | `https://zoreal.com`, Settings, API keys |
| ZOREAL Book embed | Nothing but the booking link from Meet, Book |

There are no test identities. Enrol a ZOREAL ID for yourself from
`https://zoreal.com/download` to develop and test.

## Documentation

`https://zoreal.com/documentation`, the provider at
`https://id.zoreal.com/.well-known/openid-configuration`, and each client library's README
at `https://github.com/Bynn-Intelligence`.
