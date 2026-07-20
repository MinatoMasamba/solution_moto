# Agent Coordination Protocol

All agents working on `go-mboka` MUST follow this protocol to ensure synchronization and project integrity.

## 1. Pre-Task Requirement: Context Awareness
Before initiating any work, every agent MUST read the `toujour_passer_ici.md` file located in the target directory (or closest parent directory) s il neiste pas cree le stp.
- If the directory contains folders: Explain the role and contents of those folders.
- If the directory contains files: Explain the purpose of each class/method within those files.

## 2. Activity Logging
After completing a task, the agent MUST record the action in `/home/minato/go-mboka/agent_activity.txt` using the following format:
`[YYYY-MM-DD HH:MM] - AgentName - Task Completed: [Description] - Remaining Tasks: [Description]`

## 3. Post-Task Requirement: Version Control
After updating the log, the agent MUST commit the changes to `agent_activity.txt` (and any other files modified) and execute `git push` to synchronize the work.
