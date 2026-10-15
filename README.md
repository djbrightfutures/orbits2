# Orbits 2

The pit. Hands before the model. One orbit file every brain can resume.

Version 2.1.0. The record on disk stays version 2, so a line written by 2.0.0 still reads.

Orbits version 1, in the Luxor share-box, stores encrypted envelopes. Orbits 2 is a different program. It is the open desk. It is not the Luxucleen site, and it does not open that vault.

A fact runs in this process and becomes a lap. A lap has a number, a time, and a check code of the ask and the answer. The next brain reads the file and continues. Nothing in that answer is rewritten.

## The card

This is `python -m orbits2 pit` on the machine it was built on, 2026-10-15. The crown is cleen because the hop race shown below was already in that orbit.

```
+--------------------------------------------------------------+
|                                                              |
| ORBITS 2  /  THE PIT                                         |
| hands before the model                                       |
| one orbit file. every brain resumes. nothing is rewritten.   |
|                                                              |
+--------------------------------------------------------------+
+--------------------------------------------------------------+
| ORBITS 2  /  THE PIT                                  lap 04 |
| SEE                                                  MACHINE |
+--------------------------------------------------------------+
| 0.22 ms                                                      |
| crown cleen                                                  |
+--------------------------------------------------------------+
| MACHINE                                                      |
| HOST     DjBFs                                               |
| USER     djbfs                                               |
| CWD      C:\Users\djbfs\orbits2                              |
| DISK     1189.8 GB free of 1905.8 GB                         |
| PYTHON   3.13.14                                             |
| CLOCK    2026-10-15 16:20:00Z                                |
|                                                              |
| STAMP  7e0ccd56                                              |
+--------------------------------------------------------------+
+--------------------------------------------------------------+
| ORBITS 2  /  THE PIT                                   BOARD |
+--------------------------------------------------------------+
| 01 RAN 0.08  02 RACE 1.71  03 HELD 0.50  04 SEE 0.22         |
| crown cleen                                                  |
| 01 RAN      0.08 ms  hostname                                |
| 02 RACE     1.71 ms  say hop cleen                           |
| 03 HELD     0.50 ms  prove                                   |
| 04 SEE      0.22 ms  see                                     |
|                                                              |
| ollama     awake  127.0.0.1:11434                            |
| cleen      awake  127.0.0.1:8088                             |
| openai     dark   no key                                     |
| grok       dark   no key                                     |
| opencode   dark   no url                                     |
| hermes     dark   no url                                     |
| openclaw   dark   no url                                     |
+--------------------------------------------------------------+
```

Local ports were awake because a connect succeeded. No model was loaded to draw that light. Cloud seats in this run had no key in the environment. When a key is set, the light says `key`. The key is not printed and it is not written into the orbit.

## Three laps

A fact, in this process:

```
+--------------------------------------------------------------+
| ORBITS 2  /  THE PIT                                  lap 01 |
| HANDS                                                    RAN |
+--------------------------------------------------------------+
| 0.08 ms                                                      |
| crown none                                                   |
+--------------------------------------------------------------+
| ASK                                                          |
| hostname                                                     |
| DID                                                          |
| DjBFs                                                        |
|                                                              |
| STAMP  2be589e3                                              |
+--------------------------------------------------------------+
```

A race. For this measurement both names pointed at one local hop that returns the word `hop`. Same answer. The clock picked the winner. Neither line was changed.

```
+--------------------------------------------------------------+
| ORBITS 2  /  THE PIT                                  lap 02 |
| DUEL                                                    RACE |
+--------------------------------------------------------------+
| 1.71 ms                                                      |
| crown cleen                                                  |
+--------------------------------------------------------------+
| FIELD                                                        |
| cleen  1.71 ms                                           WIN |
|   hop                                                        |
| ollama  1.73 ms                                         LIVE |
|   hop                                                        |
|                                                              |
| STAMP  2aa94fe9                                              |
+--------------------------------------------------------------+
```

