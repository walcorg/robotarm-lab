# Policy

Learned manipulation skills, trained with [LeRobot](https://github.com/huggingface/lerobot).

Each skill is one primitive the MCP backend can run: `pick@station`, `place@station`, later
`pour`, `open_lid`. Claude chooses skills; the policy executes them.

## Per skill, commit

- `skills/<name>/config.yaml`: LeRobot training config
- `skills/<name>/CARD.md`: dataset id on the Hub, number of episodes, training hardware,
  success rate over N trials, known failure modes

## Notes

- Record with the leader arm, ≥ 50 episodes per skill, varied lighting and object pose within
  the station guides.
- Training needs a modern NVIDIA GPU (≥ 12 GB). Inference runs on a smaller one.
- Wrist cameras feed the policy; the overhead camera feeds both the policy and the detector.
