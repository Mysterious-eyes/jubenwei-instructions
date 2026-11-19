# Model inference clients

`qwen25_client.py` and `qwen3_client.py` both send the same shared system prompt followed by the sentence-annotation request. Qwen3 additionally supports its thinking switch. Both use an OpenAI-compatible endpoint and accept `--model` to select the served model.

Run commands from `jubenwei_instructions/`, the resource directory inside the repository. The model checkpoint and server are supplied by the user; training configurations are in `configs/`.

## Inputs and dependencies

Install the client dependencies:

```sh
python -m pip install -r code/inference/requirements.txt
```

Provide a UTF-8 text file with one sentence per line through `--input`. The instruction-data ZIP contains task examples rather than the separate 1,200-sentence evaluation input; the fixed reference can be recovered using the [construction workflow](../build_dataset/README.md). Both clients read `qwen3_shared_system_prompt.txt` from this directory by default. Its content is shared by both model families. Use `--system-prompt /path/to/prompt.txt` to select an explicit alternate file. Empty or unreadable prompt files are rejected before inference. The `../sps_converter/` module converts final XML into the linear representation used for scoring.

The shared file contains the SPS conventions and two complete annotated sentence examples: “勤劳的工人买了材料。” and “下雪了。”. Both model families use this prompt for the six reported conditions. Its identity and the user-request template are recorded in [conditions.json](../../evaluation/conditions.json).

Set `VLLM_BASE_URL` to the endpoint and `VLLM_API_KEY` to its key. For a service without authentication, set an explicit placeholder key. `--base-url` can override the endpoint; the API key is read from the environment.

## Run

```sh
python -B code/inference/qwen25_client.py --input /path/to/sentences.txt --model YOUR_SERVED_MODEL
python -B code/inference/qwen3_client.py --input /path/to/sentences.txt --model YOUR_SERVED_MODEL --thinking off
python -B code/inference/qwen3_client.py --input /path/to/sentences.txt --model YOUR_SERVED_MODEL --thinking on
```

Choose a distinct `--output` for each condition. The default location is `reproduced/inference/`. Existing files require an explicit `--overwrite`; `--limit` selects a small input batch. Run either client with `--help` to inspect its settings. For controlled comparisons, set the prompt, model, and request options for each condition explicitly.

Both clients send a `system` message containing the shared file and a `user` message containing the annotation request. Qwen3 also passes `enable_thinking` in the request. Both read the prompt as UTF-8 (accepting a BOM), normalize line endings through text-file reading, and strip only outer whitespace. The test case's reference XML is not sent; the shared prompt's two demonstration annotations are part of the system message.

## Outputs

Both clients save four fields per record:

| Field | Content |
|---|---|
| `Instruction` | Sentence-annotation request |
| `Reasoning` | Analysis text returned by the model, when present |
| `Output` | Final response used for XML evaluation |
| `Expression` | Linear expression converted from the final XML |

The Qwen3 client also saves `.raw.jsonl` responses and `.meta.json` run metadata next to the TXT output. Response processing separates analysis from the final answer and removes a complete enclosing XML code fence. It preserves malformed XML as returned. If an API request fails, the client stops and retains completed records.

## Evaluate saved predictions

For a new four-field client output, use the corresponding reference and the TXT scorer:

```sh
python -B code/evaluate.py --reference reproduced/public_reference/reference.json --prediction reproduced/inference/YOUR_RESULT.txt
```

To reproduce the six published conditions from the saved final answers, follow the [evaluation guide](../../evaluation/README.md).

## Offline checks

```sh
python -B -m unittest discover -s code/inference -p test_clients_offline.py
```

These checks use simulated SDK responses and temporary files to verify prompt and thinking-mode options, response separation, malformed XML handling, interrupted batches, and output protection.
