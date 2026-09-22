# DECISIONS

Notes on what I built, what I skipped, and why. Written as I went.

## The 4-6 hour budget

I got the assignment brief and the starter zip late in the evening on the
20th and had the deadline the next day. Realistically I had one long
sitting rather than two shorter ones spread over days, so I prioritised:

1. Parts 1 and 3 first (architecture, validation, observability) — those
   are the pillars they evaluate hardest and the ones I have opinions on.
2. Part 4 second (reporter ) — most of the marks for "production
   readiness" live here.
3. Part 2 last (efficiency) — real but bounded, and the synthetic feed
   is small enough that the biggest wins are structural (skip work you
   don't need to do) rather than deep optimisation.


## Assumptions and open questions

Things I assumed because there wasn't time to ask, and the questions I
would have asked the product / ML team on day one of a real engagement:

- **Video stability.** I assumed the video's frame dimensions come from
  the file itself and stay constant across the file. The prototype hard-
  coded 1280x720; I read from `cv2.CAP_PROP_FRAME_WIDTH/HEIGHT` instead.
  A real feed with variable resolution mid-stream would need per-frame
  handling — I'd want to know if that's actually a thing.
- **Frame ordering.** I assumed frames are read in order and the frame
  index is monotonically increasing. No re-ordering, no gaps that matter
  for aggregation.
- **Detection semantics.** I assumed the "boundary polygon" is a single
  connected region per frame — largest contour, no multi-pitch scenes.
  For a broadcast with picture-in-picture that would be wrong.
- **What "boundary found" means.** I chose to reject detections that
  cover more than 90% of the frame because on the synthetic feed those
  are close-ups or noise, not real pitch shapes. On real footage the
  threshold would need tuning per sport / camera setup.
- **Aggregation over time.** I compute a mean intersection area across
  valid detections. In production I'd probably want a median (robust to
  outliers) and possibly a sliding-window aggregate to detect drift. I'd
  ask the ML team what the downstream crop layer actually consumes.
- **Reporter contract.** I chose the payload shapes myself. I would want
  the platform team to own that schema — they know what the orchestrator
  actually needs to make routing / retry decisions. My models are a
  strawman.
- **Run ID lifecycle.** I let the runner generate one if config doesn't
  supply one. In production the orchestrator would supply it. Config
  takes precedence over auto-generation, so both paths work.

## Validation strictness vs fallback

I fail fast almost everywhere. The one meaningful "fallback" is that
reporting is optional at the config level — a config with no `reporter`
block runs the pipeline without any HTTP traffic. That's for local dev,
not production.

**Failing fast:**

- Config uses `extra="forbid"` on every model. Unknown keys, misspelled
  keys, wrong types, out-of-range values all raise ValidationError at
  load time. This actually caught a real typo of mine during development
  (`max_attemps` vs `max_attempts`) — the pipeline refused to start and
  named the field. That's exactly the behaviour the assignment asks for
  and I got to prove it works on myself.
- Missing config file, malformed YAML, and non-mapping YAML all map to
  `ConfigError` with a clear message. Exit code 2.
- `MaskColorDetector.__init__` re-validates `min_area > 0` even though
  the config already does. Defence in depth — the class doesn't trust
  its caller.
- `FieldBoundaryAnalyzer.process_video` raises `PipelineError` if it
  can't open the video file. Previously it printed and returned
  silently with exit code 0 — the orchestrator would have thought the
  run succeeded. Caught by running the code with the file deleted.
  Exit code 3 now.

**Allowing recoverable failures:**

