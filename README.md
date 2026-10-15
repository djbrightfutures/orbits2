# Orbits 2

Hands before the model. One orbit file every brain can resume.

Orbits version 1, in the Luxor share-box, stores encrypted envelopes. Orbits 2 is a different program. It is the open desk for an agent that already has a computer. It is not the Luxucleen site, and it does not open that vault.

## What a line does

A computer fact stays in this process.

```
python -m orbits2 hands hostname
python -m orbits2 hands disk
python -m orbits2 hands list C:/some/folder
python -m orbits2 hands read C:/some/folder/notes.txt
python -m orbits2 hands run whoami
```

Any other line goes to a seat. A seat is an OpenAI-compatible chat endpoint. The names that ship here are `ollama`, `cleen`, `openai`, `grok`, `opencode`, `hermes`, and `openclaw`.

```
python -m orbits2 ask --seat ollama what is on this machine
python -m orbits2 seats
python -m orbits2 tail
```

The answer is appended to `~/.orbits2/orbit.jsonl`. The next seat receives the last eight lines, so a different brain can continue the same work.

The seat's text is printed as the model wrote it. Orbits 2 does not send that text through a moderation call, and it does not rewrite it.

## Measured

On the machine this was built on, 40 hostname reads took 0.7 ms in process and 64.2 ms through a local HTTP hop that returns at once. Run it again on yours:

```
python -m orbits2 bench
```

## Seats

| name | where it points until you change it |
| --- | --- |
| ollama | `http://127.0.0.1:11434/v1` |
| cleen | `http://127.0.0.1:8088/v1` |
| openai | `https://api.openai.com/v1` |
| grok | `https://api.x.ai/v1` |
| opencode | `ORBITS2_OPENCODE_URL` |
| hermes | `ORBITS2_HERMES_URL` |
| openclaw | `ORBITS2_OPENCLAW_URL` |

A model override is `ORBITS2_<NAME>_MODEL`. A key is `ORBITS2_<NAME>_KEY`, or `OPENAI_API_KEY` / `XAI_API_KEY` for those two seats. Keys stay in the environment. They are not written into the orbit.

A seat with no URL, or a seat that does not answer, returns `seat dark: <name>`.

## What this is not

OpenClaw, Hermes, OpenCode, REA, JEV, and Bridge keep their own jobs. Orbits 2 is the short path in front of them. The computer work happens here. The rest goes to whichever brain is awake.

`run` is an argument list, not a shell. Quoted `a&b` is one argument.

The orbit is a work log on your disk. Do not type a password into it. Version 1 is the place for secrets. This version is the place for the work.

## Where it came from

The shape came from three things already running on one machine. The Orbits vault showed that a named local record outlives a chat. ABLE128 showed that an answer which can be checked should be run. HARNESS28 showed that a lesson has to earn its place. Version 2 keeps the record and the check. The vault and the self-rewrite loop stay where they are.

The Claude Code session beside this build reviewed the name against the live tree before publish.

## Test

```
python tests/test_orbits2.py
```

Nine tests. No live model. Python 3.10 or newer. The standard library is enough.

## License

MIT. Christian Rivera (DJ BrightFuture).
