---
name: zoreal-meet
description: >-
  Integrate ZOREAL Meet and ZOREAL Book. The Meet meetings API creates and
  schedules meetings (with recurrence), lists them with their attendees, reads
  a session's transcript, ends a meeting or a series, and runs host controls:
  the knock-to-enter door, room policy, the presence rule that requires a
  verified live human, transcription, encryption and moderation. ZOREAL Book
  puts the Meet scheduling pages on your own site with one script tag,
  @zoreal/book-js or @zoreal/book-react, with prefill, metadata and booking
  events. Use for any ZOREAL Meet, verified meeting, or ZOREAL Book embed work.
metadata:
  author: bynn
  version: "1.1.0"
license: MIT
---

# ZOREAL Meet and ZOREAL Book

Meet is video and voice meetings where a participant can prove they are a real, enrolled,
live person, or that and their verified legal name. Book is the scheduling inside Meet: a
guest picks a free slot, and a booking with a room becomes a scheduled Meet call.

| Thing | Value |
|---|---|
| API base | `https://api.bynn.com/v1/zoreal/meet` |
| API key | zoreal.com, Settings, API keys |
| Documentation | `https://zoreal.com/documentation` |
| A room, for people | `https://meet.zoreal.com/<code>` |
| Book embed script | `https://book.zoreal.com/embed.js` |

## Credentials

Two kinds appear in the API, and mixing them up is the usual first bug.

- **The API key** authenticates your organization for account operations: create, list,
  read notes. It starts with `private_` or `public_`, with `sandbox_` added on test
  keys, and goes in `Authorization: Bearer <key>`. Keep it on your server.
- **The `host_token`** is returned once, when a meeting is created, and authorizes the
  host controls for that one room. Only a digest is stored, so keep it if the meeting
  will be managed later. Host controls take it in the JSON body. The meeting's owner may
  omit it and send the API key instead.

Host controls answer **404, never 403**, for a wrong or missing credential, so they
never confirm that a code exists. Read a 404 there as "check the credential" first.

Requests to the meetings surface are limited to 30 a minute per address.

## Create a meeting

```bash
curl -X POST https://api.bynn.com/v1/zoreal/meet/instant \
  -H "Authorization: Bearer $ZOREAL_API_KEY" \
  -H "Content-Type: application/json" \
  -d '{ "title": "Weekly sync" }'
```

```json
{
  "room": { "code": "kfm-qhtz-pgd", "created_at": "...", "began_at": null, "title": "Weekly sync", "e2ee": false },
  "host_token": "<HOST_TOKEN>"
}
```

- `title`: up to 80 characters, shown to everyone with the link.
- `e2ee`: end-to-end encryption, default `false`. It can be turned on later only while
  the host is alone in the room, and never off. An encrypted call cannot be transcribed.
- The code is `xxx-xxxx-xxx`, lowercase letters without `l`. People join at
  `https://meet.zoreal.com/<code>`.
- A meeting holds up to 25 people and a call runs up to 90 minutes from the host's first
  join. The link survives the cap.
- 503 means no media node can take a new room right now. Retry with backoff.

**Scheduling** is the same call with schedule fields; there is no separate endpoint:

| Field | Notes |
|---|---|
| `scheduled_at` | ISO 8601 start |
| `scheduled_minutes` | 1 to 600 |
| `scheduled_tz` | An IANA zone name, not an offset, so a series keeps its local time across daylight saving. An unknown zone answers 422. |
| `recurrence` | An RRULE body. Only `FREQ` (`DAILY`, `WEEKLY`, `MONTHLY`), `INTERVAL` and `UNTIL` are honored; anything else is accepted and ignored, so `BYDAY` does not do what it says. |

A scheduled link opens 30 minutes before its start, for the host too.

## Change, end and read meetings