Then prove. It re-ran the hostname lap. The machine still said DjBFs, so the lap is witnessed. The race is not a fact, so prove left it alone.

```
+--------------------------------------------------------------+
| ORBITS 2  /  THE PIT                                  lap 03 |
| PROVE                                              WITNESSED |
+--------------------------------------------------------------+
| 0.50 ms                                                      |
| crown cleen                                                  |
+--------------------------------------------------------------+
| CHECK                                                        |
| facts checked    1                                           |
| witnessed        1                                           |
| drifted          0                                           |
| tampered         0                                           |
| runs left alone  0                                           |
| model laps are not re-run. a model is not a fact.            |
|                                                              |
| STAMP  5a7ef37f                                              |
+--------------------------------------------------------------+
```

`stamp 2be589e3` finds that hostname lap again. If the line in the file no longer matches its code, prove says tampered.

## Measured

On 2026-10-15, 40 hostname reads took 0.68 ms in this process and 52.68 ms through a local HTTP hop that returns at once.

```
python -m orbits2 bench
```

The first publish, the same day, measured 0.7 ms and 64.2 ms. Run it on yours. The number that matters is the one you just measured.

## Commands

```
python -m orbits2 pit
python -m orbits2 live
python -m orbits2 see
python -m orbits2 prove
python -m orbits2 duel what is on this machine
python -m orbits2 duel --seats ollama,cleen what is on this machine
python -m orbits2 relay --seats ollama,cleen what is on this machine
python -m orbits2 stamp 2be589e3
python -m orbits2 hostname
```

`live` stays open. An empty line shows the board. `quit` leaves.

`duel` with no names races local seats whose port accepts a connection. A cloud seat is called only when you name it. You pay that seat's bill. The field waits, then the fastest answer that is not `seat dark:` wins. The others stay on the card with their times. A tie keeps the earlier name.

`relay` sends the ask through the seats you name, up to four. Each seat sees the previous seat's raw text.

`prove` re-runs hostname, whoami, cwd, disk, python, list, and read. The same answer is witnessed. A different answer drifted. `run` is an action, so it is not repeated. A model lap is not a fact.

`hands hostname` prints the fact and does not write a lap. A bare `hostname` writes the lap.

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

A model override is `ORBITS2_<NAME>_MODEL`. A key is `ORBITS2_<NAME>_KEY`, or `OPENAI_API_KEY` / `XAI_API_KEY` for those two seats. Keys stay in the environment.

A seat with no URL, or a seat that does not answer, returns `seat dark: <name>`.

The orbit is `~/.orbits2/orbit.jsonl`. The last card is also `~/.orbits2/pit.txt`. A line can carry `v`, `t`, `lap`, `kind`, `seat`, `ask`, `did`, `ms`, `winner`, `proof`, `stamp`, and `racers`. Old lines omit the newer fields.

## What this is not

OpenClaw, Hermes, OpenCode, REA, JEV, and Bridge keep their own jobs. Orbits 2 is the short path in front of them.

`run` is an argument list, not a shell. Quoted `a&b` is one argument.

The orbit is a work log on your disk. Do not type a password into it. Version 1 is the place for secrets. This version is the place for the work.

There is no moderation pass. The seat's text is stored and printed as it arrived.

## Where it came from

The shape came from three things already running on one machine. The Orbits vault showed that a named local record outlives a chat. ABLE128 showed that an answer which can be checked should be run. HARNESS28 showed that a lesson has to earn its place. The pit keeps the record, the race, and the check. The vault and the self-rewrite loop stay where they are.

The Claude Code session beside the first publish was told the name. That session has not committed to this repo.

## Test

```
python tests/test_orbits2.py
```

30 tests. No live model. Python 3.10 or newer. The standard library is enough.

## License

MIT. Christian Rivera (DJ BrightFuture).
