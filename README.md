# Calendly2Meet

A repository that automates filling out when2meet's with your google calendar.

## Directions

### Calendly API Key Setup

Set the `CALENDLY_API_KEY` environment variable to your Calendly API key. You can get it from [here](https://calendly.com/integrations).

```bash
export CALENDLY_API_KEY="your-api-key"
```

Check that your API key is set correctly (you should see your API key printed):

```bash
echo $CALENDLY_API_KEY
```

### Usage

1. `pip3 install requirements.txt` - installs the necessary requirements to run
2. If using Chrome, ask ChatGPT how to edit this code and make a PR; if using Firefox, download geckodriver using `brew install geckodriver`.
3. Change the variable `USER_NAME` in controller.py to your own
4. Run with the command `python3 controller.py <when2meet URL>`

## Known Issue
1. If a When2Meet spans multiple years, it fills based on your calendar for the current year