| Call | Does |
|---|---|
| `POST /v1/zoreal/meet/instant/:code/host/title` | Rename (`title`, empty clears). Also works on an ended meeting; `session_id` renames one past session. |
| `POST /v1/zoreal/meet/instant/:code/host/schedule` | Move a scheduled meeting (`scheduled_at`, `scheduled_minutes`, `notify` re-sends invitations). A series moves as a whole. 409 if it was never scheduled. |
| `POST /v1/zoreal/meet/instant/:code/host/end` | `scope`: `occurrence` (default) closes this date, `series` ends the call and retires the link. A meeting is ended, never deleted. |
| `GET /v1/zoreal/meet/instant/meetings` | The meetings your account owns, newest first, with attendees. `limit` (1 to 100), `before` (the last row's `cursor`), `q`, `from`, `to`, `tags[]`, `horizon_days`. Past rows carry `session_id`. |
| `GET /v1/zoreal/meet/instant/:code` | A meeting's public state before joining. No credential needed. No attendees here. |
| `GET /v1/zoreal/meet/instant/:code/sessions/:session_id/notes` | The transcript, speaker by speaker. Owner only. `status`: `processing`, `ready`, `empty`, `failed` or `none`. Add `/pdf` for a PDF. |

Pagination is a cursor, never an offset. Notes exist only when transcription was started
in the call.

## Host controls on a live room

All take `host_token` in the body (or the owner's API key) and name a participant by
`identity`, which is minted per join: someone who leaves and returns is a new identity.

| Call | Does |
|---|---|
| `POST .../:code/host/mute`, `.../host/remove` | Mute (the participant can unmute) or remove |
| `POST .../:code/host/promote` | Make a participant a co-host. Only the creator may promote. |
| `POST .../:code/host/transcription` (`DELETE` to stop) | Start capturing audio for notes. Visible to everyone in the room; 409 in an encrypted room. |
| `POST .../:code/host/policy` | Toggle `screen_share`, `microphone`, `camera`, `messages`, `reactions`, `knock`. Send any subset; the response is the whole policy. |
| `POST .../:code/host/presence` | The presence rule: `level` is `poh` (a live human), `poh_kyc` (adds a verified identity) or the literal `off`; `unproven_access` is `full` (stay in, marked Unproven) or `denied` (wait outside until proven). |
| `POST .../:code/host/encryption` | Turn on end-to-end encryption, one way, only while the host is alone |

(`...` is `https://api.bynn.com/v1/zoreal/meet/instant`.)

**The door.** With `knock` on, which is the default, a guest calls `POST .../:code/knock`
with a `name` and gets a `knock_token`, then polls `GET .../:code/knock/:knock_token`
every couple of seconds (`pending`, `admitted`, `denied`, `ended`). The poll is the
heartbeat: a knock unseen for ten seconds drops off the host's list. Hosts read the queue
with `POST .../:code/host/knocks` (a POST, so the credential never sits in a query
string) and answer with `.../host/admit` or `.../host/deny`.

## ZOREAL Book on your own site

The booking link from zoreal.com (Meet, Book) is the only thing the embed needs, for
example `acme/kwm-drpt`; a handle alone (`acme`) shows every active event type. There is
no key in the browser.

```html
<script src="https://book.zoreal.com/embed.js" data-zoreal-book="acme/kwm-drpt" async></script>
```

Or the package:

```js
import ZorealBook from '@zoreal/book-js';   // npm install @zoreal/book-js

ZorealBook.init();
ZorealBook.inline({ link: 'acme/kwm-drpt', element: '#book', config: { metadata: { lead_id: 'L-4471' } } });
ZorealBook.on('bookingSuccessful', ({ booking }) => crm.attach(booking.metadata.lead_id, booking.id));
ZorealBook.on('linkFailed', ({ link, reason }) => {
  if (reason === 'embed_not_available') showPlainLink(ZorealBook.hostedUrl(link));
});
```

React: `npm install @zoreal/book-react` for `<ZorealBook />`, `ZorealBookProvider`,
`useZorealBook()` and `useZorealBookEvent()`. Ways to show it: `inline`, `modal`,
`floatingButton`, `redirect`.

What to know:

- **Each event type sets a requirement**: `open` (name and an email confirmed with a
  code), `verified_human` (a live human with ZOREAL ID, no name disclosed) or
  `verified_identity` (a verified legal name). The embed can neither raise nor lower it.
- **Events carry no guest name, email or identity.** Match a booking back to your own
  records with `metadata`: up to ten string pairs, returned on every event.
- **Prefill never travels in the URL.** It is posted to the frame after it loads, and
  `redirect()` and `hostedUrl()` drop the personal fields.
- **Embedding depends on the plan.** Without it, `linkFailed` fires with
  `embed_not_available`; fall back to the hosted link.
- **A site with a Content Security Policy** needs `frame-src https://book.zoreal.com`,
  and `script-src https://book.zoreal.com` when loading the hosted script.

Full reference: the READMEs at `https://github.com/Bynn-Intelligence/zoreal-book-js` and
`https://github.com/Bynn-Intelligence/zoreal-book-react`.
