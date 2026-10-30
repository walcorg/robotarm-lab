# Scene schema

What Claude reads after every action and from `get_scene`. Text first: images cost about a
thousand tokens each and are only sent on request.

```json
{
  "timestamp": 1793393536.47,
  "estopped": false,
  "objects": [
    { "id": "C03", "class": "cup",  "station": 3,    "held_by": null,   "confidence": 0.97 },
    { "id": "V01", "class": "vial", "station": null, "held_by": "right", "confidence": 0.93 }
  ],
  "hands": [
    { "name": "left",  "grip": "open",    "holding": null,  "at_station": null },
    { "name": "right", "grip": "holding", "holding": "V01", "at_station": 4 }
  ]
}
```

| Field | Type | Notes |
|-------|------|-------|
| `timestamp` | float | Unix time the scene was assembled |
| `estopped` | bool | True while any stop is latched |
| `objects[].id` | string | Stable id; assigned by the detector or the station marker |
| `objects[].class` | string | Detector class (`cup`, `vial`, …) |
| `objects[].station` | int \| null | Station id, or null while held |
| `objects[].held_by` | `"left"` \| `"right"` \| null | |
| `objects[].confidence` | float 0–1 | Detector confidence; 1.0 in simulation |
| `hands[].grip` | `"open"` \| `"closed"` \| `"holding"` | `closed` with no object means a failed grasp |
| `hands[].holding` | string \| null | Object id |
| `hands[].at_station` | int \| null | null = home pose |

Rules:
- An object is either in exactly one station or held by exactly one hand.
- A station holds at most one object.
- Objects outside any station are not reported; the human must place them in a station.
