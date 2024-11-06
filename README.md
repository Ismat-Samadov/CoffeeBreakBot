# Break Request Bot

This Telegram bot enables employees to request breaks with a specific duration and notifies a group of approvers for approval or denial. It supports department selection, customizable break duration, and real-time notifications for both employees and approvers.

## Features

- **Department Selection**: Employees select their department from a list.
- **Break Duration**: Employees choose a break duration from a predefined list.
- **Approval Workflow**: The bot sends each request to a designated approver group, with options for approval or ignoring.
- **Notifications**: Employees receive notifications on whether their break request was approved or ignored.
- **Timeout Handling**: If a conversation is idle for 5 minutes, it automatically ends.
- **Cancel Command**: Employees can cancel a request at any point with `/cancel`.

## Prerequisites

- Python 3.8+
- A Telegram bot token from [BotFather](https://t.me/BotFather)
- Access to a Telegram group for approvers

## Installation

### Example `.env` File

Create a file named `.env` in the root of your project directory and add the following content, replacing the placeholders with your actual values:

```plaintext
# The token for your Telegram bot from BotFather
BOT_TOKEN=your_bot_token

# The chat ID of the group where approvals will be sent
# Ensure the ID starts with a "-" for groups (e.g., -1001234567890)
GROUP_CHAT_ID=-123344444
```

- **BOT_TOKEN**: The token you receive from [BotFather](https://t.me/BotFather) after creating your bot.
- **GROUP_CHAT_ID**: The chat ID for the approvers' group where break requests will be sent. This can be obtained by adding the bot to the group and using the `/getchatid` command.

> **Note**: Keep your `.env` file secure and never share it publicly, as it contains sensitive information that grants control over your bot.

### Installation Steps

1. **Clone the Repository**:
   ```bash
   git clone https://github.com/your-username/break-request-bot.git
   cd break-request-bot
   ```

2. **Install Dependencies**:
   Use a virtual environment and install required libraries:
   ```bash
   python -m venv .venv
   source .venv/bin/activate
   pip install -r requirements.txt
   ```

3. **Set Environment Variables**:
   Make sure to create a `.env` file as shown above with `BOT_TOKEN` and `GROUP_CHAT_ID`.

## Usage

### Commands

- **/start**: Begins the break request conversation. Prompts the user to select their department.
- **/cancel**: Cancels the current request at any point.
- **/getchatid**: Returns the chat ID for the group or chat where it’s issued.

### Workflow

1. **Start**: An employee initiates a break request with `/start`.
2. **Department Selection**: The bot prompts the employee to choose their department (AML, Verification, or Alert).
3. **Duration Selection**: The bot asks for a break duration (5, 10, 15, or 20 minutes).
4. **Approval Request**: The bot sends a request message to the approver group with buttons for **Approve** or **Ignore**.
5. **Approval/Ignore Actions**:
   - **Approve**: Notifies the employee that the request is approved and clears the request.
   - **Ignore**: Notifies the employee that the request was ignored and allows them to start a new one.

### Approval Notification

- If approved, the employee receives a message with break details and encouragement to enjoy their break.
- If ignored, the employee is informed and can submit a new request.

### Timeout

- If the conversation is idle for 5 minutes, it automatically cancels.

## Code Overview

### Main Components

- **Handlers**:
  - `start`: Starts the break request flow.
  - `choose_department`: Saves the department choice.
  - `choose_duration`: Saves the duration and sends approval request.
  - `handle_request_response`: Processes approval or ignore responses from approvers.
  - `cancel`: Cancels the request.
  - `get_chat_id`: Returns the chat ID of the current chat.
  - `timeout`: Handles idle conversations by ending them.

- **Inline Keyboard Buttons**:
  - Used for approvers to select **Approve** or **Ignore** options.

### Logging

- Each action is logged to track the conversation flow, actions, and any errors.
- Logs include user actions, approvals, ignored requests, and errors.

## Deployment

### Deploying on Render as a Background Worker

1. **Create a Background Worker**: In Render, set up the bot as a Background Worker, not as a Web Service.
2. **Environment Variables**: Add `BOT_TOKEN` and `GROUP_CHAT_ID` in the Render environment variables section.
3. **Start Command**: Set the start command to:
   ```bash
   python main.py
   ```

### Running Locally

To run the bot locally:
```bash
python main.py
```

## Troubleshooting

- **No Open Ports Detected**: If deploying on Render, make sure the bot is set as a Background Worker.
- **Bot Doesn’t Move to Next Step**: Ensure that environment variables are correctly set, and the bot is able to receive updates.
- **Invalid Duration Error**: Only use predefined durations (5, 10, 15, or 20) to avoid validation issues.

## Future Enhancements

- Add more departments or durations based on company requirements.
- Expand functionality for custom reminders, using `JobQueue`.
- Integrate a database to keep records of past break requests and approvals for better tracking and reporting.

---

### Example Conversation

1. **User**: `/start`
2. **Bot**: "Please choose your department."
3. **User**: Selects "AML"
4. **Bot**: "Please select your break duration in minutes."
5. **User**: Selects "10"
6. **Bot**: "Your request has been sent for approval."
7. **Approver**: Approves the request.
8. **User**: Receives "Your break for 10 minutes has been approved!"
