# Personal Agent
Personal Agent to automate common tasks

### Forward-looking features

- Tasks list (to-do and administrative)
- Golf booker
- Haircut booker
- Calendar integration
- Email integration

### To-do

- Deploy the app
- Structure tool outputs into a pydantic model
- ~~- Finish tennis booking~~
- Prompt engineering updates
- Calendar tool
- ~~- Telegram hooks~~


### Local Testing:

1. `ngrok http 8000` # start a proxy URL for localhost
2. `curl -X POST "https://api.telegram.org/bot{bot-id}/setWebhook" \
     -d "url={ngrok-generated-url}/telegram/webhook"` # set the telegram hook 


