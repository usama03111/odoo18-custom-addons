# Task Time Advanced - Real Time Duration

This module provides real-time task duration tracking functionality for Odoo 18.

## Features

### Real-time Duration Tracking
- **Systray Timer**: Live duration counter in the top systray showing current running task
- **Kanban Timer**: Real-time duration display in task kanban cards
- **Form Timer**: Duration widget in task form view

### Task Management
- **Start Task**: Begin tracking time for a task with automatic timesheet line creation
- **Stop Task**: End tracking with duration confirmation wizard
- **Multi-user Support**: Configurable option to allow multiple users to start the same task

### Timesheet Integration
- **Automatic Creation**: Timesheet lines are automatically created when starting tasks
- **Duration Tracking**: Start and end timestamps are recorded
- **Employee Linking**: Timesheet lines are linked to the current user's employee record

## Installation

1. Copy this module to your Odoo addons directory
2. Update the app list in Odoo
3. Install the module from Apps menu

## Usage

### Starting a Task
1. Open any project task
2. Click "Start Task" button in the form header or kanban card
3. Select project and task in the start wizard
4. The timer will begin counting in real-time

### Stopping a Task
1. Click "End Task" button in the form header or kanban card
2. Enter a description for the time entry
3. Confirm the duration and end the task
4. The time will be added to the task's timesheet

### Configuration
- Go to Settings > General Settings > Project
- Enable "Allow Multi User To Start Task" if you want multiple users to start the same task

## Technical Details

### Models
- `project.task`: Extended with timer fields and start/stop actions
- `sh.start.timesheet`: Wizard for starting tasks
- `sh.task.time.account.line`: Wizard for ending tasks
- `account.analytic.line`: Extended with start/end timestamps
- `res.users`: Extended with current task tracking
- `res.company`: Multi-user start configuration

### Controllers
- `/user/current/task/information`: Get current running task info for frontend
- `/end/task/information`: Get task details for ending

### Frontend Components
- **Systray Widget**: OWL component showing live timer
- **Kanban Widget**: Real-time duration field for kanban cards
- **Form Widget**: Duration display in task forms

## Dependencies
- base
- project
- hr_timesheet
- hr

## License
LGPL-3
