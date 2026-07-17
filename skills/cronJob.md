<!--
This file serves as a "Skill" or automated runbook for the AI agent to manage the Keep-Alive workflow in GitHub Actions.
When the user asks to follow these instructions, the agent must ask if they want to activate, deactivate, or modify the cron interval, make the corresponding changes to the YAML workflow file, and push them to GitHub.
-->

# Skill: Keep-Alive Workflow Management

This file contains precise instructions that you (the AI agent) must follow interactively to modify the time interval or activate/deactivate the keep-alive service (which prevents the free-tier Render server from spinning down).

## Instructions for the Agent (Runbook)

When the user requests you to "follow the instructions in `skills/cronJob.md`", you must execute the following steps sequentially:

### Step 1: Interact with the user to determine the action
Ask the user via the chat what they want to perform. Present the following options:
1. **Activate the service** (Uncomment the cron trigger in the workflow file).
2. **Deactivate the service** (Comment out the cron trigger in the workflow file).
3. **Change the time interval** (Modify the cron execution minutes).

### Step 2: Read the workflow configuration file
Open and read the contents of the workflow file located at:
`/.github/workflows/keep-alive.yml`

### Step 3: Modify the file based on the chosen option

#### Case A: Activate the service
Ensure that the `schedule` section and its respective `cron` rule are uncommented. The file should have this structure at the top:
```yaml
on:
  schedule:
    # Runs every X minutes to keep the Render free-tier container active
    - cron: '*/12 * * * *'
  workflow_dispatch:
```
*(If it was not commented out, inform the user that it was already active).*

#### Case B: Deactivate the service
Deactivate the automatic scheduler lines by prepending a `#` symbol to the beginning of the `schedule` section and the `cron` line. It should have this structure:
```yaml
on:
  # schedule:
  #   # Runs every X minutes to keep the Render free-tier container active
  #   - cron: '*/12 * * * *'
  workflow_dispatch:
```
*(This way, the automatic cron does not run, but the `workflow_dispatch` option remains active to allow running it manually if desired).*

#### Case C: Change the time interval
1. Ask the user for the desired interval in minutes (e.g., 14 minutes).
2. Modify the value inside the cron rule in the YAML file:
   `- cron: '*/<MINUTES> * * * *'` (for example: `- cron: '*/14 * * * *'`).
3. Ensure that the lines are not commented out so that the change takes effect immediately.

### Step 4: Validate YAML syntax
Ensure that the indentation and spacing format of `.github/workflows/keep-alive.yml` remains valid after your edits.

### Step 5: Commit and push to GitHub
Once the local changes have been made to the file:
1. Run `git status` to verify the modification of `.github/workflows/keep-alive.yml`.
2. Run `git add .github/workflows/keep-alive.yml`.
3. Commit the changes with a clear message in English (e.g., `"ci: update keep-alive cron job schedule to 14 minutes"` or `"ci: disable keep-alive cron job schedule"`).
4. Push the changes using `git push origin main`.
5. Confirm in the chat that the change has been successfully pushed.
