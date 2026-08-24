---
name: bynn-face-search
description: >-
  Build and query a face gallery with Bynn: create a collection, enroll faces with
  your own labels and metadata, then search it with a probe image and read distance
  and similarity scores. Covers collection lifecycle, enrollment inputs, tuning
  distance_threshold and limit, interpreting matches, and deleting a face. Use for
  1:N face matching, deduplication against a known set, and returning-user
  recognition.
metadata:
  author: bynn
  version: "1.0.0"
license: MIT
---

# Face collections and search

A collection is a gallery you own. You enroll faces into it, then search it with a probe
image and get ranked matches back.

Base: `https://api.bynn.com/v1`

## Lifecycle

```
POST   /face-collections                                  create
GET    /face-collections                                  list
POST   /face-collections/{token}/enroll                   add a face
POST   /face-collections/{token}/search                   query
DELETE /face-collections/{collection_token}/faces/{face_token}   remove one face
DELETE /face-collections/{token}                          delete the collection
```

## Create

```bash
curl -X POST https://api.bynn.com/v1/face-collections \
  -H "Authorization: Bearer <YOUR_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{ "name": "returning-customers", "description": "Enrolled at first checkout" }'
```

`name` is required, up to 255 characters. Keep one collection per purpose. A gallery
mixing unrelated populations makes every threshold a compromise.

## Enroll

```bash
curl -X POST https://api.bynn.com/v1/face-collections/<token>/enroll \
  -H "Authorization: Bearer <YOUR_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "image_url": "https://example.com/face.jpg",
    "name": "Ada Lovelace",
    "external_id": "customer_8123",
    "metadata": { "enrolled_via": "checkout" }
  }'
```

Send `image_url`, `base64_image`, or a multipart `file`. Maximum 20 MB decoded.

Always set `external_id`. It is the join key back to your own record, it comes back on
every search hit, and without it a match gives you a face id and nothing actionable.
`metadata` holds up to 16 KB of anything else you want returned with a hit.

Enrollment quality decides search quality. One sharp, well-lit, forward-facing image
beats several poor ones.

## Search

```bash
curl -X POST https://api.bynn.com/v1/face-collections/<token>/search \
  -H "Authorization: Bearer <YOUR_TOKEN>" \
  -H "Content-Type: application/json" \
  -d '{
    "image_url": "https://example.com/probe.jpg",
    "limit": 5,
    "distance_threshold": 0.4
  }'
```

| Parameter | Range | Notes |
|---|---|---|
| `limit` | 1 to 100 | How many ranked matches to return. |
| `distance_threshold` | 0.1 to 1.0 | Maximum cosine distance for a hit. Lower is stricter. Omit to search the whole gallery. |

Each result carries `face_id`, `name`, `external_id`, `metadata`, `distance`, and
`similarity`.

## Reading scores

`distance` is cosine distance, so **lower is more similar**. `similarity` is
`1 - distance`, so higher is more similar. They are the same number stated two ways. Pick
one and use it consistently, because mixing them inverts your comparison and the bug is
silent.

Calibrate the threshold on your own data. A number that works for staff photos taken in
one room will not hold for user-uploaded selfies from arbitrary phones. Enroll a set you
know the truth about, search it, and look at where genuine and impostor scores separate.

Ranking is not identity. The top hit is the closest face in the gallery, which is still
returned when the right person was never enrolled. Enforce your threshold; do not just
take `results[0]`.

## Deleting

```bash
curl -X DELETE https://api.bynn.com/v1/face-collections/<collection_token>/faces/<face_token> \
  -H "Authorization: Bearer <YOUR_TOKEN>"
```

Delete on the face, not the collection, when a person asks to be removed. Deleting the
collection destroys every enrollment in it and cannot be undone.

Biometric data is regulated in most jurisdictions. Enroll people who consented, keep the
consent record, and make sure a deletion request maps to a `face_id` you can actually
find. `external_id` is what makes that possible.

## Over MCP

`create_face_collection`, `list_face_collections`, `enroll_face`, `search_faces`,
`delete_face`, `delete_face_collection`. See `bynn-mcp`.