- Individual bad frames don't kill the run. If the detector raises
  something other than `DetectorError`, the pipeline logs it as a
  `frame_detection_failed` warning with the frame index and continues.
  A `DetectorError` (per the detector's contract, fatal) does propagate.
- Reporter failures never affect the pipeline outcome. If the retry
  loop exhausts its attempts, we log a warning and carry on. Rationale:
  the assignment explicitly says a downed reporter must not masquerade
  as a pipeline failure.
- Dead fields in the prototype config (`crop_search`, `debug_mode`,
  `confidence_threshold`) I dropped from the model rather than
  preserving. Silent unused config is worse than no config. If someone
  implements a crop-search layer later, they add it back with real
  validation.

## Performance trade-offs

The prototype processed every frame equally. My pipeline:

- Skips frames without enough green (a cheap HSV pre-check) before
  running the expensive detector. This is the big win — camera cuts
  and non-pitch frames don't pay detection cost. On the synthetic feed
  ~55 frames out of 1800 get skipped this way. On a real feed with more
  camera cuts, the ratio would be much higher.
- Hoists the outer-boundary polygon out of the frame loop. It's
  constant per video, no reason to reconstruct it 1800 times. Marginal
  on the synthetic feed; would add up on a 4-hour match feed.
- Reads frame dimensions from the video, not config. This is also a
  correctness fix: the prototype hardcoded 1280x720, so the
  intersection-area metric would have silently gone wrong on any other
  resolution.
- Doesn't cache anything expensive because there isn't anything else
  expensive that runs more than once. If a real ML detector were
  plugged in with per-sport model weights, that's where I'd add
  `functools.lru_cache` on a `load_weights(sport)` function. I don't
  have that model to justify the abstraction yet.

The `time.sleep(0.005)` per frame is left in as the prototype had it —
it's simulating detector latency that a real detector would incur. The
efficiency wins above are what would matter with a real detector.

## Observability choices

Structured JSON logs, one object per line, to stderr. Every line carries
`run_id`, `event`, `level`, `logger`, `timestamp` (UTC-aware),
`message`, plus whatever context the call site added via `extra=`.

I used stdlib `logging` with a custom `JsonFormatter` rather than
`structlog`. Fewer dependencies, and the shape is standard enough that
a log aggregator (Loki, Datadog, CloudWatch) will parse it without any
special handling. If the codebase grew and I needed context-manager
scoping of fields, I'd probably reach for structlog.

Every log event has a distinct `event` field name (`run_starting`,
`video_open`, `frame_detection_failed`, `reporter_event_not_delivered`,
etc.) so operators can filter by event type without regex-matching
message strings.

Exit codes map to failure type:
- 0 success
- 2 config error
- 3 pipeline / detector fatal
- 4 reporter fatal (reserved; currently unused because reporter failures
  are downgraded to warnings)

## The `except Exception` inside the frame loop

Normally a bare `except Exception:` is a code smell. In
`FieldBoundaryAnalyzer.process_video` I have one deliberately, and I
want to flag why:

- The `FieldDetector` protocol's contract is "return None for bad
  frames, raise `DetectorError` for fatal errors." Anything else is a
  contract violation.
- I catch `DetectorError` explicitly and re-raise (fatal).
- I catch generic `Exception` after that and log-and-continue. This
  absorbs contract-violating exceptions from buggy detector
  implementations. In an unattended overnight run I'd rather lose one
  frame's detection than crash the whole run because a third-party
  detector regressed.
- The exception is logged with `error_type` and `error` fields at
  WARNING level, so nothing is silent.

Alternative: crash and let the orchestrator restart. Reasonable, and I'd
consider it. Right now I've optimised for "one bad frame doesn't waste
1799 good ones." Would want to discuss.

## Reporter design

- Payloads are Pydantic models (`ProgressPayload`, `EventPayload`) with
  `extra="forbid"`. Same validation discipline as config.
- `RunSummary` is used both as a local return value and as a field on
  `EventPayload`. One model, two consumers.
- Retries via `tenacity`: up to `max_attempts` (default 3),
  exponential backoff (0.5s, 1s, 2s capped at 4s), only on transport
  exceptions (`requests.RequestException`). A bug that raises something
  else surfaces on the first attempt.
- Reporter failures return `False` from `send_progress` /
  `send_event`. The runner logs a warning and doesn't touch the exit
  code. This is the "reporter failure is not a pipeline failure"
  behaviour, end-to-end.

I did not implement periodic progress heartbeats mid-run. `ProgressPayload`
exists in the model layer but the runner only sends events, not
progress. On a real long-running feed I'd add a heartbeat every N
frames or every N seconds. Skipped for time; obvious next thing to add.


I did not add a healthcheck on mock_api. `depends_on` only waits for
container start, not readiness. In practice mock_api's Flask app is up
in a couple of seconds — well before the pipeline's first HTTP call —
and the retry loop absorbs any race. In production I'd add a
healthcheck plus `depends_on: [mock_api: {condition: service_healthy}]`
so start ordering is deterministic.

## AI / LLM disclosure

I used Claude (Anthropic's assistant, accessed via the web UI) heavily
throughout this exercise. Honest breakdown:

- **Planning and roadmap.** I discussed the assignment with Claude
  before writing code — talked through what the assignment was asking
  for at each part.
- **Code generation.** Reviewed with Claude for better results.
- **Debugging.** Debugged with Claude where I got stucked.

Using an LLM as a pair rather than a code generator is what I'm
comfortable with. It's faster than writing everything from scratch and
slower than "just accept the output." The trade is: I understand every
line of code in this repo and can defend any design decision here. If
you interview me on it, I can walk you through the reasoning.

## Things I'd do next

I could not run the project with docker as my machine was not supporting the docker for recent os updates. That would be my first priority.