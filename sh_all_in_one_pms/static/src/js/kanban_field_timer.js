/** @odoo-module */
import { registry } from "@web/core/registry";
import { useRef, Component } from "@odoo/owl";

class TimeCounter extends Component {
    setup() {
        this.timer_kanban_ref = useRef("timer_kanban_ref");
        console.log("TimeCounter setup loaded.");
        this.startTimer(); // start the timer logic
    }

   async startTimer() {
    console.log("Fetching start timestamp from server...");
    let startTimeMs = null;

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
        console.log("Raw response JSON:", rawData);

        // Unwrap the jsonrpc envelope
        const data = rawData.result || {};
        console.log("Parsed data:", data);

        if (data && typeof data.start_timestamp !== "undefined") {
            startTimeMs = data.start_timestamp;
        } else {
            console.warn("Response missing start_timestamp, defaulting to now.");
            startTimeMs = Date.now();
        }
    } catch (error) {
        console.error("Error fetching start timestamp:", error);
        startTimeMs = Date.now();
    }

    console.log("Start time ms:", startTimeMs);

    setInterval(() => {
        const now = Date.now();
        const elapsedMs = now - startTimeMs;
        const timerText = this.formatDuration(elapsedMs);
        if (this.timer_kanban_ref.el) {
            this.timer_kanban_ref.el.textContent = timerText;
        }
    }, 1000);
}


    formatDuration(duration) {
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
    }
}

TimeCounter.template = "sh_all_in_one_pms.KanbanTimerCount";

registry.category("fields").add("task_time_counter", {
    component: TimeCounter,
});
