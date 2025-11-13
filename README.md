# Candidate Ranking Demo (Superlinked)

A demo of a candidate ranking system, using [Superlinked](https://superlinked.com/) to identify the best candidate for a given position.

The system ranks candidates based on:
- **Evaluated skills** (aggregated through `CandidateEvaluation` events)
- **Expected vs. allocated pay**
- **Date of availability vs. required date of filling**
- **Textual similarity** between the candidate's self-description and the position's description

## Running the demo

```bash
uv sync
python main.py
