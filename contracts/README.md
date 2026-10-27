# The contract

What you get, how we run your system, and what it hands in. Nothing else is part of the contract.

## What you get

The practice dataset: one row per sentence of the practice part of the Hooly universe, as one CSV file, `practice.csv`, with its lexicon, `lexicon.json`.

| Column | Holds |
| --- | --- |
| `id` | The row's id |
| `text` | The sentence |
| `date` | The date of the page it comes from |
| `label` | `true`, `false` or `unsure`: whether the sentence is true on its date |
| `form` | The facts the sentence states, as JSON: for each, its `subject`, its `attribute` and its `value` |

- **`false`** when the sentence states at least one false value; **`unsure`** when the dataset itself gives no means to tell; **`true`** otherwise.
- **The lexicon** (`lexicon.json`) lists every subject the dataset names, with its aliases and its attributes, and the events.

## How we run your system

After the freeze we run every team's system once, from the commit its pull request held at the freeze. A push to the pull request after the freeze, or closing it, disqualifies the team, and its system is not run.

- **One image,** built from the `Dockerfile` at the root of your repository with `docker build --platform linux/amd64 .`, at most 3 GiB unpacked. The build has the network; the run does not.
- **Its `USER` is not root:** an image with no `USER`, or with `root` or `0`, is refused before it runs. End the `Dockerfile` with `USER 10001`, the user every run starts as.
- **One run, offline:** no network, 2 CPUs, 6 GiB of memory, at most 256 processes and threads, on a read-only root. `/tmp` is writable, up to 128 MB counted in the memory, and `/output` up to 256 MB.
- **No home directory.** The user 10001 has no home, and nothing outside `/tmp` and `/output` is writable. Point `HOME` and the caches of your libraries, such as `XDG_CACHE_HOME` and `HF_HOME`, at `/tmp`, or put what they hold into the image.
- **30 minutes.** At the deadline the run gets `SIGTERM`, and 10 seconds later it is stopped. `ARENA_DEADLINE` holds the deadline in Unix seconds.
- **Its input exists only when we run it,** read-only at `/universe/`: `universe.csv`, rows with the columns `id`, `text`, `date` and `label`, and `lexicon.json`, their lexicon. The rows of the practice dataset are among them, with their labels; every other row has an empty `label`. Your system must scale to an input much larger than the practice dataset. The input has no `form` column; your image may hold the practice dataset, forms included.
- **It writes one table to `/output/output.csv`.** The table on disk when the run ends counts, at the deadline too; a run that leaves no table there hands in nothing. A table still being written at the deadline counts as it stands, so write it under another name in `/output` and rename it to `output.csv` when it is complete.

## What your system hands in

One table, as CSV at `/output/output.csv`, at most 16 MiB, with these columns in any order. It is UTF-8, and its first row names the columns. A cell that holds a comma, a quote or a line break is quoted, as any CSV library writes it, or the row splits and is invalid. A CSV as Excel writes it with a Romanian locale, with semicolons and a decimal comma, reads too.

| Column | A label for an input row | A new claim |
| --- | --- | --- |
| `id` | The input row's `id` | The claim's id, unique in the table: letters, digits, `.`, `_` or `-`, at most 64 |
| `type` | Empty | `fact`, `compare`, `change`, `at_event` or `relation` |
| `text` | Empty | The claim, at most 300 characters, stated in one sentence in the forms of [`claim-forms.md`](claim-forms.md) |
| `form` | Empty | The claim in structured form, as JSON (below, and [`entry.schema.json`](entry.schema.json)) |
| `label` | `true`, `false` or `unsure`: whether the row's sentence is true on its date | `true`, or empty: every claim must be true |
| `confidence` | How sure your system is that its label is right, from 0.5 to 1; empty for `unsure` | How sure your system is that the claim is true, from 0.5 to 1 |

- **A row with an empty `type` labels the input row its `id` names.** Write one for each row of the input whose `label` is empty. The first row for an id counts; a row for an id the input does not hold, or for a row the input labels already, is ignored. An unlabelled row with no label counts as `unsure`.
- **A row with a `type` is a new claim** about Hooly, true on its date. Each is an entry of [`entry.schema.json`](entry.schema.json), with `tag` `true`.
- **Every claim must be true.** A claim whose `label` is neither `true` nor empty is invalid.
- **Every claim must be new.** A claim whose text is a row of the input is not new.
- **Exactly 1,000 claims.** The first 1,000 are judged and the claims after the 1,000th are not. An invalid claim takes its place in the 1,000 too, and so does a row that is not CSV. Each claim missing from the 1,000 scores nothing and still counts in them.

```csv
id,type,text,form,label,confidence
x-1,,,,true,0.9
x-2,,,,unsure,
e1,compare,Hooly Workspace costs more than Hooly AI Pro.,"{""left"": {""subject"": ""Hooly Workspace"", ""attribute"": ""price""}, ""right"": {""subject"": ""Hooly AI Pro"", ""attribute"": ""price""}, ""op"": ""gt""}",true,0.9
```

### The form of each type

| `type` | `form` | True when |
| --- | --- | --- |
| `fact` | `subject`, `attribute`, `value` | the fact has the value on 29 Oct 2026 |
| `compare` | `left`, `right` (each a `subject` and an `attribute`), `op`: `gt`, `lt` or `eq` | the two facts' values compare so on 29 Oct 2026; between dates `gt` is after and `lt` before |
| `change` | `subject`, `attribute`, `from`, `to` | the fact held `from`, and later `to` |
| `at_event` | `subject`, `attribute`, `event`, `value` | the fact had the value on the date of the event `event` names |
| `relation` | `subject`, `link`, `target`, `attribute`, `value` | the `attribute` of `target`, the entity the subject's `link` names, had the value while `link` named it |

`examples/entry/good/` holds one of each type.

- **Each fact** is named by its subject and attribute, as the lexicon gives them: a subject's name or alias in any case, and an attribute exactly as the lexicon writes it. A subject no entity has, or an attribute the subject lacks, makes the entry invalid.
- **A value** is exact, as [`claimed_value.schema.json`](claimed_value.schema.json) writes it, with no `op`: a claim that one value is more or less than another is a `compare`.
- **The text** must say what the claim says. One of its sentences holds the claim in the forms of [`claim-forms.md`](claim-forms.md), with its values written as [`value-forms.md`](value-forms.md) writes them; other sentences may say anything. That sentence holds nothing the claim could be read against instead: for a `fact`, `at_event` or `relation`, no other value of the claim's kind and no date or time word of its own; for a `compare`, no value, number or date at all; and for a yes or no, the fact's attribute in words. A `change` may say when its value changed.
