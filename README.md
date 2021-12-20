# volume-control

raspberry pi python service to change the receiver volume on keyboard input from
USB volume knob

## notes

you need a `config.json` in the root directory to load your auth keys -
currently just switchbot auth key. example `config.json` looks like this:

```json
{
  "switchbot_auth": "[auth key here]"
}
```
