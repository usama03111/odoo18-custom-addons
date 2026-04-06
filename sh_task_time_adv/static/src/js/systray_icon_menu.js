/** @odoo-module **/

import { Component } from "@odoo/owl";
import { registry } from "@web/core/registry";
import { useService } from "@web/core/utils/hooks";
import { session } from "@web/session";

const { onMounted } = owl;

export class TimerMenu extends Component {
    static template = "TaskTimerTemplate";

    setup() {
        this.action = useService("action");
        console.log("✅ TimerMenu setup running.");

        // Timer interval reference
        this._timerInterval = null;
        this._startTimeMs = null;

        // Helper to format duration as HH:MM:SS
        this.formatDuration = function(duration) {
            if (typeof duration !== "number" || isNaN(duration)) {
                return "00:00:00";
            }
            const seconds = Math.floor(duration / 1000);
            const hours = Math.floor(seconds / 3600);
            const minutes = Math.floor((seconds % 3600) / 60);
            const remainingSeconds = seconds % 60;
            return (
                String(hours).padStart(2, "0") +
                ":" +
                String(minutes).padStart(2, "0") +
                ":" +
                String(remainingSeconds).padStart(2, "0")
            );
        };

        // Helper to clear timer interval and reset display
        this.clearTimer = function() {
            if (this._timerInterval) {
                clearInterval(this._timerInterval);
                this._timerInterval = null;
            }
            const timerEl = document.getElementById("task_timer");
            if (timerEl) {
                timerEl.innerText = "00:00:00";
            }
        };

        // Helper to start real-time timer
        this.startTimer = function(startTimeMs) {
            this.clearTimer();
            this._startTimeMs = startTimeMs;
            const timerEl = document.getElementById("task_timer");
            if (!timerEl) return;
            this._timerInterval = setInterval(() => {
                const now = Date.now();
                const elapsedMs = now - this._startTimeMs;
                timerEl.innerText = this.formatDuration(elapsedMs);
            }, 1000);
            // Immediately show the first value
            timerEl.innerText = this.formatDuration(Date.now() - this._startTimeMs);
        };

        // Helper to check backend and update button state and timer
        this.updateButtonStateFromBackend = async () => {
            try {
                const response = await fetch("/user/current/task/information", {
                    method: "POST",
                    headers: {
                        "Content-Type": "application/json",
                        "X-Requested-With": "XMLHttpRequest",
                    },
                    body: JSON.stringify({}),
                    credentials: "same-origin",
                });
                const rawData = await response.json();
                const data = rawData.result || rawData;
                console.log("Systray: fetched task info:", data);
                if (data && typeof data.start_timestamp !== "undefined" && data.start_timestamp !== null) {
                    this.showStopButton();
                    this.startTimer(data.start_timestamp);
                } else {
                    this.showStartButton();
                    this.clearTimer();
                }
            } catch (error) {
                console.error("Systray: error fetching task info, defaulting to Start button", error);
                this.showStartButton();
                this.clearTimer();
            }
        };

        onMounted(async () => {
            console.log("✅ onMounted: checking task state from backend.");
            await this.updateButtonStateFromBackend();
        });
    }

    showStartButton() {
        document.getElementById("timer_start").style.display = "flex";
        document.getElementById("timer_stop").style.display = "none";
        document.getElementById("task_timer").style.display = "none";
        document.getElementById("user_task").style.display = "none";
        // Clear timer when showing start button
        if (this.clearTimer) this.clearTimer();
    }

    showStopButton() {
        document.getElementById("timer_start").style.display = "none";
        document.getElementById("timer_stop").style.display = "flex";
        document.getElementById("task_timer").style.display = "inline";
        document.getElementById("user_task").style.display = "inline";
        document.getElementById("user_task").innerText = "Running Task";
        // Timer will be started by updateButtonStateFromBackend
    }

    _start_timer(ev) {
        ev.preventDefault();
        this.action.doAction({
            type: "ir.actions.act_window",
            view_type: "form",
            view_mode: "form",
            views: [[false, "form"]],
            res_model: "sh.start.timesheet",
            target: "new",
            context: {
                form_view_ref: "sh_task_track.start_timesheet_form",
            },
        });

        // After 1 second, re-check backend state and update timer
        setTimeout(() => {
            this.updateButtonStateFromBackend();
        }, 1000);
    }

    async _stop_timer(ev) {
        ev.preventDefault();
        console.log("STOP TIMER CLICKED");
        // Call the controller and wait for the result
        const response = await fetch("/end/task/information", {
            method: "POST",
            headers: {
                "Content-Type": "application/json",
                "X-Requested-With": "XMLHttpRequest",
            },
            body: JSON.stringify({ user_id: session.uid }),
            credentials: "same-origin",
        });
        const task_result = await response.json();
        console.log("task_result", task_result);
        const data = task_result.result || task_result; // Use .result if present, else use the object itself
        if (data && data[0] && data[1]) {
            this.action.doAction({
                type: "ir.actions.act_window",
                view_type: "form",
                view_mode: "form",
                views: [[false, "form"]],
                res_model: "sh.task.time.account.line",
                target: "new",
                context: {
                    default_start_date: data[1],
                    active_id: data[0],
                    active_model: "project.task",
                },
            });
        } else {
            alert("No running task found to stop.");
        }
    }
}

export const systrayItem = {
    Component: TimerMenu,
};

registry.category("systray").add("TimerMenu", systrayItem, { sequence: 1 });
